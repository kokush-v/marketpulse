from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.features.ai_assistant.tools import SourcesCapture, build_read_tools
from app.features.auth.models import User
from app.features.market_data.service import UpstreamMarketDataError

NOW = datetime.now(UTC)
FRESH = (NOW - timedelta(minutes=1)).isoformat()
OLD = (NOW - timedelta(hours=5)).isoformat()
WEEK_AGO = (NOW - timedelta(days=7)).isoformat()


def _asset(asset_id: str, symbol: str, name: str, price: float) -> SimpleNamespace:
    return SimpleNamespace(
        asset_id=asset_id,
        id=asset_id,
        symbol=symbol,
        name=name,
        current_price=price,
        price_change_percentage_24h=0.0,
        market_cap_rank=1,
    )


BTC = _asset("bitcoin", "BTC", "Bitcoin", 100_000.0)
ETH = _asset("ethereum", "ETH", "Ethereum", 3_000.0)
DOGE = _asset("dogecoin", "DOGE", "Dogecoin", 0.2)
ASSETS = [BTC, ETH, DOGE]


def _alert(**overrides: Any) -> SimpleNamespace:
    values: dict[str, Any] = {
        "id": uuid4(),
        "asset_id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin",
        "status": "active",
        "scenario": "price_above",
        "trigger_mode": "currency",
        "threshold_value": 120_000.0,
        "baseline_price": None,
        "rule_summary": "Price above $120,000",
        "time_summary": "One-time",
    }
    return SimpleNamespace(**{**values, **overrides})


