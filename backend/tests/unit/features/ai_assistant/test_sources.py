from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from app.features.ai_assistant.graph import AssistantGraphResponse
from app.features.ai_assistant.schemas import (
    AssistantMessageResponse,
    AssistantMessageSourceResponse,
    SendAssistantMessageRequest,
)
from app.features.ai_assistant.service import AssistantService
from app.features.ai_assistant.tools import SourcesCapture, build_read_tools
from app.features.ai_assistant.tools.shared import is_stale
from app.features.auth.models import User
from app.features.market_data.service import UpstreamMarketDataError

NOW = datetime.now(UTC)
FRESH = (NOW - timedelta(minutes=1)).isoformat()
OLD = (NOW - timedelta(hours=5)).isoformat()
BTC = SimpleNamespace(
    id="bitcoin",
    asset_id="bitcoin",
    symbol="BTC",
    name="Bitcoin",
    description="A digital asset.",
    current_price=100_000.0,
    price_change_percentage_24h=2.04,
    market_cap_rank=1,
)
ARTICLE = SimpleNamespace(
    title="Bitcoin update",
    summary="Market update.",
    url="https://example.com/bitcoin",
    published_at="2026-11-03T08:00:00Z",
    source="Example News",
)


async def _async(value: Any) -> Any:
    return value


def _tools(capture: SourcesCapture, **services: Any) -> dict[str, Any]:
    defaults = {
        "market_data_service": SimpleNamespace(),
        "news_service": SimpleNamespace(),
        "watchlist_service": SimpleNamespace(),
        "alert_service": SimpleNamespace(),
    }
    return {
        tool.name: tool
        for tool in build_read_tools(
            user=cast(User, SimpleNamespace(id=uuid4())),
            sources_capture=capture,
            **{key: cast(Any, value) for key, value in {**defaults, **services}.items()},
        )
    }


def _overview_service(generated_at: str) -> SimpleNamespace:
    return SimpleNamespace(
        get_market_overview=lambda: _async(
            SimpleNamespace(generated_at=generated_at, featured_assets=[BTC])
        ),
        search_assets=lambda _query: _async(SimpleNamespace(items=[BTC])),
        get_historical_prices=lambda **_: _async(
            SimpleNamespace(
                period="7d",
                series=[
                    SimpleNamespace(
                        asset_id="bitcoin",
                        points=[
                            SimpleNamespace(time=OLD, price=99_000.0),
                            SimpleNamespace(time=FRESH, price=100_000.0),
                        ],
                    )
                ],
            )
        ),
    )


@pytest.mark.asyncio
async def test_coin_overview_captures_marketpulse_source_with_update_time() -> None:
    capture = SourcesCapture()
    tools = _tools(capture, market_data_service=_overview_service(FRESH))

    result = await tools["get_coin_overview"].ainvoke({"query": "BTC"})

    assert result.data.updated_at == FRESH
    assert result.data.stale is False
    assert [source.model_dump() for source in capture.sources] == [
        {
            "kind": "marketpulse",
            "label": "MarketPulse knowledge",
            "title": "Bitcoin (BTC) market data",
            "url": None,
            "updated_at": FRESH,
            "stale": False,
        }
    ]


@pytest.mark.asyncio
async def test_coin_overview_marks_old_data_stale() -> None:
    capture = SourcesCapture()
    tools = _tools(capture, market_data_service=_overview_service(OLD))

    result = await tools["get_coin_overview"].ainvoke({"query": "Bitcoin"})

    assert result.data.stale is True
    assert capture.sources[0].stale is True
    assert capture.sources[0].updated_at == OLD


