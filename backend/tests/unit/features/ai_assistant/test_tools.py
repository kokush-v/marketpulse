from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.features.ai_assistant.actions import PendingActionCapture
from app.features.ai_assistant.schemas import AssistantPendingActionResponse
from app.features.ai_assistant.tools import ChartPayloadCapture, ToolResult, build_read_tools
from app.features.ai_assistant.tools.shared import resolve_alert
from app.features.auth.models import User


def tool_map() -> dict[str, Any]:
    asset = SimpleNamespace(
        id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        description="A digital asset.",
        categories=["Layer 1"],
        current_price=100_000.0,
        price_change_24h=2_000.0,
        price_change_percentage_24h=2.04,
        market_cap_rank=1,
        market_cap=2_000_000_000_000.0,
    )

    async def search_assets(query: str) -> SimpleNamespace:
        assets = {
            "bitcoin": asset,
            "btc": asset,
            "ethereum": SimpleNamespace(
                asset_id="ethereum",
                symbol="ETH",
                name="Ethereum",
                current_price=3_500.0,
                price_change_percentage_24h=1.0,
                market_cap_rank=2,
            ),
        }
        return SimpleNamespace(items=[assets[query.lower()]] if query.lower() in assets else [])

    market_data_service = SimpleNamespace(
        get_market_overview=lambda: _async(SimpleNamespace(featured_assets=[asset])),
        search_assets=search_assets,
        get_historical_prices=lambda **_: _async(
            SimpleNamespace(
                period="7d",
                series=[
                    SimpleNamespace(
                        asset_id="bitcoin",
                        points=[
                            SimpleNamespace(time="2026-08-28T00:00:00Z", price=100_000.0),
                            SimpleNamespace(time="2026-08-29T00:00:00Z", price=101_000.0),
                        ],
                    )
                ],
            )
        ),
    )
    news_service = SimpleNamespace(
        search_coin_news=lambda _query: _async(
            SimpleNamespace(
                query="bitcoin",
                articles=[
                    SimpleNamespace(
                        title="Bitcoin update",
                        summary="Market update.",
                        url="https://example.com/bitcoin",
                        published_at="2026-08-29T00:00:00Z",
                        source="Example News",
                    )
                ],
            )
        )
    )
    watchlist_service = SimpleNamespace(
        get_watchlist=lambda _user: _async(
            SimpleNamespace(
                assets=[
                    SimpleNamespace(asset_id="bitcoin", symbol="BTC", name="Bitcoin"),
                ]
            )
        )
    )
    alert_service = SimpleNamespace(
        list_alerts=lambda _user: _async(
            SimpleNamespace(
                items=[
                    SimpleNamespace(
                        id="internal-alert-id",
                        name="Bitcoin",
                        symbol="BTC",
                        status="active",
                        rule_summary="Price above $100,000",
                        time_summary="Always",
                    )
                ]
            )
        )
    )
    return {
        tool.name: tool
        for tool in build_read_tools(
            user=cast(User, SimpleNamespace()),
            market_data_service=cast(Any, market_data_service),
            news_service=cast(Any, news_service),
            watchlist_service=cast(Any, watchlist_service),
            alert_service=cast(Any, alert_service),
        )
    }


async def _async(value: Any) -> Any:
    return value


@pytest.mark.asyncio
async def test_read_tools_exclude_internal_identifiers_and_redundant_metadata() -> None:
    tools = tool_map()

    overview = await tools["get_coin_overview"].ainvoke({"query": "Bitcoin"})
    news = await tools["get_coin_news"].ainvoke({"query": "Bitcoin"})
    watchlist = await tools["list_watchlist_assets"].ainvoke({})
    alerts = await tools["list_alerts"].ainvoke({})

    assert isinstance(overview, ToolResult)
    assert overview.status == "ok"
    assert json.loads(str(overview))["data"]["coin"]["symbol"] == "BTC"
    assert overview.data.coin is not None
    assert overview.data.coin.model_dump() == {
        "symbol": "BTC",
        "name": "Bitcoin",
        "description": "A digital asset.",
        "current_price": 100_000.0,
        "price_change_percentage_24h": 2.04,
        "market_cap_rank": 1,
    }
    assert news.status == "ok"
    assert watchlist.data.model_dump() == {"assets": [{"symbol": "BTC", "name": "Bitcoin"}]}
    assert alerts.data.model_dump() == {
        "alerts": [
            {
                "coin": "Bitcoin (BTC)",
                "status": "active",
                "rule": "Price above $100,000",
                "schedule": "Always",
            }
        ]
    }


