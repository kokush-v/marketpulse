from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from groq import APIConnectionError, APITimeoutError, BadRequestError, RateLimitError
from langchain_core.messages import AIMessage
from sqlalchemy.exc import SQLAlchemyError

from app.features.ai_assistant.schemas import SendAssistantMessageRequest
from app.features.ai_assistant.service import AssistantService, AssistantServiceError
from app.features.auth.models import User


class FailingModel:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def bind_tools(self, _tools: object) -> FailingModel:
        return self

    async def ainvoke(self, _messages: object) -> object:
        raise self.error


class OutcomeModel:
    def __init__(self) -> None:
        self.messages: list[object] = []

    async def ainvoke(self, messages: list[object]) -> AIMessage:
        self.messages = messages
        return AIMessage(content="Ваше сповіщення успішно створено.")


def make_service(error: Exception) -> AssistantService:
    service = AssistantService(
        session=cast(object, None),
        market_data_service=cast(object, None),
        news_service=cast(object, None),
        watchlist_service=cast(object, None),
        alert_service=cast(object, None),
    )
    service._model = FailingModel(error)
    return service


def provider_response(status_code: int, headers: dict[str, str] | None = None) -> httpx.Response:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return httpx.Response(status_code, headers=headers, request=request)


@pytest.mark.asyncio
async def test_rate_limit_error_is_retryable_and_includes_retry_delay() -> None:
    error = RateLimitError(
        "Rate limit exceeded",
        response=provider_response(429, {"retry-after": "7"}),
        body=None,
    )

    with pytest.raises(AssistantServiceError) as caught:
        await make_service(error)._get_graph_response(cast(User, object()), [])

    assert caught.value.status_code == 429
    assert caught.value.code == "assistant_rate_limited"
    assert caught.value.retryable is True
    assert caught.value.retry_after_seconds == 7
    assert "7 seconds" in caught.value.message


@pytest.mark.asyncio
async def test_timeout_error_is_retryable() -> None:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")

    with pytest.raises(AssistantServiceError) as caught:
        await make_service(APITimeoutError(request))._get_graph_response(cast(User, object()), [])

    assert caught.value.status_code == 504
    assert caught.value.code == "assistant_timeout"
    assert caught.value.retryable is True


@pytest.mark.asyncio
async def test_invalid_model_response_is_not_retryable() -> None:
    error = BadRequestError(
        "Invalid tool call",
        response=provider_response(400),
        body=None,
    )

    with pytest.raises(AssistantServiceError) as caught:
        await make_service(error)._get_graph_response(cast(User, object()), [])

    assert caught.value.status_code == 422
    assert caught.value.code == "invalid_model_response"
    assert caught.value.retryable is False


@pytest.mark.asyncio
async def test_connection_error_is_retryable() -> None:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")

    with pytest.raises(AssistantServiceError) as caught:
        await make_service(APIConnectionError(request=request))._get_graph_response(
            cast(User, object()),
            [],
        )

    assert caught.value.status_code == 503
    assert caught.value.code == "assistant_unavailable"
    assert caught.value.retryable is True


