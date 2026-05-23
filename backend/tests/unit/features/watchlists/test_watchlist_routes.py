from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_async_session
from app.features.auth.models import User
from app.main import app


def _make_user() -> User:
    return User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="watcher@example.com",
        created_at=datetime.now(tz=UTC),
    )


def test_watchlist_route_requires_access_token() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    with TestClient(app) as client:
        response = client.get("/watchlists/starred")
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing access token"


def test_watchlist_route_returns_authenticated_user_assets() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    from app.features.auth import dependencies as auth_dependencies
    from app.features.watchlists import service as watchlist_service_module

    original_decode = auth_dependencies._decode_access_token
    original_get_watchlist = watchlist_service_module.WatchlistService.get_watchlist

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_watchlist(self, user):
        assert user.id == fake_user.id
        return {
            "assets": [
                {
                    "id": str(uuid4()),
                    "asset_id": "bitcoin",
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "image_url": "https://example.com/btc.png",
                    "created_at": "2026-05-22T10:00:00Z",
                }
            ]
        }

    async def fake_get_authenticated_user(self, supabase_user_id):
        assert supabase_user_id == fake_user.supabase_user_id
        return fake_user

    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    watchlist_service_module.WatchlistService.get_watchlist = fake_get_watchlist

    with TestClient(app) as client:
        response = client.get("/watchlists/starred", headers={"Authorization": "Bearer valid"})

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    watchlist_service_module.WatchlistService.get_watchlist = original_get_watchlist
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["assets"][0]["asset_id"] == "bitcoin"


def test_add_watchlist_asset_route_maps_duplicate_error() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    from app.features.auth import dependencies as auth_dependencies
    from app.features.watchlists import service as watchlist_service_module
    from app.features.watchlists.service import WatchlistServiceError

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_add_asset = watchlist_service_module.WatchlistService.add_asset

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_add_asset(self, user, payload):
        assert user.id == fake_user.id
        assert payload.asset_id == "bitcoin"
        raise WatchlistServiceError(status_code=409, message="Asset is already saved")

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    watchlist_service_module.WatchlistService.add_asset = fake_add_asset

    with TestClient(app) as client:
        response = client.post(
            "/watchlists/starred/assets",
            headers={"Authorization": "Bearer valid"},
            json={
                "asset_id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "image_url": "https://example.com/btc.png",
            },
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    watchlist_service_module.WatchlistService.add_asset = original_add_asset
    app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["message"] == "Asset is already saved"


def test_watchlist_context_route_returns_selected_asset_payload() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    from app.features.auth import dependencies as auth_dependencies
    from app.features.watchlists import service as watchlist_service_module

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_get_asset_context = watchlist_service_module.WatchlistService.get_asset_context

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_get_asset_context(self, user, asset_id):
        assert user.id == fake_user.id
        assert asset_id == "bitcoin"
        return {
            "summary": {
                "asset_id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "market_cap_rank": 1,
                "current_price": 100000.0,
                "price_change_24h": 1000.0,
                "price_change_percentage_24h": 1.0,
                "market_cap": 2_000_000_000_000.0,
                "total_volume": 50_000_000_000.0,
                "high_24h": 101000.0,
                "low_24h": 99000.0,
                "image_url": "https://example.com/btc.png",
                "homepage": "https://bitcoin.org",
                "description": "Bitcoin info",
                "categories": ["Store of Value"],
            },
            "chart": [
                {"time": "2026-05-21T10:00:00Z", "price": 99000.0, "volume": 0.0},
                {"time": "2026-05-22T10:00:00Z", "price": 100000.0, "volume": 0.0},
            ],
            "related_news": [
                {
                    "title": "Bitcoin climbs on ETF momentum",
                    "summary": "Spot demand remains firm through the session.",
                    "url": "https://example.com/bitcoin/news",
                    "published_at": "2026-05-22T09:00:00Z",
                    "source": "CoinGecko",
                }
            ],
        }

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    watchlist_service_module.WatchlistService.get_asset_context = fake_get_asset_context

    with TestClient(app) as client:
        response = client.get(
            "/watchlists/starred/assets/bitcoin/context",
            headers={"Authorization": "Bearer valid"},
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    watchlist_service_module.WatchlistService.get_asset_context = original_get_asset_context
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["summary"]["asset_id"] == "bitcoin"
    assert response.json()["related_news"][0]["source"] == "CoinGecko"