@pytest.mark.asyncio
async def test_price_chart_tool_persists_safe_chart_payload_without_provider_ids() -> None:
    capture = ChartPayloadCapture()
    asset = SimpleNamespace(asset_id="bitcoin", symbol="BTC", name="Bitcoin")
    market_data_service = SimpleNamespace(
        search_assets=lambda _query: _async(SimpleNamespace(items=[asset])),
        get_historical_prices=lambda **_: _async(
            SimpleNamespace(
                period="7d",
                series=[
                    SimpleNamespace(
                        asset_id="bitcoin",
                        points=[SimpleNamespace(time="2026-08-29T00:00:00Z", price=101_000.0)],
                    )
                ],
            )
        ),
        get_market_overview=lambda: _async(SimpleNamespace(featured_assets=[])),
    )
    tools = {
        tool.name: tool
        for tool in build_read_tools(
            user=cast(User, SimpleNamespace()),
            market_data_service=cast(Any, market_data_service),
            news_service=cast(Any, SimpleNamespace()),
            watchlist_service=cast(Any, SimpleNamespace()),
            alert_service=cast(Any, SimpleNamespace()),
            chart_payload_capture=capture,
        )
    }

    result = await tools["get_price_chart_data"].ainvoke({"coins": ["BTC"]})

    assert isinstance(result, ToolResult)
    assert result.status == "ok"
    assert [series.model_dump() for series in result.data.series] == [
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "point_count": 1,
            "start_price": 101_000.0,
            "end_price": 101_000.0,
            "low_price": 101_000.0,
            "high_price": 101_000.0,
            "change_percentage": 0.0,
        }
    ]
    assert "points" not in str(result)
    assert capture.payload is not None
    assert capture.payload.period == "7d"
    assert capture.payload.series[0].symbol == "BTC"
    assert "asset_id" not in str(result)


@pytest.mark.asyncio
async def test_watchlist_proposal_is_compact_and_requires_confirmation() -> None:
    asset = SimpleNamespace(
        asset_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        image_url=None,
    )
    action = AssistantPendingActionResponse.model_validate(
        {
            "id": uuid4(),
            "action_type": "add_watchlist_asset",
            "status": "pending",
            "summary": {
                "title": "Add Bitcoin (BTC) to your watchlist",
                "details": ["Asset: Bitcoin (BTC)"],
            },
        }
    )
    capture = PendingActionCapture()
    action_service = SimpleNamespace(propose=AsyncMock(return_value=action))
    watchlist_service = SimpleNamespace(
        search_assets=lambda _query: _async(SimpleNamespace(items=[asset])),
        get_watchlist=lambda _user: _async(SimpleNamespace(assets=[])),
    )
    tools = {
        tool.name: tool
        for tool in build_read_tools(
            user=cast(User, SimpleNamespace(id=uuid4())),
            market_data_service=cast(Any, SimpleNamespace()),
            news_service=cast(Any, SimpleNamespace()),
            watchlist_service=cast(Any, watchlist_service),
            alert_service=cast(Any, SimpleNamespace()),
            conversation=cast(Any, SimpleNamespace(id=uuid4())),
            action_service=cast(Any, action_service),
            pending_action_capture=capture,
        )
    }

    result = await tools["propose_add_watchlist_asset"].ainvoke({"query": "BTC"})

    assert result.status == "confirmation_required"
    assert result.data.model_dump() == {
        "action_type": "add_watchlist_asset",
        "summary": {
            "title": "Add Bitcoin (BTC) to your watchlist",
            "details": ["Asset: Bitcoin (BTC)"],
        },
    }
    assert capture.pending_action == action
    action_service.propose.assert_awaited_once()