@pytest.mark.asyncio
async def test_coin_overview_search_fallback_is_stale_without_update_time() -> None:
    capture = SourcesCapture()
    market_data_service = SimpleNamespace(
        get_market_overview=lambda: _async(SimpleNamespace(generated_at=FRESH, featured_assets=[])),
        search_assets=lambda _query: _async(SimpleNamespace(items=[BTC])),
    )
    tools = _tools(capture, market_data_service=market_data_service)

    result = await tools["get_coin_overview"].ainvoke({"query": "Bitcoin"})

    assert result.status == "partial_match"
    assert result.data.stale is True
    assert capture.sources[0].updated_at is None
    assert capture.sources[0].stale is True


@pytest.mark.asyncio
async def test_price_chart_source_uses_latest_point_time() -> None:
    capture = SourcesCapture()
    tools = _tools(capture, market_data_service=_overview_service(FRESH))

    result = await tools["get_price_chart_data"].ainvoke({"coins": ["BTC"]})

    assert result.data.series[0].updated_at == FRESH
    assert result.data.series[0].stale is False
    assert capture.sources[0].title == "Bitcoin (BTC) price history"
    assert capture.sources[0].updated_at == FRESH
    assert capture.sources[0].url is None


@pytest.mark.asyncio
async def test_news_sources_include_publisher_title_time_and_link_deduplicated_by_url() -> None:
    capture = SourcesCapture()
    news_service = SimpleNamespace(
        search_coin_news=lambda _query: _async(
            SimpleNamespace(query="bitcoin", articles=[ARTICLE, ARTICLE])
        )
    )
    tools = _tools(capture, news_service=news_service)

    await tools["get_coin_news"].ainvoke({"query": "Bitcoin"})
    await tools["get_coin_news"].ainvoke({"query": "BTC"})

    assert [source.model_dump() for source in capture.sources] == [
        {
            "kind": "news",
            "label": "Example News",
            "title": "Bitcoin update",
            "url": "https://example.com/bitcoin",
            "updated_at": "2026-11-03T08:00:00Z",
            "stale": False,
        }
    ]


@pytest.mark.asyncio
async def test_watchlist_and_alert_sources_have_no_link_or_update_time() -> None:
    capture = SourcesCapture()
    tools = _tools(
        capture,
        watchlist_service=SimpleNamespace(
            get_watchlist=lambda _user: _async(SimpleNamespace(assets=[BTC]))
        ),
        alert_service=SimpleNamespace(
            list_alerts=lambda _user: _async(
                SimpleNamespace(
                    items=[
                        SimpleNamespace(
                            name="Bitcoin",
                            symbol="BTC",
                            status="active",
                            rule_summary="Price above $120,000",
                            time_summary="One-time",
                        )
                    ]
                )
            )
        ),
    )

    await tools["list_watchlist_assets"].ainvoke({})
    await tools["list_alerts"].ainvoke({})
    await tools["list_alerts"].ainvoke({})

    assert [
        (source.title, source.url, source.updated_at, source.stale) for source in capture.sources
    ] == [
        ("Your watchlist", None, None, False),
        ("Your alerts", None, None, False),
    ]
    assert all(source.label == "MarketPulse knowledge" for source in capture.sources)


@pytest.mark.asyncio
async def test_tool_errors_and_empty_results_add_no_sources() -> None:
    capture = SourcesCapture()

    async def failing_overview() -> None:
        raise UpstreamMarketDataError(status_code=503, message="Market data is unavailable.")

    tools = _tools(
        capture,
        market_data_service=SimpleNamespace(
            get_market_overview=failing_overview,
            search_assets=lambda _query: _async(SimpleNamespace(items=[])),
        ),
        news_service=SimpleNamespace(
            search_coin_news=lambda _query: _async(SimpleNamespace(query="x", articles=[]))
        ),
        watchlist_service=SimpleNamespace(
            get_watchlist=lambda _user: _async(SimpleNamespace(assets=[]))
        ),
        alert_service=SimpleNamespace(list_alerts=lambda _user: _async(SimpleNamespace(items=[]))),
    )

    overview = await tools["get_coin_overview"].ainvoke({"query": "Bitcoin"})
    await tools["get_coin_news"].ainvoke({"query": "Bitcoin"})
    await tools["list_watchlist_assets"].ainvoke({})
    await tools["list_alerts"].ainvoke({})

    assert overview.status == "error"
    assert capture.sources == []


