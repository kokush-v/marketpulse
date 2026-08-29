from __future__ import annotations

import httpx
import pytest

from app.features.market_data.service import MarketDataService, UpstreamMarketDataError


class StubResponse:
    def __init__(self, status_code: int, payload: dict[str, object] | None = None) -> None:
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

    async def get(self, path: str, params: dict[str, str] | None = None) -> StubResponse:
        if self._error:
            raise self._error
        assert self._response is not None
        if path == "/api/v1/assets/search":
            assert params is not None
            assert "q" in params
        elif path == "/api/v1/news":
            assert params is not None
            assert "query" in params
        elif path == "/api/v1/price-charts":
            assert params == {"asset_ids": "bitcoin", "period": "7d"}
        else:
            assert path == "/api/v1/market-overview"
        return self._response


@pytest.mark.asyncio
async def test_market_data_service_returns_validated_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "generated_at": "2026-05-21T12:00:00Z",
        "source": "market-data-api",
        "ranking_basis": "Top 25 crypto assets by market capitalization",
        "hero_asset_id": "bitcoin",
        "featured_assets": [],
        "hero_chart": [],
        "top_gainers": [],
        "top_losers": [],
    }

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(response=StubResponse(status_code=200, payload=payload)),
    )

    service = MarketDataService(base_url="http://localhost:3001")
    result = await service.get_market_overview()

    assert result.source == "market-data-api"
    assert result.ranking_basis == "Top 25 crypto assets by market capitalization"


@pytest.mark.asyncio
async def test_market_data_service_returns_asset_search_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "items": [
            {
                "asset_id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "market_cap_rank": 1,
                "current_price": 108250.12,
                "price_change_percentage_24h": 1.42,
                "image_url": "https://example.com/btc.png",
            }
        ]
    }

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(response=StubResponse(status_code=200, payload=payload)),
    )

    service = MarketDataService(base_url="http://localhost:3001")
    result = await service.search_assets("btc")

    assert result.items[0].asset_id == "bitcoin"
    assert result.items[0].symbol == "BTC"


@pytest.mark.asyncio
async def test_market_data_service_returns_normalized_historical_prices(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "period": "7d",
        "series": [
            {
                "asset_id": "bitcoin",
                "points": [{"time": "2026-08-29T00:00:00Z", "price": 101_000.0}],
            }
        ],
    }
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(response=StubResponse(status_code=200, payload=payload)),
    )

    result = await MarketDataService(base_url="http://localhost:3001").get_historical_prices(
        asset_ids=["bitcoin"],
        period="7d",
    )

    assert result.period == "7d"
    assert result.series[0].points[0].price == 101_000.0


@pytest.mark.asyncio
async def test_find_asset_requires_exact_asset_id_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "items": [
            {
                "asset_id": "wrapped-bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "market_cap_rank": 15,
                "current_price": 108250.12,
                "price_change_percentage_24h": 1.42,
                "image_url": "https://example.com/wbtc.png",
            },
            {
                "asset_id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "market_cap_rank": 1,
                "current_price": 108250.12,
                "price_change_percentage_24h": 1.42,
                "image_url": "https://example.com/btc.png",
            },
        ]
    }

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(response=StubResponse(status_code=200, payload=payload)),
    )

    service = MarketDataService(base_url="http://localhost:3001")
    result = await service.find_asset(asset_id="bitcoin", symbol="BTC", name="Bitcoin")

    assert result is not None
    assert result.asset_id == "bitcoin"


@pytest.mark.asyncio
async def test_find_asset_returns_none_for_symbol_name_collision_without_asset_id_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "items": [
            {
                "asset_id": "wrapped-bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "market_cap_rank": 15,
                "current_price": 108250.12,
                "price_change_percentage_24h": 1.42,
                "image_url": "https://example.com/wbtc.png",
            }
        ]
    }

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(response=StubResponse(status_code=200, payload=payload)),
    )

    service = MarketDataService(base_url="http://localhost:3001")
    result = await service.find_asset(asset_id="bitcoin", symbol="BTC", name="Bitcoin")

    assert result is None


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
                payload={"error": {"detail": "Crypto market data is temporarily busy."}},
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
        lambda **kwargs: StubAsyncClient(error=httpx.ReadTimeout("Timed out", request=request)),
    )

    service = MarketDataService(base_url="http://localhost:3001")

    with pytest.raises(UpstreamMarketDataError) as exc_info:
        await service.get_market_overview()

    assert exc_info.value.status_code == 504
    assert exc_info.value.message == "Market overview timed out upstream."


@pytest.mark.asyncio
async def test_market_data_service_returns_coin_news_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "articles": [
            {
                "title": "Bitcoin reclaims momentum",
                "summary": "Spot demand improved during the session.",
                "url": "https://example.com/news/bitcoin",
                "image_url": "https://example.com/news/bitcoin.png",
                "published_at": "2026-05-25T09:30:00Z",
                "source": "NewsAPI",
            }
        ]
    }

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(response=StubResponse(status_code=200, payload=payload)),
    )

    service = MarketDataService(base_url="http://localhost:3001")
    result = await service.get_coin_news("bitcoin")

    assert result.articles[0].title == "Bitcoin reclaims momentum"
    assert result.articles[0].source == "NewsAPI"
    assert result.articles[0].image_url == "https://example.com/news/bitcoin.png"


@pytest.mark.asyncio
async def test_market_data_service_maps_coin_news_rate_limited_upstream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: StubAsyncClient(
            response=StubResponse(
                status_code=429,
                payload={"error": {"detail": "Coin news provider is rate limited."}},
            )
        ),
    )

    service = MarketDataService(base_url="http://localhost:3001")

    with pytest.raises(UpstreamMarketDataError) as exc_info:
        await service.get_coin_news("bitcoin")

    assert exc_info.value.status_code == 429
    assert exc_info.value.message == "Coin news provider is rate limited."