@pytest.mark.asyncio
async def test_failed_generation_does_not_persist_a_message_that_can_be_retried() -> None:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    service = make_service(APIConnectionError(request=request))
    conversation = SimpleNamespace(id=uuid4(), title=None)
    service.repository = SimpleNamespace(
        get_conversation_for_user=AsyncMock(return_value=conversation),
        list_messages_for_conversation=AsyncMock(return_value=[]),
        append_message=AsyncMock(),
    )

    with pytest.raises(AssistantServiceError):
        await service.send_message(
            cast(User, SimpleNamespace(id=uuid4())),
            conversation.id,
            SendAssistantMessageRequest(content="Show a Bitcoin chart"),
        )

    service.repository.append_message.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "operation", "outcome"),
    [
        ("Так, підтвердити", "confirm", "Created alert for **Solana (SOL)**."),
        ("No, cancel", "cancel", "Cancelled the pending action."),
    ],
)
async def test_explicit_chat_reply_resolves_only_the_current_owned_pending_action(
    content: str,
    operation: str,
    outcome: str,
) -> None:
    service = make_service(RuntimeError("model should not be called"))
    now = datetime.now(UTC)
    conversation = SimpleNamespace(id=uuid4(), title=None, created_at=now, updated_at=now)
    pending_action = SimpleNamespace(id=uuid4())
    action_service = SimpleNamespace(
        confirm=AsyncMock(return_value=(SimpleNamespace(), "Created alert for **Solana (SOL)**.")),
        cancel=AsyncMock(),
    )
    service.repository = SimpleNamespace(
        get_conversation_for_user=AsyncMock(return_value=conversation),
        get_current_pending_action_for_user=AsyncMock(return_value=pending_action),
        append_message=AsyncMock(),
        list_messages_for_conversation=AsyncMock(return_value=[]),
    )
    service._action_service = lambda: action_service  # type: ignore[method-assign]
    service._get_graph_response = AsyncMock()  # type: ignore[method-assign]
    user = cast(User, SimpleNamespace(id=uuid4()))

    response = await service.send_message(
        user,
        conversation.id,
        SendAssistantMessageRequest(content=content),
    )

    service.repository.get_current_pending_action_for_user.assert_awaited_once_with(
        user_id=user.id,
        conversation_id=conversation.id,
    )
    service._get_graph_response.assert_not_awaited()
    assert service.repository.append_message.await_args_list[0].kwargs["content"] == content
    assert service.repository.append_message.await_args_list[1].kwargs["content"] == outcome
    if operation == "confirm":
        action_service.confirm.assert_awaited_once_with(
            user=user,
            conversation_id=conversation.id,
            action_id=pending_action.id,
        )
        action_service.cancel.assert_not_awaited()
    else:
        action_service.cancel.assert_awaited_once_with(
            user=user,
            conversation_id=conversation.id,
            action_id=pending_action.id,
        )
        action_service.confirm.assert_not_awaited()
    assert response.messages == []


def test_chat_action_decision_ignores_ambiguous_text() -> None:
    assert AssistantService._chat_action_decision("Sure, that sounds good") is None


@pytest.mark.asyncio
async def test_chat_confirmation_returns_a_safe_message_when_action_execution_fails() -> None:
    service = make_service(RuntimeError("model should not be called"))
    now = datetime.now(UTC)
    conversation = SimpleNamespace(id=uuid4(), title=None, created_at=now, updated_at=now)
    pending_action = SimpleNamespace(id=uuid4())
    service.repository = SimpleNamespace(
        get_conversation_for_user=AsyncMock(return_value=conversation),
        get_current_pending_action_for_user=AsyncMock(return_value=pending_action),
        append_message=AsyncMock(),
        list_messages_for_conversation=AsyncMock(return_value=[]),
    )
    service._action_service = lambda: SimpleNamespace(  # type: ignore[method-assign]
        confirm=AsyncMock(side_effect=SQLAlchemyError("database failed")),
        cancel=AsyncMock(),
    )

    await service.send_message(
        cast(User, SimpleNamespace(id=uuid4())),
        conversation.id,
        SendAssistantMessageRequest(content="Yes, confirm"),
    )

    assert service.repository.append_message.await_args_list[1].kwargs["content"] == (
        "I couldn't complete that action. No changes were made. Please try again."
    )


@pytest.mark.asyncio
async def test_action_outcome_is_generated_from_the_verified_result() -> None:
    service = make_service(RuntimeError("model should not be called"))
    outcome_model = OutcomeModel()
    service._model = outcome_model

    content = await service._generate_action_outcome_response(
        messages=[],
        verified_outcome="Created alert for **Solana (SOL)**: Price above $150.00.",
    )

    assert content == "Ваше сповіщення успішно створено."
    assert any(
        "Verified completed outcome" in str(message.content) for message in outcome_model.messages
    )
