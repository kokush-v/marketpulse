from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.features.ai_assistant.repository import AssistantRepository


@pytest.mark.asyncio
async def test_assistant_message_persists_chart_payload() -> None:
    chart_payload = {
        "period": "7d",
        "series": [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "points": [{"time": "2026-08-29T00:00:00Z", "price": 101_000.0}],
            }
        ],
    }
    session = SimpleNamespace(
        refresh=AsyncMock(),
        execute=AsyncMock(return_value=SimpleNamespace(scalar_one=lambda: -1)),
        add=MagicMock(),
        commit=AsyncMock(),
    )
    repository = AssistantRepository(session)
    conversation = SimpleNamespace(id=uuid4(), title=None, updated_at=None)

    message = await repository.append_message(
        conversation=conversation,
        role="assistant",
        content="Bitcoin moved higher over the selected period.",
        suggested_replies=["Show ETH", "Use 30 days", "Show related news"],
        chart_payload=chart_payload,
    )

    assert message.chart_payload == chart_payload
    session.add.assert_called_once_with(message)
