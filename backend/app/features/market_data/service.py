from __future__ import annotations

from dataclasses import dataclass

import httpx
from fastapi import status

from app.core.config import settings
from app.features.market_data.schemas import (
    AssetSearchResponse,
    AssetSearchResultResponse,
    CoinNewsSearchResponse,
    HistoricalPriceChartResponse,
    MarketOverviewResponse,
)


@dataclass
class UpstreamMarketDataError(Exception):
    status_code: int
    message: str


class MarketDataService:
    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.market_data_api_base_url).rstrip("/")

    async def get_market_overview(self) -> MarketOverviewResponse:
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=15.0) as client:
                response = await client.get("/api/v1/market-overview")
        except httpx.TimeoutException as exc:
            raise self._upstream_exception(
                status.HTTP_504_GATEWAY_TIMEOUT,
                "Market overview timed out upstream.",
            ) from exc
        except httpx.HTTPError as exc:
            raise self._upstream_exception(
                status.HTTP_502_BAD_GATEWAY,
                "Market overview is unavailable right now.",
            ) from exc

        if response.status_code >= 400:
            raise self._upstream_exception(
                self._map_status_code(response.status_code),
                self._extract_message(response),
            )

        return MarketOverviewResponse.model_validate(response.json())

    async def search_assets(self, query: str) -> AssetSearchResponse:
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=15.0) as client:
                response = await client.get(
                    "/api/v1/assets/search",
                    params={"q": query},
                )
        except httpx.TimeoutException as exc:
            raise self._upstream_exception(
                status.HTTP_504_GATEWAY_TIMEOUT,
                "Asset search timed out upstream.",
            ) from exc
        except httpx.HTTPError as exc:
            raise self._upstream_exception(
                status.HTTP_502_BAD_GATEWAY,
                "Asset search is unavailable right now.",
            ) from exc

        if response.status_code >= 400:
            raise self._upstream_exception(
                self._map_status_code(response.status_code),
                self._extract_message(response),
            )

        return AssetSearchResponse.model_validate(response.json())

    async def get_coin_news(self, query: str) -> CoinNewsSearchResponse:
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=15.0) as client:
                response = await client.get(
                    "/api/v1/news",
                    params={"query": query},
                )
        except httpx.TimeoutException as exc:
            raise self._upstream_exception(
                status.HTTP_504_GATEWAY_TIMEOUT,
                "Coin news timed out upstream.",
            ) from exc
        except httpx.HTTPError as exc:
            raise self._upstream_exception(
                status.HTTP_502_BAD_GATEWAY,
                "Coin news is unavailable right now.",
            ) from exc

        if response.status_code >= 400:
            raise self._upstream_exception(
                self._map_status_code(response.status_code),
                self._extract_message(
                    response,
                    default_message="Coin news is unavailable right now.",
                ),
            )

        return CoinNewsSearchResponse.model_validate(response.json())

    async def get_historical_prices(
        self,
        *,
        asset_ids: list[str],
        period: str,
    ) -> HistoricalPriceChartResponse:
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=20.0) as client:
                response = await client.get(
                    "/api/v1/price-charts",
                    params={"asset_ids": ",".join(asset_ids), "period": period},
                )
        except httpx.TimeoutException as exc:
            raise self._upstream_exception(
                status.HTTP_504_GATEWAY_TIMEOUT,
                "Historical price data timed out upstream.",
            ) from exc
        except httpx.HTTPError as exc:
            raise self._upstream_exception(
                status.HTTP_502_BAD_GATEWAY,
                "Historical price data is unavailable right now.",
            ) from exc

        if response.status_code >= 400:
            raise self._upstream_exception(
                self._map_status_code(response.status_code),
                self._extract_message(
                    response,
                    default_message="Historical price data is unavailable right now.",
                ),
            )

        try:
            return HistoricalPriceChartResponse.model_validate(response.json())
        except (ValueError, TypeError) as exc:
            raise self._upstream_exception(
                status.HTTP_502_BAD_GATEWAY,
                "Historical price data is unavailable right now.",
            ) from exc

    async def find_asset(
        self,
        *,
        asset_id: str,
        symbol: str,
        name: str,
    ) -> AssetSearchResultResponse | None:
        candidates = [asset_id.strip(), symbol.strip(), name.strip()]
        seen: set[str] = set()
        normalized_asset_id = asset_id.lower()

        for candidate in candidates:
            normalized_candidate = candidate.lower()
            if not candidate or normalized_candidate in seen:
                continue
            seen.add(normalized_candidate)

            matches = await self.search_assets(candidate)
            exact = next(
                (item for item in matches.items if item.asset_id.lower() == normalized_asset_id),
                None,
            )
            if exact is not None:
                return exact

        return None

    def _map_status_code(self, upstream_status_code: int) -> int:
        if upstream_status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return status.HTTP_429_TOO_MANY_REQUESTS
        if upstream_status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return status.HTTP_503_SERVICE_UNAVAILABLE
        return status.HTTP_502_BAD_GATEWAY

    def _extract_message(
        self,
        response: httpx.Response,
        default_message: str = "Market overview is unavailable right now.",
    ) -> str:
        try:
            payload = response.json()
        except ValueError:
            return default_message

        if isinstance(payload, dict):
            if isinstance(payload.get("message"), str) and payload["message"].strip():
                return payload["message"]

            error_payload = payload.get("error")
            if isinstance(error_payload, dict):
                detail = error_payload.get("detail")
                title = error_payload.get("title")
                if isinstance(detail, str) and detail.strip():
                    return detail
                if isinstance(title, str) and title.strip():
                    return title

        return default_message

    def _upstream_exception(self, status_code: int, message: str) -> UpstreamMarketDataError:
        return UpstreamMarketDataError(status_code=status_code, message=message)
