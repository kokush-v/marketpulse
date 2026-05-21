from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_market_overview_route_returns_public_payload() -> None:
    from app.features.market_data import service as market_data_service_module

    original = market_data_service_module.MarketDataService.get_market_overview

    async def fake_get_market_overview(self):
        return {
            "generated_at": "2026-05-21T12:00:00Z",
            "source": "market-data-api",
            "ranking_basis": "Top 10 crypto assets by market capitalization",
            "hero_asset_id": "bitcoin",
            "featured_assets": [
                {
                    "id": "bitcoin",
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "market_cap_rank": 1,
                    "current_price": 108250.12,
                    "price_change_24h": 1520.42,
                    "price_change_percentage_24h": 1.42,
                    "market_cap": 2150000000000.0,
                    "total_volume": 48250000000.0,
                    "high_24h": 109000.0,
                    "low_24h": 106800.0,
                    "image_url": "https://example.com/btc.png",
                    "homepage": "https://bitcoin.org",
                    "description": "Bitcoin is a decentralized digital asset.",
                    "categories": ["Smart Contract Platform"],
                    "chart": [
                        {"time": "2026-05-20T10:00:00Z", "price": 104500.0, "volume": 0.0},
                        {"time": "2026-05-21T10:00:00Z", "price": 108250.12, "volume": 0.0},
                    ],
                }
            ],
            "hero_chart": [
                {"time": "2026-05-20T10:00:00Z", "price": 104500.0, "volume": 0.0},
                {"time": "2026-05-21T10:00:00Z", "price": 108250.12, "volume": 0.0},
            ],
            "top_gainers": [
                {
                    "id": "bitcoin",
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "current_price": 108250.12,
                    "price_change_24h": 1520.42,
                    "price_change_percentage_24h": 1.42,
                    "market_cap_rank": 1,
                    "image_url": "https://example.com/btc.png",
                }
            ],
            "top_losers": [
                {
                    "id": "ethereum",
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "current_price": 4250.75,
                    "price_change_24h": -85.12,
                    "price_change_percentage_24h": -1.96,
                    "market_cap_rank": 2,
                    "image_url": "https://example.com/eth.png",
                }
            ],
        }

    market_data_service_module.MarketDataService.get_market_overview = fake_get_market_overview

    with TestClient(app) as client:
        response = client.get("/market-data/overview")

    market_data_service_module.MarketDataService.get_market_overview = original

    assert response.status_code == 200
    assert response.json()["ranking_basis"] == "Top 10 crypto assets by market capitalization"
    assert response.json()["hero_asset_id"] == "bitcoin"


def test_market_overview_route_maps_rate_limit_failure() -> None:
    from app.features.market_data import service as market_data_service_module

    original = market_data_service_module.MarketDataService.get_market_overview

    async def fake_get_market_overview(self):
        raise market_data_service_module.UpstreamMarketDataError(
            status_code=429,
            message="Crypto market data is temporarily busy.",
        )

    market_data_service_module.MarketDataService.get_market_overview = fake_get_market_overview

    with TestClient(app) as client:
        response = client.get("/market-data/overview")

    market_data_service_module.MarketDataService.get_market_overview = original

    assert response.status_code == 429
    assert response.json() == {"message": "Crypto market data is temporarily busy."}


def test_market_overview_route_maps_upstream_unavailable_failure() -> None:
    from app.features.market_data import service as market_data_service_module

    original = market_data_service_module.MarketDataService.get_market_overview

    async def fake_get_market_overview(self):
        raise market_data_service_module.UpstreamMarketDataError(
            status_code=503,
            message="Crypto market data service is unavailable.",
        )

    market_data_service_module.MarketDataService.get_market_overview = fake_get_market_overview

    with TestClient(app) as client:
        response = client.get("/market-data/overview")

    market_data_service_module.MarketDataService.get_market_overview = original

    assert response.status_code == 503
    assert response.json() == {"message": "Crypto market data service is unavailable."}
