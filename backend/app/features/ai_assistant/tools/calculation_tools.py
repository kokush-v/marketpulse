from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from langchain_core.tools import BaseTool, tool

from app.features.ai_assistant.tools.contracts import (
    AlertData,
    AssetData,
    CalculationClarificationData,
    CalculationPeriod,
    ConversionData,
    ConvertAmountInput,
    PriceChangeData,
    PriceChangeInput,
    SourcesCapture,
    TargetDistanceData,
    TargetDistanceInput,
    ToolErrorData,
    ToolResult,
)
from app.features.ai_assistant.tools.shared import (
    add_marketpulse_source,
    is_stale,
    normalize_alert_text,
    safe_error,
)
from app.features.alerts.schemas import AlertResponse
from app.features.alerts.service import AlertService, AlertServiceError
from app.features.auth.models import User
from app.features.market_data.schemas import AssetSearchResultResponse
from app.features.market_data.service import MarketDataService, UpstreamMarketDataError

ConversionResult = ToolResult[ConversionData | CalculationClarificationData | ToolErrorData]
PriceChangeResult = ToolResult[PriceChangeData | CalculationClarificationData | ToolErrorData]
TargetDistanceResult = ToolResult[TargetDistanceData | CalculationClarificationData | ToolErrorData]


@dataclass(frozen=True)
class CoinPrice:
    asset_id: str
    symbol: str
    name: str
    price: Decimal
    updated_at: str | None

    @property
    def label(self) -> str:
        return f"{self.name} ({self.symbol})"


def build_calculation_tools(
    *,
    user: User,
    market_data_service: MarketDataService,
    alert_service: AlertService,
    sources_capture: SourcesCapture | None = None,
) -> list[BaseTool]:
    @tool("convert_crypto_amount", args_schema=ConvertAmountInput)
    async def convert_crypto_amount(
        coin: str,
        direction: Literal["coin_to_usd", "usd_to_coin"],
        amount: float | None = None,
    ) -> ConversionResult:
        """Convert a coin amount to USD or a USD amount to a coin amount at the current rate."""
        if amount is None or amount <= 0:
            return clarification("Please provide an amount greater than zero to convert.")
        try:
            coin_price, coin_clarification = await resolve_coin_price(market_data_service, coin)
            if coin_clarification is not None:
                return coin_clarification
            assert coin_price is not None
            if coin_price.price <= 0:
                return safe_error("A current price is not available for that coin right now.")
            input_amount = Decimal(str(amount))
            if direction == "coin_to_usd":
                converted = round_usd(input_amount * coin_price.price)
            else:
                converted = round_coin(input_amount / coin_price.price)
            stale = is_stale(coin_price.updated_at)
            add_marketpulse_source(
                sources_capture,
                f"{coin_price.label} price",
                updated_at=coin_price.updated_at,
                stale=stale,
            )
            return ToolResult(
                status="ok",
                data=ConversionData(
                    symbol=coin_price.symbol,
                    direction=direction,
                    input_amount=amount,
                    converted_amount=converted,
                    usd_rate=round_usd(coin_price.price),
                    updated_at=coin_price.updated_at,
                    stale=stale,
                ),
            )
        except UpstreamMarketDataError as error:
            return safe_error(error.message)

    @tool("calculate_price_change", args_schema=PriceChangeInput)
    async def calculate_price_change(
        coin: str,
        period: CalculationPeriod | None = None,
    ) -> PriceChangeResult:
        """Calculate a coin's USD and percentage price change over 24h, 7d, 30d, or 1y."""
        if period is None:
            return clarification("Please choose a period: 24 hours, 7 days, 30 days, or 1 year.")
        try:
            asset, coin_clarification = await resolve_coin(market_data_service, coin)
            if coin_clarification is not None:
                return coin_clarification
            assert asset is not None
            history = await market_data_service.get_historical_prices(
                asset_ids=[asset.asset_id],
                period=period,
            )
            points = next(
                (series.points for series in history.series if series.asset_id == asset.asset_id),
                [],
            )
            if not points:
                return safe_error("Historical price data is not available for that coin right now.")
            start, end = points[0], points[-1]
            start_price = Decimal(str(start.price))
            end_price = Decimal(str(end.price))
            if start_price <= 0:
                return safe_error("Historical price data is not available for that coin right now.")
            stale = is_stale(end.time)
            add_marketpulse_source(
                sources_capture,
                f"{asset.name} ({asset.symbol}) price history",
                updated_at=end.time,
                stale=stale,
            )
            return ToolResult(
                status="ok",
                data=PriceChangeData(
                    symbol=asset.symbol,
                    period=period,
                    start_price=round_usd(start_price),
                    start_time=start.time,
                    end_price=round_usd(end_price),
                    end_time=end.time,
                    change_usd=round_usd(end_price - start_price),
                    change_percentage=round_percentage(
                        (end_price - start_price) / start_price * 100
                    ),
                    stale=stale,
                ),
            )
        except UpstreamMarketDataError as error:
            return safe_error(error.message)

    @tool("calculate_target_distance", args_schema=TargetDistanceInput)
    async def calculate_target_distance(
        coin: str,
        target_price: float | None = None,
        alert: str | None = None,
    ) -> TargetDistanceResult:
        """Calculate how far a coin's current price is from a USD target or one of the user's
        active price alerts."""
        if (target_price is None) == (alert is None):
            return clarification(
                "Please provide either a USD target price or which of your alerts to use."
            )
        if target_price is not None and target_price <= 0:
            return clarification("Please provide a USD target price greater than zero.")
        try:
            coin_price, coin_clarification = await resolve_coin_price(market_data_service, coin)
            if coin_clarification is not None:
                return coin_clarification
            assert coin_price is not None
            if target_price is not None:
                target = Decimal(str(target_price))
                origin = "User target"
            else:
                assert alert is not None
                matched, alert_clarification = await resolve_price_alert(
                    alert_service, user, coin_price, alert
                )
                if alert_clarification is not None:
                    return alert_clarification
                assert matched is not None
                alert_target = price_alert_target(matched)
                if alert_target is None:
                    return safe_error("The target price of that alert cannot be determined.")
                target = alert_target
                origin = f"Alert: {matched.rule_summary}"
            if coin_price.price <= 0:
                return safe_error("A current price is not available for that coin right now.")
            difference = target - coin_price.price
            stale = is_stale(coin_price.updated_at)
            add_marketpulse_source(
                sources_capture,
                f"{coin_price.label} price",
                updated_at=coin_price.updated_at,
                stale=stale,
            )
            return ToolResult(
                status="ok",
                data=TargetDistanceData(
                    symbol=coin_price.symbol,
                    current_price=round_usd(coin_price.price),
                    target_price=round_usd(target),
                    target_origin=origin,
                    difference_usd=round_usd(difference),
                    difference_percentage=round_percentage(difference / coin_price.price * 100),
                    direction="above" if difference >= 0 else "below",
                    updated_at=coin_price.updated_at,
                    stale=stale,
                ),
            )
        except (UpstreamMarketDataError, AlertServiceError) as error:
            return safe_error(error.message)

    return [convert_crypto_amount, calculate_price_change, calculate_target_distance]


