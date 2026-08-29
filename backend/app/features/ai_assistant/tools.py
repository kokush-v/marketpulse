from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field, field_validator

from app.features.ai_assistant.schemas import (
    AssistantChartPayloadResponse,
    AssistantChartPointResponse,
    AssistantChartSeriesResponse,
)
from app.features.alerts.service import AlertService, AlertServiceError
from app.features.auth.models import User
from app.features.market_data.service import MarketDataService, UpstreamMarketDataError
from app.features.news.service import NewsService, NewsServiceError
from app.features.watchlists.service import WatchlistService, WatchlistServiceError


class CoinQueryInput(BaseModel):
    query: str = Field(min_length=1, max_length=120, description="Coin name, symbol, or asset ID")


class PriceChartInput(BaseModel):
    coins: list[str] = Field(
        min_length=1,
        max_length=5,
        description="One to five unambiguous coin names or symbols.",
    )
    period: Literal["24h", "7d", "30d", "1y"] = Field(
        default="7d",
        description="Chart period. Use 7d when the user did not request a period.",
    )

    @field_validator("coins")
    @classmethod
    def validate_coins(cls, coins: list[str]) -> list[str]:
        normalized = [coin.strip() for coin in coins]
        if any(not coin for coin in normalized):
            raise ValueError("Coin names must not be blank")
        if len({coin.casefold() for coin in normalized}) != len(normalized):
            raise ValueError("Coins must be distinct")
        return normalized


@dataclass
class ChartPayloadCapture:
    payload: AssistantChartPayloadResponse | None = None


