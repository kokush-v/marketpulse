from __future__ import annotations

import logging
import re
from typing import Annotated
from uuid import UUID

from fastapi import Depends, status
from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.features.ai_assistant.actions import (
    AssistantActionError,
    AssistantActionService,
    PendingActionCapture,
)
from app.features.ai_assistant.graph import (
    AssistantGraph,
    AssistantGraphConfigurationError,
    AssistantGraphResponse,
    build_groq_model,
)
from app.features.ai_assistant.models import AssistantConversation, AssistantMessage
from app.features.ai_assistant.repository import AssistantRepository
from app.features.ai_assistant.schemas import (
    AssistantConversationListResponse,
    AssistantConversationResponse,
    AssistantConversationSummaryResponse,
    AssistantErrorCode,
    AssistantMessageResponse,
    CreateAssistantConversationRequest,
    SendAssistantMessageRequest,
    UpdateAssistantConversationRequest,
)
from app.features.ai_assistant.tools import ChartPayloadCapture, SourcesCapture, build_read_tools
from app.features.alerts.service import AlertService, AlertServiceError
from app.features.auth.models import User
from app.features.market_data.service import MarketDataService
from app.features.news.service import NewsService
from app.features.watchlists.service import WatchlistService, WatchlistServiceError

logger = logging.getLogger(__name__)


