from __future__ import annotations

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
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
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
from app.features.ai_assistant.tools import ChartPayloadCapture, build_read_tools
from app.features.alerts.service import AlertService
from app.features.auth.models import User
from app.features.market_data.service import MarketDataService
from app.features.news.service import NewsService
from app.features.watchlists.service import WatchlistService


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

        messages = await self.repository.list_messages_for_conversation(conversation.id)
        response = await self._get_graph_response(user, messages, pending_content=content)
        await self.repository.append_message(
            conversation=conversation,
            role="user",
            content=content,
            initial_title=self._initial_title_from_message(content),
        )
        await self.repository.append_message(
            conversation=conversation,
            role="assistant",
            content=self._message_content(response.message),
            suggested_replies=response.suggested_replies,
            chart_payload=(
                response.chart_payload.model_dump(mode="json")
                if response.chart_payload is not None
                else None
            ),
        )
        messages = await self.repository.list_messages_for_conversation(conversation.id)
        return self._conversation_response(conversation, messages)

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
        pending_content: str | None = None,
    ) -> AssistantGraphResponse:
        try:
            model = self._model or build_groq_model()
            self._model = model
            chart_payload_capture = ChartPayloadCapture()
            graph = AssistantGraph(
                model,
                tools=build_read_tools(
                    user=user,
                    market_data_service=self.market_data_service,
                    news_service=self.news_service,
                    watchlist_service=self.watchlist_service,
                    alert_service=self.alert_service,
                    chart_payload_capture=chart_payload_capture,
                ),
                chart_payload_getter=lambda: chart_payload_capture.payload,
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
