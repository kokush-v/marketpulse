from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.db.session import get_async_session
from app.features.ai_assistant import service as assistant_service_module
from app.features.ai_assistant.models import AssistantMessage, AssistantMessageFeedback
from app.features.ai_assistant.schemas import (
    AssistantConversationResponse,
    AssistantMessageFeedbackResponse,
    SubmitAssistantMessageFeedbackRequest,
)
from app.features.ai_assistant.service import AssistantService, AssistantServiceError
from app.features.auth import dependencies as auth_dependencies
from app.features.auth.models import User
from app.main import app

NOW = datetime.now(UTC)


def _message(role: str = "assistant", feedback: object | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), role=role, feedback=feedback)


def _service(message: SimpleNamespace | None) -> AssistantService:
    service = AssistantService(
        session=cast(Any, None),
        market_data_service=cast(Any, None),
        news_service=cast(Any, None),
        watchlist_service=cast(Any, None),
        alert_service=cast(Any, None),
    )

    async def create_message_feedback(**kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(rating=kwargs["rating"], reason=kwargs["reason"], created_at=NOW)

    service.repository = cast(
        Any,
        SimpleNamespace(
            session=SimpleNamespace(rollback=AsyncMock()),
            get_message_for_user=AsyncMock(return_value=message),
            create_message_feedback=AsyncMock(side_effect=create_message_feedback),
        ),
    )
    return service


def _user() -> User:
    return cast(User, SimpleNamespace(id=uuid4()))


# Service


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("rating", "reason"),
    [("positive", None), ("negative", "The price was wrong."), ("positive", "Clear answer")],
)
async def test_submits_feedback_for_an_owned_assistant_message(
    rating: str, reason: str | None
) -> None:
    message = _message()
    service = _service(message)
    user = _user()
    conversation_id = uuid4()

    response = await service.submit_message_feedback(
        user,
        conversation_id,
        message.id,
        SubmitAssistantMessageFeedbackRequest(rating=rating, reason=reason),
    )

    assert response == AssistantMessageFeedbackResponse(
        rating=rating, reason=reason, created_at=NOW
    )
    service.repository.get_message_for_user.assert_awaited_once_with(
        user_id=user.id, conversation_id=conversation_id, message_id=message.id
    )
    create_kwargs = service.repository.create_message_feedback.await_args.kwargs
    assert create_kwargs["message"] is message
    assert create_kwargs["user_id"] == user.id


@pytest.mark.asyncio
async def test_rejects_a_second_rating_for_the_same_message() -> None:
    existing = SimpleNamespace(rating="positive", reason=None, created_at=NOW)
    service = _service(_message(feedback=existing))

    with pytest.raises(AssistantServiceError) as caught:
        await service.submit_message_feedback(
            _user(), uuid4(), uuid4(), SubmitAssistantMessageFeedbackRequest(rating="negative")
        )

    assert caught.value.status_code == 409
    assert caught.value.code == "feedback_already_submitted"
    service.repository.create_message_feedback.assert_not_awaited()


@pytest.mark.asyncio
async def test_concurrent_duplicate_rating_is_rejected_by_the_unique_constraint() -> None:
    service = _service(_message())
    service.repository.create_message_feedback = AsyncMock(
        side_effect=IntegrityError("insert", {}, Exception("duplicate key"))
    )

    with pytest.raises(AssistantServiceError) as caught:
        await service.submit_message_feedback(
            _user(), uuid4(), uuid4(), SubmitAssistantMessageFeedbackRequest(rating="positive")
        )

    assert caught.value.status_code == 409
    service.repository.session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_rejects_a_message_not_owned_by_the_user_as_not_found() -> None:
    service = _service(None)

    with pytest.raises(AssistantServiceError) as caught:
        await service.submit_message_feedback(
            _user(), uuid4(), uuid4(), SubmitAssistantMessageFeedbackRequest(rating="positive")
        )

    assert caught.value.status_code == 404
    assert caught.value.code == "message_not_found"


@pytest.mark.asyncio
async def test_rejects_feedback_on_a_user_message() -> None:
    service = _service(_message(role="user"))

    with pytest.raises(AssistantServiceError) as caught:
        await service.submit_message_feedback(
            _user(), uuid4(), uuid4(), SubmitAssistantMessageFeedbackRequest(rating="positive")
        )

    assert caught.value.status_code == 422
    assert caught.value.code == "invalid_feedback_target"
    service.repository.create_message_feedback.assert_not_awaited()


# Request validation


def test_reason_is_trimmed_and_empty_reason_is_stored_as_null() -> None:
    assert SubmitAssistantMessageFeedbackRequest(rating="negative", reason="  Wrong  ").reason == (
        "Wrong"
    )
    assert SubmitAssistantMessageFeedbackRequest(rating="negative", reason="   ").reason is None