def _market_data_service(
    *,
    generated_at: str = FRESH,
    featured: list[SimpleNamespace] | None = None,
    search_items: list[SimpleNamespace] | None = None,
    points: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    async def search_assets(query: str) -> SimpleNamespace:
        if search_items is not None:
            return SimpleNamespace(items=search_items)
        normalized = query.casefold()
        return SimpleNamespace(
            items=[
                item
                for item in ASSETS
                if normalized in {item.asset_id, item.symbol.casefold(), item.name.casefold()}
            ]
        )

    async def get_market_overview() -> SimpleNamespace:
        return SimpleNamespace(
            generated_at=generated_at,
            featured_assets=ASSETS if featured is None else featured,
        )

    async def get_historical_prices(*, asset_ids: list[str], period: str) -> SimpleNamespace:
        return SimpleNamespace(
            period=period,
            series=[SimpleNamespace(asset_id=asset_ids[0], points=points or [])],
        )

    return SimpleNamespace(
        search_assets=search_assets,
        get_market_overview=get_market_overview,
        get_historical_prices=get_historical_prices,
    )


def _tools(
    *,
    market_data_service: SimpleNamespace | None = None,
    alerts: list[SimpleNamespace] | None = None,
    capture: SourcesCapture | None = None,
    user: Any = None,
) -> tuple[dict[str, Any], SimpleNamespace]:
    alert_service = SimpleNamespace(
        list_alerts=AsyncMock(return_value=SimpleNamespace(items=alerts or []))
    )
    tools = {
        tool.name: tool
        for tool in build_read_tools(
            user=cast(User, user or SimpleNamespace(id=uuid4())),
            market_data_service=cast(Any, market_data_service or _market_data_service()),
            news_service=cast(Any, SimpleNamespace()),
            watchlist_service=cast(Any, SimpleNamespace()),
            alert_service=cast(Any, alert_service),
            sources_capture=capture,
        )
    }
    return tools, alert_service


# Conversion


@pytest.mark.asyncio
async def test_converts_coin_amount_to_usd() -> None:
    tools, _ = _tools()

    result = await tools["convert_crypto_amount"].ainvoke(
        {"coin": "BTC", "amount": 0.5, "direction": "coin_to_usd"}
    )

    assert result.status == "ok"
    assert result.data.model_dump() == {
        "symbol": "BTC",
        "direction": "coin_to_usd",
        "input_amount": 0.5,
        "converted_amount": 50_000.0,
        "usd_rate": 100_000.0,
        "updated_at": FRESH,
        "stale": False,
    }


@pytest.mark.asyncio
async def test_converts_usd_to_coin_amount_rounded_to_eight_decimals() -> None:
    tools, _ = _tools(
        market_data_service=_market_data_service(
            featured=[_asset("ethereum", "ETH", "Ethereum", 3_333.0)]
        )
    )

    result = await tools["convert_crypto_amount"].ainvoke(
        {"coin": "Ethereum", "amount": 1000, "direction": "usd_to_coin"}
    )

    assert result.status == "ok"
    assert result.data.converted_amount == 0.30003

    tools, _ = _tools(
        market_data_service=_market_data_service(
            featured=[_asset("ethereum", "ETH", "Ethereum", 3_000.0)]
        )
    )
    result = await tools["convert_crypto_amount"].ainvoke(
        {"coin": "ETH", "amount": 1000, "direction": "usd_to_coin"}
    )
    assert result.data.converted_amount == 0.33333333


@pytest.mark.asyncio
async def test_usd_values_below_one_dollar_keep_eight_decimals() -> None:
    tools, _ = _tools(
        market_data_service=_market_data_service(
            featured=[_asset("dogecoin", "DOGE", "Dogecoin", 0.123456789)]
        )
    )

    result = await tools["convert_crypto_amount"].ainvoke(
        {"coin": "DOGE", "amount": 1, "direction": "coin_to_usd"}
    )

    assert result.data.usd_rate == 0.12345679
    assert result.data.converted_amount == 0.12345679


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", [None, 0, -5])
async def test_conversion_without_a_positive_amount_requests_clarification(
    amount: float | None,
) -> None:
    tools, _ = _tools()
    payload: dict[str, Any] = {"coin": "BTC", "direction": "coin_to_usd"}
    if amount is not None:
        payload["amount"] = amount

    result = await tools["convert_crypto_amount"].ainvoke(payload)

    assert result.status == "clarification_needed"
    assert "amount" in result.data.message


@pytest.mark.asyncio
async def test_ambiguous_coin_lists_matching_coins() -> None:
    candidates = [
        _asset("tether", "USDT", "Tether", 1.0),
        _asset("tether-gold", "XAUT", "Tether Gold", 2_400.0),
    ]
    tools, _ = _tools(market_data_service=_market_data_service(search_items=candidates))

    result = await tools["convert_crypto_amount"].ainvoke(
        {"coin": "teth", "amount": 1, "direction": "coin_to_usd"}
    )

    assert result.status == "clarification_needed"
    assert [match.symbol for match in result.data.matches] == ["USDT", "XAUT"]


@pytest.mark.asyncio
async def test_market_data_failure_returns_safe_error() -> None:
    async def failing_search(_query: str) -> None:
        raise UpstreamMarketDataError(status_code=503, message="Market data is unavailable.")

    tools, _ = _tools(market_data_service=SimpleNamespace(search_assets=failing_search))

    result = await tools["convert_crypto_amount"].ainvoke(
        {"coin": "BTC", "amount": 1, "direction": "coin_to_usd"}
    )

    assert result.status == "error"
    assert result.data.message == "Market data is unavailable."


# Price change


@pytest.mark.asyncio
@pytest.mark.parametrize("period", ["24h", "7d", "30d", "1y"])
async def test_calculates_price_change_for_each_period(period: str) -> None:
    points = [
        SimpleNamespace(time=WEEK_AGO, price=3_000.0),
        SimpleNamespace(time=FRESH, price=3_150.0),
    ]
    tools, _ = _tools(market_data_service=_market_data_service(points=points))

    result = await tools["calculate_price_change"].ainvoke({"coin": "ETH", "period": period})

    assert result.status == "ok"
    assert result.data.model_dump() == {
        "symbol": "ETH",
        "period": period,
        "start_price": 3_000.0,
        "start_time": WEEK_AGO,
        "end_price": 3_150.0,
        "end_time": FRESH,
        "change_usd": 150.0,
        "change_percentage": 5.0,
        "stale": False,
    }


@pytest.mark.asyncio
async def test_price_change_without_history_returns_safe_error() -> None:
    tools, _ = _tools(market_data_service=_market_data_service(points=[]))

    result = await tools["calculate_price_change"].ainvoke({"coin": "ETH", "period": "7d"})

    assert result.status == "error"


@pytest.mark.asyncio
async def test_price_change_without_period_requests_clarification() -> None:
    tools, _ = _tools()

    result = await tools["calculate_price_change"].ainvoke({"coin": "ETH"})

    assert result.status == "clarification_needed"


# Target distance


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("target", "difference", "percentage", "direction"),
    [(120_000, 20_000.0, 20.0, "above"), (90_000, -10_000.0, -10.0, "below")],
)
async def test_distance_to_user_target(
    target: float, difference: float, percentage: float, direction: str
) -> None:
    tools, alert_service = _tools()

    result = await tools["calculate_target_distance"].ainvoke(
        {"coin": "BTC", "target_price": target}
    )

    assert result.status == "ok"
    assert result.data.current_price == 100_000.0
    assert result.data.target_price == float(target)
    assert result.data.target_origin == "User target"
    assert result.data.difference_usd == difference
    assert result.data.difference_percentage == percentage
    assert result.data.direction == direction
    alert_service.list_alerts.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [{"coin": "BTC"}, {"coin": "BTC", "target_price": 120_000, "alert": "my alert"}],
)
async def test_distance_requires_exactly_one_target(payload: dict[str, Any]) -> None:
    tools, _ = _tools()

    result = await tools["calculate_target_distance"].ainvoke(payload)

    assert result.status == "clarification_needed"