@pytest.mark.asyncio
async def test_watchlist_removal_requests_clarification_when_asset_is_not_saved() -> None:
    watchlist_service = SimpleNamespace(
        get_watchlist=lambda _user: _async(SimpleNamespace(assets=[])),
    )
    tools = {
        tool.name: tool
        for tool in build_read_tools(
            user=cast(User, SimpleNamespace(id=uuid4())),
            market_data_service=cast(Any, SimpleNamespace()),
            news_service=cast(Any, SimpleNamespace()),
            watchlist_service=cast(Any, watchlist_service),
            alert_service=cast(Any, SimpleNamespace()),
            conversation=cast(Any, SimpleNamespace(id=uuid4())),
            action_service=cast(Any, SimpleNamespace()),
        )
    }

    result = await tools["propose_remove_watchlist_asset"].ainvoke({"query": "BTC"})

    assert result.status == "clarification_needed"
    assert result.data.matches == []


@pytest.mark.asyncio
async def test_alert_proposal_requests_missing_required_fields() -> None:
    tools = {
        tool.name: tool
        for tool in build_read_tools(
            user=cast(User, SimpleNamespace(id=uuid4())),
            market_data_service=cast(Any, SimpleNamespace()),
            news_service=cast(Any, SimpleNamespace()),
            watchlist_service=cast(Any, SimpleNamespace()),
            alert_service=cast(Any, SimpleNamespace()),
            conversation=cast(Any, SimpleNamespace(id=uuid4())),
            action_service=cast(Any, SimpleNamespace()),
        )
    }

    result = await tools["propose_create_alert"].ainvoke({"asset": "BTC"})

    assert result.status == "clarification_needed"
    assert result.data.model_dump() == {
        "message": "Please provide the missing alert details.",
        "missing_fields": ["scenario"],
    }


def _alert(asset_id: str, symbol: str, name: str, rule_summary: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        asset_id=asset_id,
        symbol=symbol,
        name=name,
        status="active",
        rule_summary=rule_summary,
        time_summary="One-time",
    )


BTC_ALERT = _alert("bitcoin", "BTC", "Bitcoin", "Price above $120,000")
SOL_ABOVE_ALERT = _alert("solana", "SOL", "Solana", "Price above $200")
SOL_NEWS_ALERT = _alert("solana", "SOL", "Solana", "Any new coin news")


def _alert_service(*alerts: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(list_alerts=AsyncMock(return_value=SimpleNamespace(items=list(alerts))))


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["Bitcoin", "btc", "my BTC alert", "bitcoin"])
async def test_resolve_alert_matches_single_alert_by_coin(query: str) -> None:
    alert, clarification = await resolve_alert(
        cast(Any, _alert_service(BTC_ALERT, SOL_ABOVE_ALERT)),
        cast(User, SimpleNamespace()),
        query,
    )

    assert clarification is None
    assert alert is BTC_ALERT


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["Solana price above $200", "SOL price above 200"])
async def test_resolve_alert_narrows_several_matches_by_condition(query: str) -> None:
    alert, clarification = await resolve_alert(
        cast(Any, _alert_service(SOL_ABOVE_ALERT, SOL_NEWS_ALERT)),
        cast(User, SimpleNamespace()),
        query,
    )

    assert clarification is None
    assert alert is SOL_ABOVE_ALERT


@pytest.mark.asyncio
async def test_resolve_alert_lists_matches_when_several_alerts_match_coin() -> None:
    alert, clarification = await resolve_alert(
        cast(Any, _alert_service(BTC_ALERT, SOL_ABOVE_ALERT, SOL_NEWS_ALERT)),
        cast(User, SimpleNamespace()),
        "Solana",
    )

    assert alert is None
    assert clarification is not None
    assert clarification.status == "clarification_needed"
    assert [item.rule for item in clarification.data.matches] == [
        "Price above $200",
        "Any new coin news",
    ]
    assert all(item.coin == "Solana (SOL)" for item in clarification.data.matches)


