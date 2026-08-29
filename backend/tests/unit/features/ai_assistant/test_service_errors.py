from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from groq import APIConnectionError, APITimeoutError, BadRequestError, RateLimitError

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