@pytest.mark.asyncio
async def test_distance_to_fixed_price_alert() -> None:
    tools, _ = _tools(alerts=[_alert()])

    result = await tools["calculate_target_distance"].ainvoke(
        {"coin": "Bitcoin", "alert": "my alert"}
    )

    assert result.status == "ok"
    assert result.data.target_price == 120_000.0
    assert result.data.target_origin == "Alert: Price above $120,000"
    assert result.data.difference_usd == 20_000.0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scenario", "target", "difference"),
    [("price_above", 3_150.0, 150.0), ("price_below", 2_850.0, -150.0)],
)
async def test_distance_to_percent_alert_uses_baseline_price(
    scenario: str, target: float, difference: float
) -> None:
    alert = _alert(
        asset_id="ethereum",
        symbol="ETH",
        name="Ethereum",
        scenario=scenario,
        trigger_mode="percent",
        threshold_value=5.0,
        baseline_price=3_000.0,
        rule_summary=f"Price {'up' if scenario == 'price_above' else 'down'} 5%",
    )
    tools, _ = _tools(alerts=[alert])

    result = await tools["calculate_target_distance"].ainvoke({"coin": "ETH", "alert": "my alert"})

    assert result.status == "ok"
    assert result.data.target_price == target
    assert result.data.difference_usd == difference


@pytest.mark.asyncio
async def test_percent_alert_without_baseline_returns_safe_error() -> None:
    alert = _alert(trigger_mode="percent", threshold_value=5.0, baseline_price=None)
    tools, _ = _tools(alerts=[alert])

    result = await tools["calculate_target_distance"].ainvoke({"coin": "BTC", "alert": "my alert"})

    assert result.status == "error"


