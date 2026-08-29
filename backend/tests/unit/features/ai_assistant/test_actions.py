from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.features.ai_assistant.actions import AssistantActionError, AssistantActionService
from app.features.ai_assistant.schemas import AssistantPendingActionSummaryResponse


def pending_action(*, action_type: str = "add_watchlist_asset") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        status="pending",
        action_type=action_type,
        target_id="bitcoin",
        validated_input={
            "asset_id": "bitcoin",
            "symbol": "BTC",
            "name": "Bitcoin",
            "image_url": None,
        },
        display_summary={
            "title": "Add Bitcoin (BTC) to your watchlist",
            "details": ["Asset: Bitcoin (BTC)"],
        },
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        message_id=None,
    )


@pytest.mark.asyncio
async def test_proposal_does_not_execute_watchlist_mutation() -> None:
    action = pending_action()
    repository = SimpleNamespace(create_pending_action=AsyncMock(return_value=action))
    watchlist_service = SimpleNamespace(add_asset=AsyncMock())
    service = AssistantActionService(
        repository=repository,
        watchlist_service=watchlist_service,
        alert_service=SimpleNamespace(),
    )

    proposal = await service.propose(
        conversation=SimpleNamespace(id=uuid4()),
        user=SimpleNamespace(id=uuid4()),
        action_type="add_watchlist_asset",
        target_id="bitcoin",
        validated_input=action.validated_input,
        summary=AssistantPendingActionSummaryResponse.model_validate(action.display_summary),
    )

    assert proposal.status == "pending"
    repository.create_pending_action.assert_awaited_once()
    watchlist_service.add_asset.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirmation_executes_once_and_cannot_be_repeated() -> None:
    action = pending_action()

    async def resolve_pending_action(*, action: SimpleNamespace, status: str) -> None:
        action.status = status

    async def claim_pending_action(**_: object) -> SimpleNamespace:
        if action.status == "pending":
            action.status = "executing"
        return action

    repository = SimpleNamespace(
        claim_pending_action=AsyncMock(side_effect=claim_pending_action),
        resolve_pending_action=AsyncMock(side_effect=resolve_pending_action),
        session=SimpleNamespace(commit=AsyncMock()),
    )
    watchlist_service = SimpleNamespace(
        add_asset=AsyncMock(return_value=SimpleNamespace(name="Bitcoin", symbol="BTC"))
    )
    service = AssistantActionService(
        repository=repository,
        watchlist_service=watchlist_service,
        alert_service=SimpleNamespace(),
    )
    user = SimpleNamespace(id=uuid4())
    conversation_id = uuid4()

    proposal, result = await service.confirm(
        user=user,
        conversation_id=conversation_id,
        action_id=action.id,
    )

    assert proposal.status == "confirmed"
    assert result == "Added **Bitcoin (BTC)** to your watchlist."
    watchlist_service.add_asset.assert_awaited_once()

    with pytest.raises(AssistantActionError, match="already been resolved"):
        await service.confirm(user=user, conversation_id=conversation_id, action_id=action.id)

    watchlist_service.add_asset.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirmation_does_not_disclose_or_execute_another_users_action() -> None:
    repository = SimpleNamespace(claim_pending_action=AsyncMock(return_value=None))
    watchlist_service = SimpleNamespace(add_asset=AsyncMock())
    service = AssistantActionService(
        repository=repository,
        watchlist_service=watchlist_service,
        alert_service=SimpleNamespace(),
    )

    with pytest.raises(AssistantActionError) as caught:
        await service.confirm(
            user=SimpleNamespace(id=uuid4()),
            conversation_id=uuid4(),
            action_id=uuid4(),
        )

    assert caught.value.not_found is True
    watchlist_service.add_asset.assert_not_awaited()


@pytest.mark.asyncio
async def test_confirmation_rolls_back_and_keeps_action_retryable_after_execution_failure() -> None:
    action = pending_action()
    action.status = "executing"
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    repository = SimpleNamespace(
        claim_pending_action=AsyncMock(return_value=action),
        get_pending_action_for_user=AsyncMock(return_value=action),
        session=session,
    )
    watchlist_service = SimpleNamespace(
        add_asset=AsyncMock(side_effect=RuntimeError("database failed"))
    )
    service = AssistantActionService(
        repository=repository,
        watchlist_service=watchlist_service,
        alert_service=SimpleNamespace(),
    )

    with pytest.raises(RuntimeError, match="database failed"):
        await service.confirm(
            user=SimpleNamespace(id=uuid4()),
            conversation_id=uuid4(),
            action_id=action.id,
        )

    session.rollback.assert_awaited_once()
    assert action.status == "pending"
    session.commit.assert_awaited_once()