class AssistantServiceError(Exception):
    def __init__(
        self,
        status_code: int,
        code: AssistantErrorCode,
        message: str,
        *,
        retryable: bool = False,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds


class AssistantService:
    _ACTION_OUTCOME_PROMPT = """You write the final user-facing response after a MarketPulse action
has already completed. Respond naturally in the language used by the conversation. Briefly explain
the verified outcome below. Do not mention tools, internal state, pending actions, confirmation
mechanisms, or implementation details. Do not ask for confirmation and do not suggest or perform
another operation."""
    _CHAT_ACTION_DECISIONS = {
        "yes": "confirm",
        "yes confirm": "confirm",
        "так": "confirm",
        "так підтвердити": "confirm",
        "no": "cancel",
        "no cancel": "cancel",
        "ні": "cancel",
        "ні скасувати": "cancel",
    }
    _PENDING_ACTION_SUGGESTED_REPLIES = ["Yes, confirm", "No, cancel"]
    _PENDING_ACTION_FOLLOW_UP_REPLIES = [
        "Show my watchlist.",
        "List my alerts.",
        "What can I do next?",
    ]

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_async_session)],
        market_data_service: Annotated[MarketDataService, Depends()],
        news_service: Annotated[NewsService, Depends()],
        watchlist_service: Annotated[WatchlistService, Depends()],
        alert_service: Annotated[AlertService, Depends()],
    ) -> None:
        self.repository = AssistantRepository(session)
        self.market_data_service = market_data_service
        self.news_service = news_service
        self.watchlist_service = watchlist_service
        self.alert_service = alert_service
        self._model = None

    async def list_conversations(self, user: User) -> AssistantConversationListResponse:
        conversations = await self.repository.list_conversations_for_user(user.id)
        return AssistantConversationListResponse(
            items=[self._summary_response(conversation) for conversation in conversations]
        )

    async def create_conversation(
        self,
        user: User,
        payload: CreateAssistantConversationRequest,
    ) -> AssistantConversationResponse:
        title = payload.title.strip() if payload.title else None
        conversation = await self.repository.create_conversation(
            user_id=user.id,
            title=title or None,
        )
        return self._conversation_response(conversation, [])

    async def get_conversation(
        self,
        user: User,
        conversation_id: UUID,
    ) -> AssistantConversationResponse:
        conversation = await self._get_owned_conversation(user, conversation_id)
        messages = await self.repository.list_messages_for_conversation(conversation.id)
        return self._conversation_response(conversation, messages)

    async def update_conversation_title(
        self,
        user: User,
        conversation_id: UUID,
        payload: UpdateAssistantConversationRequest,
    ) -> AssistantConversationResponse:
        title = payload.title.strip()
        if not title:
            raise AssistantServiceError(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "invalid_conversation_title",
                "Conversation title must not be blank",
            )
        conversation = await self._get_owned_conversation(user, conversation_id)
        conversation = await self.repository.update_conversation_title(
            conversation=conversation,
            title=title,
        )
        messages = await self.repository.list_messages_for_conversation(conversation.id)
        return self._conversation_response(conversation, messages)

    async def delete_conversation(self, user: User, conversation_id: UUID) -> None:
        conversation = await self._get_owned_conversation(user, conversation_id)
        await self.repository.delete_conversation(conversation=conversation)

    async def confirm_pending_action(
        self,
        user: User,
        conversation_id: UUID,
        action_id: UUID,
    ) -> AssistantConversationResponse:
        conversation = await self._get_owned_conversation(user, conversation_id)
        action_service = self._action_service()
        try:
            _, result_message = await action_service.confirm(
                user=user,
                conversation_id=conversation.id,
                action_id=action_id,
            )
        except AssistantActionError as error:
            raise AssistantServiceError(
                status.HTTP_404_NOT_FOUND if error.not_found else status.HTTP_409_CONFLICT,
                "pending_action_not_found" if error.not_found else "pending_action_resolved",
                error.message,
            ) from error
        except (AlertServiceError, WatchlistServiceError) as error:
            raise AssistantServiceError(
                error.status_code,
                "pending_action_resolved",
                error.message,
            ) from error

        await self.repository.append_message(
            conversation=conversation,
            role="assistant",
            content=result_message,
            suggested_replies=[
                "Show my watchlist.",
                "List my alerts.",
                "What can I do next?",
            ],
        )
        messages = await self.repository.list_messages_for_conversation(conversation.id)
        return self._conversation_response(conversation, messages)

    async def cancel_pending_action(
        self,
        user: User,
        conversation_id: UUID,
        action_id: UUID,
    ) -> AssistantConversationResponse:
        conversation = await self._get_owned_conversation(user, conversation_id)
        try:
            await self._action_service().cancel(
                user=user,
                conversation_id=conversation.id,
                action_id=action_id,
            )
        except AssistantActionError as error:
            raise AssistantServiceError(
                status.HTTP_404_NOT_FOUND if error.not_found else status.HTTP_409_CONFLICT,
                "pending_action_not_found" if error.not_found else "pending_action_resolved",
                error.message,
            ) from error

        await self.repository.append_message(
            conversation=conversation,
            role="assistant",
            content="Cancelled the pending action.",
            suggested_replies=[
                "Show my watchlist.",
                "List my alerts.",
                "What can I do next?",
            ],
        )
        messages = await self.repository.list_messages_for_conversation(conversation.id)
        return self._conversation_response(conversation, messages)

    async def send_message(
        self,
        user: User,
        conversation_id: UUID,
        payload: SendAssistantMessageRequest,
    ) -> AssistantConversationResponse:
        conversation = await self._get_owned_conversation(user, conversation_id)
        content = payload.content.strip()
        if not content:
            raise AssistantServiceError(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "invalid_message",
                "Message must not be blank",
            )

        action_decision = self._chat_action_decision(content)
        if action_decision is not None:
            pending_action = await self.repository.get_current_pending_action_for_user(
                user_id=user.id,
                conversation_id=conversation.id,
            )
            if pending_action is not None:
                return await self._resolve_pending_action_from_chat(
                    user=user,
                    conversation=conversation,
                    content=content,
                    action_id=pending_action.id,
                    decision=action_decision,
                )

        messages = await self.repository.list_messages_for_conversation(conversation.id)
        response = await self._get_graph_response(
            user,
            messages,
            conversation=conversation,
            pending_content=content,
        )
        await self.repository.append_message(
            conversation=conversation,
            role="user",
            content=content,
            initial_title=self._initial_title_from_message(content),
        )
        assistant_message = await self.repository.append_message(
            conversation=conversation,
            role="assistant",
            content=self._message_content(response.message),
            suggested_replies=(
                self._PENDING_ACTION_SUGGESTED_REPLIES
                if response.pending_action is not None
                else response.suggested_replies
            ),
            chart_payload=(
                response.chart_payload.model_dump(mode="json")
                if response.chart_payload is not None
                else None
            ),
            pending_action=(
                response.pending_action.model_dump(mode="json")
                if response.pending_action is not None
                else None
            ),
            sources=(
                [source.model_dump(mode="json") for source in response.sources]
                if response.sources
                else None
            ),
        )
        if response.pending_action is not None:
            action = await self.repository.get_pending_action_for_user(
                user_id=user.id,
                conversation_id=conversation.id,
                action_id=response.pending_action.id,
            )
            if action is not None and action.status == "pending":
                await self.repository.link_pending_action_message(
                    action=action,
                    message=assistant_message,
                    pending_action=response.pending_action.model_dump(mode="json"),
                )
        messages = await self.repository.list_messages_for_conversation(conversation.id)
        return self._conversation_response(conversation, messages)

    async def _resolve_pending_action_from_chat(
        self,
        *,
        user: User,
        conversation: AssistantConversation,
        content: str,
        action_id: UUID,
        decision: str,
    ) -> AssistantConversationResponse:
        await self.repository.append_message(
            conversation=conversation,
            role="user",
            content=content,
        )

        try:
            if decision == "confirm":
                _, result_message = await self._action_service().confirm(
                    user=user,
                    conversation_id=conversation.id,
                    action_id=action_id,
                )
            else:
                await self._action_service().cancel(
                    user=user,
                    conversation_id=conversation.id,
                    action_id=action_id,
                )
                result_message = "Cancelled the pending action."
        except (AssistantActionError, AlertServiceError, SQLAlchemyError, WatchlistServiceError):
            result_message = (
                "I couldn't complete that action. No changes were made. Please try again."
            )

        outcome_context = await self.repository.list_messages_for_conversation(conversation.id)
        assistant_content = await self._generate_action_outcome_response(
            messages=outcome_context,
            verified_outcome=result_message,
        )
        await self.repository.append_message(
            conversation=conversation,
            role="assistant",
            content=assistant_content,
            suggested_replies=self._PENDING_ACTION_FOLLOW_UP_REPLIES,
        )
        messages = await self.repository.list_messages_for_conversation(conversation.id)
        return self._conversation_response(conversation, messages)

    async def _generate_action_outcome_response(
        self,
        *,
        messages: list[AssistantMessage],
        verified_outcome: str,
    ) -> str:
        try:
            model = self._model or build_groq_model()
            self._model = model
            context = [
                HumanMessage(content=message.content)
                if message.role == "user"
                else AIMessage(content=message.content)
                for message in messages[-8:]
                if message.role in {"user", "assistant"}
            ]
            response = await model.ainvoke(
                [
                    SystemMessage(content=self._ACTION_OUTCOME_PROMPT),
                    *context,
                    SystemMessage(content=f"Verified completed outcome: {verified_outcome}"),
                ]
            )
            content = self._message_content(response)
            return content or verified_outcome
        except Exception:
            logger.warning("Assistant action outcome response generation failed", exc_info=True)
            return verified_outcome

    async def _get_owned_conversation(
        self,
        user: User,
        conversation_id: UUID,
    ) -> AssistantConversation:
        conversation = await self.repository.get_conversation_for_user(
            user_id=user.id,
            conversation_id=conversation_id,
        )
        if conversation is None:
            raise AssistantServiceError(
                status.HTTP_404_NOT_FOUND,
                "conversation_not_found",
                "Conversation not found",
            )
        return conversation

    async def _get_graph_response(
        self,
        user: User,
        messages: list[AssistantMessage],
        conversation: AssistantConversation | None = None,
        pending_content: str | None = None,
    ) -> AssistantGraphResponse:
        try:
            model = self._model or build_groq_model()
            self._model = model
            chart_payload_capture = ChartPayloadCapture()
            pending_action_capture = PendingActionCapture()
            sources_capture = SourcesCapture()
            action_service = self._action_service()
            graph = AssistantGraph(
                model,
                tools=build_read_tools(
                    user=user,
                    market_data_service=self.market_data_service,
                    news_service=self.news_service,
                    watchlist_service=self.watchlist_service,
                    alert_service=self.alert_service,
                    conversation=conversation,
                    action_service=action_service,
                    chart_payload_capture=chart_payload_capture,
                    pending_action_capture=pending_action_capture,
                    sources_capture=sources_capture,
                ),
                chart_payload_getter=lambda: chart_payload_capture.payload,
                pending_action_getter=lambda: pending_action_capture.pending_action,
                sources_getter=lambda: sources_capture.sources,
            )
            graph_messages = [
                HumanMessage(content=message.content)
                if message.role == "user"
                else AIMessage(content=message.content)
                for message in messages
                if message.role in {"user", "assistant"}
            ]
            if pending_content is not None:
                graph_messages.append(HumanMessage(content=pending_content))
            return await graph.respond_with_suggestions(graph_messages)
        except AssistantGraphConfigurationError as error:
            raise AssistantServiceError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "assistant_not_configured",
                "The AI assistant is not configured yet. Please try again later.",
            ) from error

        except RateLimitError as error:
            retry_after_seconds = self._retry_after_seconds(error)
            message = "The AI assistant is receiving too many requests."
            if retry_after_seconds is not None:
                message = f"{message} Try again in {retry_after_seconds} seconds."
            else:
                message = f"{message} Please try again shortly."
            raise AssistantServiceError(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "assistant_rate_limited",
                message,
                retryable=True,
                retry_after_seconds=retry_after_seconds,
            ) from error
        except APITimeoutError as error:
            raise AssistantServiceError(
                status.HTTP_504_GATEWAY_TIMEOUT,
                "assistant_timeout",
                "The AI assistant took too long to respond. Please try again.",
                retryable=True,
            ) from error
        except (AuthenticationError, PermissionDeniedError) as error:
            raise AssistantServiceError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "assistant_configuration_error",
                "The AI assistant is temporarily unavailable due to a service configuration issue.",
            ) from error
        except (BadRequestError, UnprocessableEntityError) as error:
            raise AssistantServiceError(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "invalid_model_response",
                (
                    "The AI assistant could not process that request. "
                    "Please rephrase it and try again."
                ),
            ) from error
        except APIConnectionError as error:
            raise AssistantServiceError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "assistant_unavailable",
                "The AI assistant is temporarily unavailable. Please try again shortly.",
                retryable=True,
            ) from error
        except APIStatusError as error:
            if error.status_code in {
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                status.HTTP_429_TOO_MANY_REQUESTS,
            }:
                raise AssistantServiceError(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    "assistant_rate_limited",
                    "The AI assistant request is too large right now. Please try again shortly.",
                    retryable=True,
                ) from error
            raise AssistantServiceError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "assistant_unavailable",
                "The AI assistant is temporarily unavailable. Please try again shortly.",
                retryable=error.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from error
        except Exception as error:
            raise AssistantServiceError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "assistant_unavailable",
                "The AI assistant is temporarily unavailable. Please try again shortly.",
                retryable=True,
            ) from error

    def _action_service(self) -> AssistantActionService:
        return AssistantActionService(
            repository=self.repository,
            watchlist_service=self.watchlist_service,
            alert_service=self.alert_service,
        )

    @classmethod
    def _chat_action_decision(cls, content: str) -> str | None:
        normalized = re.sub(r"[^\w\s]", " ", content.casefold())
        normalized = " ".join(normalized.split())
        return cls._CHAT_ACTION_DECISIONS.get(normalized)

    @staticmethod
    def _retry_after_seconds(error: RateLimitError) -> int | None:
        retry_after = error.response.headers.get("retry-after")
        if retry_after is None:
            return None
        try:
            seconds = int(float(retry_after))
        except ValueError:
            return None
        return seconds if seconds > 0 else None

    @staticmethod
    def _message_content(message: AIMessage) -> str:
        if isinstance(message.content, str):
            return message.content
        return "\n".join(
            item["text"]
            for item in message.content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        )

    @staticmethod
    def _initial_title_from_message(content: str) -> str:
        words = content.split()
        title = " ".join(words[:3])
        if len(words) > 3:
            return f"{title[:197].rstrip()}..."
        return title[:200]

    @staticmethod
    def _summary_response(
        conversation: AssistantConversation,
    ) -> AssistantConversationSummaryResponse:
        return AssistantConversationSummaryResponse.model_validate(conversation)

    @classmethod
    def _conversation_response(
        cls,
        conversation: AssistantConversation,
        messages: list[AssistantMessage],
    ) -> AssistantConversationResponse:
        return AssistantConversationResponse(
            **cls._summary_response(conversation).model_dump(),
            messages=[AssistantMessageResponse.model_validate(message) for message in messages],
        )