@pytest.mark.asyncio
async def test_several_matching_alerts_are_listed_without_a_calculation() -> None:
    alerts = [
        _alert(threshold_value=110_000.0, rule_summary="Price above $110,000"),
        _alert(threshold_value=120_000.0, rule_summary="Price above $120,000"),
        _alert(
            scenario="price_below",
            threshold_value=90_000.0,
            rule_summary="Price below $90,000",
        ),
    ]
    capture = SourcesCapture()
    tools, _ = _tools(alerts=alerts, capture=capture)

    result = await tools["calculate_target_distance"].ainvoke({"coin": "BTC", "alert": "my alert"})

    assert result.status == "clarification_needed"
    assert [item.rule for item in result.data.alerts] == [
        "Price above $110,000",
        "Price above $120,000",
        "Price below $90,000",
    ]
    assert capture.sources == []

    chosen = await tools["calculate_target_distance"].ainvoke(
        {"coin": "BTC", "alert": "price above $120,000"}
    )
    assert chosen.status == "ok"
    assert chosen.data.target_price == 120_000.0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "alert",
    [
        _alert(scenario="coin_news", trigger_mode=None, threshold_value=None),
        _alert(status="paused"),
        _alert(asset_id="ethereum", symbol="ETH", name="Ethereum"),
    ],
)
async def test_no_active_price_alert_for_the_coin_requests_clarification(
    alert: SimpleNamespace,
) -> None:
    tools, _ = _tools(alerts=[alert])

    result = await tools["calculate_target_distance"].ainvoke({"coin": "BTC", "alert": "my alert"})

    assert result.status == "clarification_needed"
    assert "no active price alert" in result.data.message
    assert result.data.alerts == []


@pytest.mark.asyncio
async def test_distance_uses_only_the_authenticated_users_alerts() -> None:
    user = SimpleNamespace(id=uuid4())
    tools, alert_service = _tools(alerts=[], user=user)

    result = await tools["calculate_target_distance"].ainvoke({"coin": "BTC", "alert": "my alert"})

    alert_service.list_alerts.assert_awaited_once_with(user)
    assert result.status == "clarification_needed"


# Sources and staleness


@pytest.mark.asyncio
async def test_calculations_record_marketpulse_sources_with_staleness() -> None:
    capture = SourcesCapture()
    points = [
        SimpleNamespace(time=WEEK_AGO, price=90_000.0),
        SimpleNamespace(time=OLD, price=100_000.0),
    ]
    tools, _ = _tools(
        market_data_service=_market_data_service(generated_at=OLD, points=points),
        capture=capture,
    )

    conversion = await tools["convert_crypto_amount"].ainvoke(
        {"coin": "BTC", "amount": 1, "direction": "coin_to_usd"}
    )
    change = await tools["calculate_price_change"].ainvoke({"coin": "BTC", "period": "7d"})
    distance = await tools["calculate_target_distance"].ainvoke(
        {"coin": "BTC", "target_price": 120_000}
    )

    assert conversion.data.stale is True
    assert change.data.stale is True
    assert distance.data.stale is True
    assert [
        (source.label, source.title, source.url, source.updated_at, source.stale)
        for source in capture.sources
    ] == [
        ("MarketPulse knowledge", "Bitcoin (BTC) price", None, OLD, True),
        ("MarketPulse knowledge", "Bitcoin (BTC) price history", None, OLD, True),
    ]


@pytest.mark.asyncio
async def test_price_outside_featured_assets_has_no_update_time_and_is_stale() -> None:
    capture = SourcesCapture()
    tools, _ = _tools(market_data_service=_market_data_service(featured=[]), capture=capture)

    result = await tools["convert_crypto_amount"].ainvoke(
        {"coin": "BTC", "amount": 1, "direction": "coin_to_usd"}
    )

    assert result.data.updated_at is None
    assert result.data.stale is True
    assert capture.sources[0].updated_at is None
    assert capture.sources[0].stale is True


@pytest.mark.asyncio
async def test_clarifications_record_no_sources() -> None:
    capture = SourcesCapture()
    tools, _ = _tools(capture=capture)

    await tools["convert_crypto_amount"].ainvoke({"coin": "BTC", "direction": "coin_to_usd"})
    await tools["calculate_target_distance"].ainvoke({"coin": "BTC", "alert": "my alert"})

    assert capture.sources == []
