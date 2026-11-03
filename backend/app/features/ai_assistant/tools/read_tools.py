from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from app.features.ai_assistant.schemas import AssistantMessageSourceResponse
from app.features.ai_assistant.tools.contracts import (
    AlertData,
    AlertsData,
    AssetData,
    CoinNewsData,
    CoinOverviewLookupData,
    CoinQueryInput,
    CoinSummary,
    NewsArticleData,
    SourcesCapture,
    ToolErrorData,
    ToolResult,
    WatchlistAssetsData,
)
from app.features.ai_assistant.tools.shared import add_marketpulse_source, is_stale, safe_error
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
    sources_capture: SourcesCapture | None = None,
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
                stale = is_stale(overview.generated_at)
                add_marketpulse_source(
                    sources_capture,
                    f"{asset.name} ({asset.symbol}) market data",
                    updated_at=overview.generated_at,
                    stale=stale,
                )
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
                        ),
                        updated_at=overview.generated_at,
                        stale=stale,
                    ),
                )

            matches = await market_data_service.search_assets(normalized_query)
            # Search results carry no update time, so they are always treated as stale.
            for item in matches.items[:5]:
                add_marketpulse_source(
                    sources_capture,
                    f"{item.name} ({item.symbol}) market data",
                    stale=True,
                )
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
                    stale=bool(matches.items),
                ),
            )
        except UpstreamMarketDataError as error:
            return safe_error(error.message)

    @tool("get_coin_news", args_schema=CoinQueryInput)
    async def get_coin_news(query: str) -> ToolResult[CoinNewsData | ToolErrorData]:
        """Get the latest available news for a named cryptocurrency."""
        try:
            news = await news_service.search_coin_news(query)
            if sources_capture is not None:
                for article in news.articles[:5]:
                    sources_capture.add(
                        AssistantMessageSourceResponse(
                            kind="news",
                            label=article.source,
                            title=article.title,
                            url=article.url,
                            updated_at=article.published_at,
                        )
                    )
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
            if watchlist.assets:
                add_marketpulse_source(sources_capture, "Your watchlist")
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
            if alerts.items:
                add_marketpulse_source(sources_capture, "Your alerts")
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
