from __future__ import annotations

import httpx
import pytest

from app.features.market_data.service import MarketDataService, UpstreamMarketDataError


class StubResponse:
    def __init__(
        self, status_code: int, payload: dict[str, object] | None = None
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, object]:
        return self._payload


class StubAsyncClient:
    def __init__(
        self,
        response: StubResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error

    async def __aenter__(self) -> StubAsyncClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, path: str) -> StubResponse:
        assert path == "/api/v1/market-overview"
        if self._error:
            raise self._error
        assert self._response is not None
        return self._response


@pytest.mark.asyncio
async def test_market_data_service_returns_validated_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "generated_at": "2026-05-21T12:00:00Z",
        "source": "market-data-api",
        "ranking_basis": "Top 10 crypto assets by market capitalization",
        "hero_asset_id": "bitcoin",
        "featured_assets": [],
        "hero_chart": [],
        "top_gainers": [],
        "top_losers": [],
    }

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            response=StubResponse(status_code=200, payload=payload)
        ),
    )

    service = MarketDataService(base_url="http://localhost:3001")
    result = await service.get_market_overview()

    assert result.source == "market-data-api"
    assert result.ranking_basis == "Top 10 crypto assets by market capitalization"


@pytest.mark.asyncio
async def test_market_data_service_maps_rate_limited_upstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            response=StubResponse(
                status_code=429,
                payload={
                    "error": {"detail": "Crypto market data is temporarily busy."}
                },
            )
        ),
    )

    service = MarketDataService(base_url="http://localhost:3001")

    with pytest.raises(UpstreamMarketDataError) as exc_info:
        await service.get_market_overview()

    assert exc_info.value.status_code == 429
    assert exc_info.value.message == "Crypto market data is temporarily busy."


@pytest.mark.asyncio
async def test_market_data_service_maps_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = httpx.Request("GET", "http://localhost:3001/api/v1/market-overview")

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            error=httpx.ReadTimeout("Timed out", request=request)
        ),
    )

    service = MarketDataService(base_url="http://localhost:3001")

    with pytest.raises(UpstreamMarketDataError) as exc_info:
        await service.get_market_overview()

    assert exc_info.value.status_code == 504
    assert exc_info.value.message == "Market overview timed out upstream."