@pytest.mark.asyncio
async def test_resolve_alert_reports_no_match_with_user_alerts() -> None:
    alert, clarification = await resolve_alert(
        cast(Any, _alert_service(BTC_ALERT, SOL_ABOVE_ALERT)),
        cast(User, SimpleNamespace()),
        "Dogecoin",
    )

    assert alert is None
    assert clarification is not None
    assert clarification.status == "clarification_needed"
    assert "No matching alert" in clarification.data.message
    assert [item.coin for item in clarification.data.matches] == ["Bitcoin (BTC)", "Solana (SOL)"]


@pytest.mark.asyncio
async def test_resolve_alert_searches_only_the_users_alerts() -> None:
    user = cast(User, SimpleNamespace(id=uuid4()))
    alert_service = _alert_service(BTC_ALERT)

    alert, _clarification = await resolve_alert(cast(Any, alert_service), user, "Bitcoin")

    alert_service.list_alerts.assert_awaited_once_with(user)
    assert alert is BTC_ALERT


def _alert_action_tools(
    action_service: SimpleNamespace,
    alert_service: SimpleNamespace,
    watchlist_service: SimpleNamespace | None = None,
) -> dict[str, Any]:
    return {
        tool.name: tool
        for tool in build_read_tools(
            user=cast(User, SimpleNamespace(id=uuid4())),
            market_data_service=cast(Any, SimpleNamespace()),
            news_service=cast(Any, SimpleNamespace()),
            watchlist_service=cast(Any, watchlist_service or SimpleNamespace()),
            alert_service=cast(Any, alert_service),
            conversation=cast(Any, SimpleNamespace(id=uuid4())),
            action_service=cast(Any, action_service),
        )
    }


def _pending_action(action_type: str) -> AssistantPendingActionResponse:
    return AssistantPendingActionResponse.model_validate(
        {
            "id": uuid4(),
            "action_type": action_type,
            "status": "pending",
            "summary": {
                "title": "Alert for Bitcoin (BTC)",
                "details": ["Rule: Price above $120,000"],
            },
        }
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "action_type"),
    [
        ("propose_pause_alert", "pause_alert"),
        ("propose_resume_alert", "resume_alert"),
        ("propose_delete_alert", "delete_alert"),
    ],
)
async def test_alert_lifecycle_proposal_accepts_coin_only_argument(
    tool_name: str, action_type: str
) -> None:
    action_service = SimpleNamespace(propose=AsyncMock(return_value=_pending_action(action_type)))
    tools = _alert_action_tools(action_service, _alert_service(BTC_ALERT, SOL_ABOVE_ALERT))

    result = await tools[tool_name].ainvoke({"alert": "Bitcoin"})

    assert result.status == "confirmation_required"
    assert action_service.propose.await_args.kwargs["action_type"] == action_type
    assert action_service.propose.await_args.kwargs["target_id"] == str(BTC_ALERT.id)


@pytest.mark.asyncio
async def test_alert_update_proposal_accepts_coin_only_argument() -> None:
    action_service = SimpleNamespace(
        propose=AsyncMock(return_value=_pending_action("update_alert"))
    )
    watchlist_service = SimpleNamespace(
        get_watchlist=AsyncMock(
            return_value=SimpleNamespace(
                assets=[
                    SimpleNamespace(
                        asset_id="bitcoin", symbol="BTC", name="Bitcoin", image_url=None
                    )
                ]
            )
        )
    )
    tools = _alert_action_tools(
        action_service, _alert_service(BTC_ALERT, SOL_ABOVE_ALERT), watchlist_service
    )

    result = await tools["propose_update_alert"].ainvoke(
        {
            "alert": "BTC",
            "asset": "Bitcoin",
            "scenario": "price_above",
            "trigger_mode": "currency",
            "threshold_value": 130000,
        }
    )

    assert result.status == "confirmation_required"
    assert action_service.propose.await_args.kwargs["action_type"] == "update_alert"
    assert action_service.propose.await_args.kwargs["target_id"] == str(BTC_ALERT.id)