def test_reason_over_the_limit_and_invalid_rating_are_rejected() -> None:
    with pytest.raises(ValidationError):
        SubmitAssistantMessageFeedbackRequest(rating="negative", reason="x" * 1001)
    with pytest.raises(ValidationError):
        SubmitAssistantMessageFeedbackRequest(rating=cast(Any, "neutral"))
    assert (
        len(SubmitAssistantMessageFeedbackRequest(rating="negative", reason="x" * 1000).reason)
        == 1000
    )


# Conversation response and deletion


def test_conversation_response_includes_message_feedback() -> None:
    conversation = AssistantConversationResponse.model_validate(
        SimpleNamespace(
            id=uuid4(),
            title=None,
            created_at=NOW,
            updated_at=NOW,
            messages=[
                SimpleNamespace(
                    id=uuid4(),
                    role="assistant",
                    content="Answer",
                    suggested_replies=[],
                    chart_payload=None,
                    pending_action=None,
                    sources=None,
                    feedback=SimpleNamespace(rating="negative", reason="Wrong", created_at=NOW),
                    created_at=NOW,
                ),
                SimpleNamespace(
                    id=uuid4(),
                    role="user",
                    content="Question",
                    suggested_replies=[],
                    chart_payload=None,
                    pending_action=None,
                    sources=None,
                    feedback=None,
                    created_at=NOW,
                ),
            ],
        ),
        from_attributes=True,
    )

    assert conversation.messages[0].feedback == AssistantMessageFeedbackResponse(
        rating="negative", reason="Wrong", created_at=NOW
    )
    assert conversation.messages[1].feedback is None


def test_feedback_is_deleted_with_its_message_and_conversation() -> None:
    feedback_fk = next(iter(AssistantMessageFeedback.__table__.c.message_id.foreign_keys))
    message_fk = next(iter(AssistantMessage.__table__.c.conversation_id.foreign_keys))

    assert feedback_fk.column.table.name == "assistant_messages"
    assert feedback_fk.ondelete == "CASCADE"
    assert message_fk.ondelete == "CASCADE"
    assert AssistantMessageFeedback.__table__.c.message_id.unique is True


# Route


@pytest.fixture
def authenticated_client(monkeypatch: pytest.MonkeyPatch):
    user = User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="feedback@example.com",
        created_at=NOW,
    )

    async def fake_get_async_session():
        yield object()

    async def fake_get_authenticated_user(self, supabase_user_id):
        return user

    monkeypatch.setattr(
        auth_dependencies,
        "_decode_access_token",
        lambda _token: {"sub": str(user.supabase_user_id), "email": user.email, "exp": 4102444800},
    )
    monkeypatch.setattr(
        auth_dependencies.AuthService, "get_authenticated_user", fake_get_authenticated_user
    )
    app.dependency_overrides[get_async_session] = fake_get_async_session
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer token"
        yield client, user
    app.dependency_overrides.clear()


def _feedback_path() -> str:
    return f"/assistant/conversations/{uuid4()}/messages/{uuid4()}/feedback"


def test_feedback_route_requires_access_token() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    with TestClient(app) as client:
        response = client.post(_feedback_path(), json={"rating": "positive"})
    app.dependency_overrides.clear()

    assert response.status_code == 401


def test_feedback_route_returns_created_feedback(
    authenticated_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = authenticated_client

    async def fake_submit(self, current_user, conversation_id, message_id, payload):
        assert current_user.id == user.id
        return AssistantMessageFeedbackResponse(
            rating=payload.rating, reason=payload.reason, created_at=NOW
        )

    monkeypatch.setattr(
        assistant_service_module.AssistantService, "submit_message_feedback", fake_submit
    )

    response = client.post(_feedback_path(), json={"rating": "negative", "reason": " Wrong "})

    assert response.status_code == 201
    assert response.json()["rating"] == "negative"
    assert response.json()["reason"] == "Wrong"


@pytest.mark.parametrize(
    ("status_code", "code"),
    [
        (404, "message_not_found"),
        (409, "feedback_already_submitted"),
        (422, "invalid_feedback_target"),
    ],
)
def test_feedback_route_returns_service_errors(
    authenticated_client, monkeypatch: pytest.MonkeyPatch, status_code: int, code: str
) -> None:
    client, _user = authenticated_client

    async def fake_submit(self, *_args):
        raise AssistantServiceError(status_code, code, "Rejected")

    monkeypatch.setattr(
        assistant_service_module.AssistantService, "submit_message_feedback", fake_submit
    )

    response = client.post(_feedback_path(), json={"rating": "positive"})

    assert response.status_code == status_code
    assert response.json()["code"] == code


@pytest.mark.parametrize(
    "body", [{"rating": "neutral"}, {"rating": "negative", "reason": "x" * 1001}]
)
def test_feedback_route_rejects_invalid_payloads(authenticated_client, body: dict) -> None:
    client, _user = authenticated_client

    response = client.post(_feedback_path(), json=body)

    assert response.status_code == 422
