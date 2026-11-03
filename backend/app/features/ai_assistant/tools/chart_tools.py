from __future__ import annotations

from typing import Literal

from langchain_core.tools import BaseTool, tool

from app.features.ai_assistant.schemas import (
    AssistantChartPayloadResponse,
    AssistantChartPointResponse,
    AssistantChartSeriesResponse,
)
from app.features.ai_assistant.tools.contracts import (
    AssetData,
    ChartAmbiguousAssetData,
    ChartClarificationData,
    ChartPayloadCapture,
    ChartSeriesSummaryData,
    PriceChartData,
    PriceChartInput,
    SourcesCapture,
    ToolErrorData,
    ToolResult,
)
from app.features.ai_assistant.tools.shared import add_marketpulse_source, is_stale, safe_error
from app.features.market_data.service import MarketDataService, UpstreamMarketDataError


def build_chart_tools(
    *,
    market_data_service: MarketDataService,
    chart_payload_capture: ChartPayloadCapture | None,
    sources_capture: SourcesCapture | None = None,
) -> list[BaseTool]:
    @tool("get_price_chart_data", args_schema=PriceChartInput)
    async def get_price_chart_data(
        coins: list[str],
        period: Literal["24h", "7d", "30d", "1y"] = "7d",
    ) -> ToolResult[PriceChartData | ChartClarificationData | ToolErrorData]:
        """Get historical USD prices for one to five coins and render a chart in the reply."""
        try:
            resolved_assets = []
            ambiguous: list[ChartAmbiguousAssetData] = []
            missing: list[str] = []
            for coin in coins:
                matches = await market_data_service.search_assets(coin)
                exact = [
                    item
                    for item in matches.items
                    if coin.casefold()
                    in {item.asset_id.casefold(), item.symbol.casefold(), item.name.casefold()}
                ]
                if len(exact) == 1:
                    resolved_assets.append(exact[0])
                elif not matches.items:
                    missing.append(coin)
                else:
                    ambiguous.append(
                        ChartAmbiguousAssetData(
                            query=coin,
                            matches=[
                                AssetData(symbol=item.symbol, name=item.name)
                                for item in matches.items[:5]
                            ],
                        )
                    )
            if missing or ambiguous:
                return ToolResult(
                    status="clarification_needed",
                    data=ChartClarificationData(
                        message="Please clarify the coin selection before I create the chart.",
                        not_found=missing,
                        ambiguous=ambiguous,
                    ),
                )

            history = await market_data_service.get_historical_prices(
                asset_ids=[asset.asset_id for asset in resolved_assets],
                period=period,
            )
            points_by_asset_id = {series.asset_id: series.points for series in history.series}
            if any(asset.asset_id not in points_by_asset_id for asset in resolved_assets):
                return safe_error(
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
            summaries = [series_summary(series) for series in chart_payload.series]
            for summary in summaries:
                add_marketpulse_source(
                    sources_capture,
                    f"{summary.name} ({summary.symbol}) price history",
                    updated_at=summary.updated_at,
                    stale=summary.stale,
                )
            return ToolResult(
                status="ok",
                data=PriceChartData(period=chart_payload.period, series=summaries),
            )
        except UpstreamMarketDataError as error:
            return safe_error(error.message)

    return [get_price_chart_data]


def series_summary(series: AssistantChartSeriesResponse) -> ChartSeriesSummaryData:
    prices = [point.price for point in series.points]
    start_price = prices[0]
    end_price = prices[-1]
    change_percentage = ((end_price - start_price) / start_price * 100) if start_price else 0.0
    return ChartSeriesSummaryData(
        symbol=series.symbol,
        name=series.name,
        point_count=len(prices),
        start_price=start_price,
        end_price=end_price,
        low_price=min(prices),
        high_price=max(prices),
        change_percentage=round(change_percentage, 2),
        updated_at=series.points[-1].time,
        stale=is_stale(series.points[-1].time),
    )