def test_is_stale_for_fresh_old_and_unknown_update_times() -> None:
    now = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)

    assert is_stale("2026-11-03T11:50:00Z", max_age_seconds=900, now=now) is False
    assert is_stale("2026-11-03T11:44:59Z", max_age_seconds=900, now=now) is True
    assert is_stale("2026-11-03T07:00:00+00:00", max_age_seconds=900, now=now) is True
    assert is_stale(None, max_age_seconds=900, now=now) is True
    assert is_stale("not a timestamp", max_age_seconds=900, now=now) is True


def _service_with_conversation() -> tuple[AssistantService, SimpleNamespace]:
    service = AssistantService(
        session=cast(Any, None),
        market_data_service=cast(Any, None),
        news_service=cast(Any, None),
        watchlist_service=cast(Any, None),
        alert_service=cast(Any, None),
    )
    conversation = SimpleNamespace(id=uuid4(), title=None, created_at=NOW, updated_at=NOW)
    service.repository = cast(
        Any,
        SimpleNamespace(
            get_conversation_for_user=AsyncMock(return_value=conversation),
            get_current_pending_action_for_user=AsyncMock(return_value=None),
            list_messages_for_conversation=AsyncMock(return_value=[]),
            append_message=AsyncMock(),
        ),
    )
    return service, conversation


@pytest.mark.asyncio
async def test_send_message_persists_sources_for_the_owned_conversation() -> None:
    service, conversation = _service_with_conversation()
    source = AssistantMessageSourceResponse(
        kind="marketpulse",
        label="MarketPulse knowledge",
        title="Bitcoin (BTC) market data",
        updated_at=FRESH,
    )
    service._get_graph_response = AsyncMock(  # type: ignore[method-assign]
        return_value=AssistantGraphResponse(
            message=AIMessage(content="Bitcoin trades at $100,000."),
            suggested_replies=[],
            sources=[source],
        )
    )
    user = cast(User, SimpleNamespace(id=uuid4()))

    await service.send_message(
        user, conversation.id, SendAssistantMessageRequest(content="BTC price?")
    )

    service.repository.get_conversation_for_user.assert_awaited_once_with(
        user_id=user.id, conversation_id=conversation.id
    )
    assistant_call = service.repository.append_message.await_args_list[1]
    assert assistant_call.kwargs["sources"] == [source.model_dump(mode="json")]


@pytest.mark.asyncio
async def test_send_message_without_tool_sources_stores_no_sources() -> None:
    service, conversation = _service_with_conversation()
    service._get_graph_response = AsyncMock(  # type: ignore[method-assign]
        return_value=AssistantGraphResponse(
            message=AIMessage(content="I can help with MarketPulse data."),
            suggested_replies=[],
        )
    )

    await service.send_message(
        cast(User, SimpleNamespace(id=uuid4())),
        conversation.id,
        SendAssistantMessageRequest(content="What can you do?"),
    )

    assert service.repository.append_message.await_args_list[1].kwargs["sources"] is None


def _stored_message(sources: list[dict[str, object]] | None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        role="assistant",
        content="Answer",
        suggested_replies=[],
        chart_payload=None,
        pending_action=None,
        sources=sources,
        created_at=NOW,
    )


def test_message_response_returns_persisted_sources_and_empty_list_when_missing() -> None:
    stored = {
        "kind": "news",
        "label": "Example News",
        "title": "Bitcoin update",
        "url": "https://example.com/bitcoin",
        "updated_at": "2026-11-03T08:00:00Z",
        "stale": False,
    }

    with_sources = AssistantMessageResponse.model_validate(_stored_message([stored]))
    without_sources = AssistantMessageResponse.model_validate(_stored_message(None))

    assert [source.model_dump() for source in with_sources.sources] == [stored]
    assert without_sources.sources == []
