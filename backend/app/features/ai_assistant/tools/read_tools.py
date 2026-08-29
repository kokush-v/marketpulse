from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from app.features.ai_assistant.tools.contracts import (
    AlertData,
    AlertsData,
    AssetData,
    CoinNewsData,
    CoinOverviewLookupData,
    CoinQueryInput,
    CoinSummary,
    NewsArticleData,
    ToolErrorData,
    ToolResult,
    WatchlistAssetsData,
)
from app.features.ai_assistant.tools.shared import safe_error
from app.features.alerts.service import AlertService, AlertServiceError
from app.features.auth.models import User
from app.features.market_data.service import MarketDataService, UpstreamMarketDataError
from app.features.news.service import NewsService, NewsServiceError
from app.features.watchlists.service import WatchlistService, WatchlistServiceError


def build_read_tools(
    *,
    user: User,
    market_data_service: MarketDataService,
    news_service: NewsService,
    watchlist_service: WatchlistService,
    alert_service: AlertService,
) -> list[BaseTool]:
    @tool("get_coin_overview", args_schema=CoinQueryInput)
    async def get_coin_overview(
        query: str,
    ) -> ToolResult[CoinOverviewLookupData | ToolErrorData]:
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
                return ToolResult(
                    status="ok",
                    data=CoinOverviewLookupData(
                        coin=CoinSummary(
                            symbol=asset.symbol,
                            name=asset.name,
                            description=asset.description,
                            current_price=asset.current_price,
                            price_change_percentage_24h=asset.price_change_percentage_24h,
                            market_cap_rank=asset.market_cap_rank,
                        )
                    ),
                )

            matches = await market_data_service.search_assets(normalized_query)
            return ToolResult(
                status="not_found" if not matches.items else "partial_match",
                data=CoinOverviewLookupData(
                    message=(
                        "No detailed featured-asset profile is available for that coin right now."
                    ),
                    matches=[
                        CoinSummary(
                            symbol=item.symbol,
                            name=item.name,
                            current_price=item.current_price,
                            price_change_percentage_24h=item.price_change_percentage_24h,
                            market_cap_rank=item.market_cap_rank,
                        )
                        for item in matches.items[:5]
                    ],
                ),
            )
        except UpstreamMarketDataError as error:
            return safe_error(error.message)

    @tool("get_coin_news", args_schema=CoinQueryInput)
    async def get_coin_news(query: str) -> ToolResult[CoinNewsData | ToolErrorData]:
        """Get the latest available news for a named cryptocurrency."""
        try:
            news = await news_service.search_coin_news(query)
            return ToolResult(
                status="ok",
                data=CoinNewsData(
                    articles=[
                        NewsArticleData(
                            title=article.title,
                            summary=article.summary,
                            url=article.url,
                            published_at=article.published_at,
                            source=article.source,
                        )
                        for article in news.articles[:5]
                    ]
                ),
            )
        except (NewsServiceError, UpstreamMarketDataError) as error:
            return safe_error(error.message)

    @tool("list_watchlist_assets")
    async def list_watchlist_assets() -> ToolResult[WatchlistAssetsData | ToolErrorData]:
        """List the authenticated user's saved watchlist assets."""
        try:
            watchlist = await watchlist_service.get_watchlist(user)
            return ToolResult(
                status="ok",
                data=WatchlistAssetsData(
                    assets=[
                        AssetData(symbol=asset.symbol, name=asset.name)
                        for asset in watchlist.assets
                    ]
                ),
            )
        except WatchlistServiceError as error:
            return safe_error(error.message)

    @tool("list_alerts")
    async def list_alerts() -> ToolResult[AlertsData | ToolErrorData]:
        """List the authenticated user's current price and news alerts."""
        try:
            alerts = await alert_service.list_alerts(user)
            return ToolResult(
                status="ok",
                data=AlertsData(
                    alerts=[
                        AlertData(
                            coin=f"{alert.name} ({alert.symbol})",
                            status=alert.status,
                            rule=alert.rule_summary,
                            schedule=alert.time_summary,
                        )
                        for alert in alerts.items
                    ]
                ),
            )
        except AlertServiceError as error:
            return safe_error(error.message)

    return [get_coin_overview, get_coin_news, list_watchlist_assets, list_alerts]
