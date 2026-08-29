from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.features.ai_assistant.repository import AssistantRepository
from app.features.ai_assistant.schemas import UpdateAssistantConversationRequest
from app.features.ai_assistant.service import AssistantService, AssistantServiceError
from app.features.auth.models import User


def make_service() -> AssistantService:
    return AssistantService(
        session=cast(object, None),
        market_data_service=cast(object, None),
        news_service=cast(object, None),
        watchlist_service=cast(object, None),
        alert_service=cast(object, None),
    )


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Bitcoin news", "Bitcoin news"),
        ("Tell me about Solana price today", "Tell me about..."),
        ("  What   happened\nwith ETH today?  ", "What happened with..."),
    ],
)
def test_initial_title_uses_first_three_words(message: str, expected: str) -> None:
    assert AssistantService._initial_title_from_message(message) == expected


@pytest.mark.asyncio
async def test_update_title_rejects_whitespace_only_title() -> None:
    service = make_service()

    with pytest.raises(AssistantServiceError) as caught:
        await service.update_conversation_title(
            cast(User, SimpleNamespace(id=uuid4())),
            uuid4(),
            UpdateAssistantConversationRequest(title="   "),
        )

    assert caught.value.code == "invalid_conversation_title"


@pytest.mark.asyncio
async def test_update_title_changes_only_an_owned_conversation() -> None:
    service = make_service()
    conversation = SimpleNamespace(
        id=uuid4(),
        title="Old title",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    async def update_conversation_title(*, title: str, **_: object) -> SimpleNamespace:
        conversation.title = title
        return conversation

    repository = SimpleNamespace(
        get_conversation_for_user=AsyncMock(return_value=conversation),
        update_conversation_title=AsyncMock(side_effect=update_conversation_title),
        list_messages_for_conversation=AsyncMock(return_value=[]),
    )
    service.repository = repository

    response = await service.update_conversation_title(
        cast(User, SimpleNamespace(id=uuid4())),
        conversation.id,
        UpdateAssistantConversationRequest(title="  New title  "),
    )

    repository.update_conversation_title.assert_awaited_once_with(
        conversation=conversation,
        title="New title",
    )
    assert response.title == "New title"


@pytest.mark.asyncio
async def test_update_title_keeps_conversation_activity_timestamp() -> None:
    timestamp = datetime.now(UTC)
    conversation = SimpleNamespace(title="Old title", updated_at=timestamp)
    session = AsyncMock()
    repository = AssistantRepository(cast(object, session))

    await repository.update_conversation_title(conversation=conversation, title="New title")

    assert conversation.title == "New title"
    assert conversation.updated_at == timestamp


@pytest.mark.asyncio
async def test_rename_requires_owned_conversation() -> None:
    service = make_service()
    repository = SimpleNamespace(
        get_conversation_for_user=AsyncMock(return_value=None),
        update_conversation_title=AsyncMock(),
    )
    service.repository = repository

    with pytest.raises(AssistantServiceError) as caught:
        await service.update_conversation_title(
            cast(User, SimpleNamespace(id=uuid4())),
            uuid4(),
            UpdateAssistantConversationRequest(title="New title"),
        )

    assert caught.value.code == "conversation_not_found"
    repository.update_conversation_title.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_requires_owned_conversation() -> None:
    service = make_service()
    repository = SimpleNamespace(
        get_conversation_for_user=AsyncMock(return_value=None),
        delete_conversation=AsyncMock(),
    )
    service.repository = repository

    with pytest.raises(AssistantServiceError) as caught:
        await service.delete_conversation(cast(User, SimpleNamespace(id=uuid4())), uuid4())

    assert caught.value.code == "conversation_not_found"
    repository.delete_conversation.assert_not_awaited()