def build_read_tools(
    *,
    user: User,
    market_data_service: MarketDataService,
    news_service: NewsService,
    watchlist_service: WatchlistService,
    alert_service: AlertService,
    chart_payload_capture: ChartPayloadCapture | None = None,
) -> list[BaseTool]:
    """Create request-scoped tools; ownership is always derived from ``user``."""

    @tool("get_coin_overview", args_schema=CoinQueryInput)
    async def get_coin_overview(query: str) -> dict[str, Any]:
        """Get a compact market summary and description for a named cryptocurrency."""
        normalized_query = query.strip()
        try:
            overview = await market_data_service.get_market_overview()
            normalized = normalized_query.lower()
            asset = next(
                (
                    item
                    for item in overview.featured_assets
                    if normalized in {item.id.lower(), item.symbol.lower(), item.name.lower()}
                ),
                None,
            )
            if asset is not None:
                return {
                    "status": "ok",
                    "coin": {
                        "symbol": asset.symbol,
                        "name": asset.name,
                        "description": asset.description,
                        "current_price": asset.current_price,
                        "price_change_percentage_24h": asset.price_change_percentage_24h,
                        "market_cap_rank": asset.market_cap_rank,
                    },
                }

            matches = await market_data_service.search_assets(normalized_query)
            return {
                "status": "not_found" if not matches.items else "partial_match",
                "message": (
                    "No detailed featured-asset profile is available for that coin right now."
                ),
                "matches": [
                    {
                        "symbol": item.symbol,
                        "name": item.name,
                        "current_price": item.current_price,
                        "price_change_percentage_24h": item.price_change_percentage_24h,
                        "market_cap_rank": item.market_cap_rank,
                    }
                    for item in matches.items[:5]
                ],
            }
        except UpstreamMarketDataError as error:
            return _safe_error(error.message)

    @tool("get_coin_news", args_schema=CoinQueryInput)
    async def get_coin_news(query: str) -> dict[str, Any]:
        """Get the latest available news for a named cryptocurrency."""
        try:
            news = await news_service.search_coin_news(query)
            return {
                "status": "ok",
                "articles": [
                    {
                        "title": article.title,
                        "summary": article.summary,
                        "url": article.url,
                        "published_at": article.published_at,
                        "source": article.source,
                    }
                    for article in news.articles[:5]
                ],
            }
        except (NewsServiceError, UpstreamMarketDataError) as error:
            return _safe_error(error.message)

    @tool("list_watchlist_assets")
    async def list_watchlist_assets() -> dict[str, Any]:
        """List the authenticated user's saved watchlist assets."""
        try:
            watchlist = await watchlist_service.get_watchlist(user)
            return {
                "status": "ok",
                "assets": [
                    {"symbol": asset.symbol, "name": asset.name} for asset in watchlist.assets
                ],
            }
        except WatchlistServiceError as error:
            return _safe_error(error.message)

    @tool("list_alerts")
    async def list_alerts() -> dict[str, Any]:
        """List the authenticated user's current price and news alerts."""
        try:
            alerts = await alert_service.list_alerts(user)
            return {
                "status": "ok",
                "alerts": [
                    {
                        "coin": f"{alert.name} ({alert.symbol})",
                        "status": alert.status,
                        "rule": alert.rule_summary,
                        "schedule": alert.time_summary,
                    }
                    for alert in alerts.items
                ],
            }
        except AlertServiceError as error:
            return _safe_error(error.message)

    @tool("get_price_chart_data", args_schema=PriceChartInput)
    async def get_price_chart_data(
        coins: list[str],
        period: Literal["24h", "7d", "30d", "1y"] = "7d",
    ) -> dict[str, Any]:
        """Get historical USD prices for one to five coins and render a chart in the reply."""
        try:
            resolved_assets = []
            ambiguous: list[dict[str, Any]] = []
            missing: list[str] = []

            for coin in coins:
                matches = await market_data_service.search_assets(coin)
                exact_matches = [
                    item
                    for item in matches.items
                    if coin.casefold()
                    in {item.asset_id.casefold(), item.symbol.casefold(), item.name.casefold()}
                ]
                if len(exact_matches) == 1:
                    resolved_assets.append(exact_matches[0])
                elif not matches.items:
                    missing.append(coin)
                else:
                    ambiguous.append(
                        {
                            "query": coin,
                            "matches": [
                                {"symbol": item.symbol, "name": item.name}
                                for item in matches.items[:5]
                            ],
                        }
                    )

            if missing or ambiguous:
                return {
                    "status": "clarification_needed",
                    "message": "Please clarify the coin selection before I create the chart.",
                    "not_found": missing,
                    "ambiguous": ambiguous,
                }

            history = await market_data_service.get_historical_prices(
                asset_ids=[asset.asset_id for asset in resolved_assets],
                period=period,
            )
            points_by_asset_id = {series.asset_id: series.points for series in history.series}
            if any(asset.asset_id not in points_by_asset_id for asset in resolved_assets):
                return _safe_error(
                    "Historical price data is incomplete right now. Please try again."
                )

            chart_payload = AssistantChartPayloadResponse(
                period=history.period,
                series=[
                    AssistantChartSeriesResponse(
                        symbol=asset.symbol,
                        name=asset.name,
                        points=[
                            AssistantChartPointResponse(time=point.time, price=point.price)
                            for point in points_by_asset_id[asset.asset_id]
                        ],
                    )
                    for asset in resolved_assets
                ],
            )
            if chart_payload_capture is not None:
                chart_payload_capture.payload = chart_payload
            return {
                "status": "ok",
                "chart_summary": {
                    "period": chart_payload.period,
                    "series": [_series_summary(series) for series in chart_payload.series],
                },
            }
        except UpstreamMarketDataError as error:
            return _safe_error(error.message)

    return [
        get_coin_overview,
        get_coin_news,
        list_watchlist_assets,
        list_alerts,
        get_price_chart_data,
    ]


def _safe_error(message: str) -> dict[str, str]:
    return {"status": "error", "message": message}


def _series_summary(series: AssistantChartSeriesResponse) -> dict[str, float | int | str]:
    prices = [point.price for point in series.points]
    start_price = prices[0]
    end_price = prices[-1]
    change_percentage = ((end_price - start_price) / start_price * 100) if start_price else 0.0
    return {
        "symbol": series.symbol,
        "name": series.name,
        "point_count": len(prices),
        "start_price": start_price,
        "end_price": end_price,
        "low_price": min(prices),
        "high_price": max(prices),
        "change_percentage": round(change_percentage, 2),
    }