def clarification(
    message: str,
    *,
    matches: list[AssetData] | None = None,
    alerts: list[AlertData] | None = None,
) -> ToolResult[CalculationClarificationData]:
    return ToolResult(
        status="clarification_needed",
        data=CalculationClarificationData(
            message=message,
            matches=matches or [],
            alerts=alerts or [],
        ),
    )


async def resolve_coin(
    market_data_service: MarketDataService,
    query: str,
) -> tuple[AssetSearchResultResponse | None, ToolResult[CalculationClarificationData] | None]:
    matches = await market_data_service.search_assets(query.strip())
    normalized = query.strip().casefold()
    exact = [
        item
        for item in matches.items
        if normalized in {item.asset_id.casefold(), item.symbol.casefold(), item.name.casefold()}
    ]
    if len(exact) == 1:
        return exact[0], None
    if not matches.items:
        return None, clarification("No coin matches that name. Please check the coin name.")
    return None, clarification(
        "Several coins match that name. Ask which one the user means.",
        matches=[AssetData(symbol=item.symbol, name=item.name) for item in matches.items[:5]],
    )


async def resolve_coin_price(
    market_data_service: MarketDataService,
    query: str,
) -> tuple[CoinPrice | None, ToolResult[CalculationClarificationData] | None]:
    asset, coin_clarification = await resolve_coin(market_data_service, query)
    if coin_clarification is not None:
        return None, coin_clarification
    assert asset is not None
    overview = await market_data_service.get_market_overview()
    featured = next((item for item in overview.featured_assets if item.id == asset.asset_id), None)
    if featured is not None:
        return CoinPrice(
            asset_id=asset.asset_id,
            symbol=featured.symbol,
            name=featured.name,
            price=Decimal(str(featured.current_price)),
            updated_at=overview.generated_at,
        ), None
    # Search results carry no update time, so a price from them is treated as stale.
    return CoinPrice(
        asset_id=asset.asset_id,
        symbol=asset.symbol,
        name=asset.name,
        price=Decimal(str(asset.current_price)),
        updated_at=None,
    ), None


async def resolve_price_alert(
    alert_service: AlertService,
    user: User,
    coin_price: CoinPrice,
    reference: str,
) -> tuple[AlertResponse | None, ToolResult[CalculationClarificationData] | None]:
    alerts = await alert_service.list_alerts(user)
    candidates = [
        item
        for item in alerts.items
        if item.asset_id == coin_price.asset_id
        and item.status == "active"
        and item.scenario in {"price_above", "price_below"}
    ]
    if len(candidates) > 1:
        normalized_reference = normalize_alert_text(reference)
        by_rule = [
            item
            for item in candidates
            if normalize_alert_text(item.rule_summary) in normalized_reference
        ]
        if len(by_rule) == 1:
            candidates = by_rule
    if len(candidates) == 1:
        return candidates[0], None
    if not candidates:
        return None, clarification(
            f"There is no active price alert for {coin_price.label}. Do not calculate a distance."
        )
    return None, clarification(
        "Several active price alerts match. List them and ask which one to use.",
        alerts=[
            AlertData(
                coin=f"{item.name} ({item.symbol})",
                status=item.status,
                rule=item.rule_summary,
                schedule=item.time_summary,
            )
            for item in candidates[:5]
        ],
    )


def price_alert_target(alert: AlertResponse) -> Decimal | None:
    if alert.threshold_value is None:
        return None
    threshold = Decimal(str(alert.threshold_value))
    if alert.trigger_mode == "currency":
        return threshold
    if alert.trigger_mode == "percent" and alert.baseline_price is not None:
        baseline = Decimal(str(alert.baseline_price))
        sign = 1 if alert.scenario == "price_above" else -1
        return baseline * (1 + sign * threshold / 100)
    return None


def round_usd(value: Decimal) -> float:
    places = Decimal("0.01") if abs(value) >= 1 else Decimal("0.00000001")
    return float(value.quantize(places, rounding=ROUND_HALF_UP))


def round_coin(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP))


def round_percentage(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
