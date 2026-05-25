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
        email="reader@example.com",
        created_at=datetime.now(tz=UTC),
    )


def test_news_route_requires_access_token() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    with TestClient(app) as client:
        response = client.get("/news", params={"query": "bitcoin"})
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing access token"


def test_news_route_returns_coin_name_results() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    from app.features.auth import dependencies as auth_dependencies
    from app.features.news import service as news_service_module

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_search_coin_news = news_service_module.NewsService.search_coin_news

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        assert supabase_user_id == fake_user.supabase_user_id
        return fake_user

    async def fake_search_coin_news(self, query: str):
        assert query == "bitcoin"
        return {
            "query": "bitcoin",
            "articles": [
                {
                    "title": "Bitcoin reclaims momentum",
                    "summary": "Spot demand improved during the morning session.",
                    "url": "https://example.com/news/bitcoin",
                    "image_url": "https://example.com/news/bitcoin.png",
                    "published_at": "2026-05-25T09:30:00Z",
                    "source": "NewsAPI",
                }
            ],
        }

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    news_service_module.NewsService.search_coin_news = fake_search_coin_news

    with TestClient(app) as client:
        response = client.get(
            "/news",
            params={"query": "bitcoin"},
            headers={"Authorization": "Bearer valid"},
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    news_service_module.NewsService.search_coin_news = original_search_coin_news
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["query"] == "bitcoin"
    assert response.json()["articles"][0]["source"] == "NewsAPI"
    assert response.json()["articles"][0]["image_url"] == "https://example.com/news/bitcoin.png"


def test_news_route_returns_symbol_results() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    from app.features.auth import dependencies as auth_dependencies
    from app.features.news import service as news_service_module

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_search_coin_news = news_service_module.NewsService.search_coin_news

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_search_coin_news(self, query: str):
        assert query == "BTC"
        return {"query": "BTC", "articles": []}

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    news_service_module.NewsService.search_coin_news = fake_search_coin_news

    with TestClient(app) as client:
        response = client.get(
            "/news",
            params={"query": "BTC"},
            headers={"Authorization": "Bearer valid"},
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    news_service_module.NewsService.search_coin_news = original_search_coin_news
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"query": "BTC", "articles": []}


def test_news_route_returns_validation_error_when_query_missing() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    from app.features.auth import dependencies as auth_dependencies

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user

    with TestClient(app) as client:
        response = client.get("/news", headers={"Authorization": "Bearer valid"})

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_news_route_maps_upstream_failure() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    from app.features.auth import dependencies as auth_dependencies
    from app.features.market_data.service import UpstreamMarketDataError
    from app.features.news import service as news_service_module

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_search_coin_news = news_service_module.NewsService.search_coin_news

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_search_coin_news(self, query: str):
        raise UpstreamMarketDataError(
            status_code=429,
            message="Coin news provider is rate limited.",
        )

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    news_service_module.NewsService.search_coin_news = fake_search_coin_news

    with TestClient(app) as client:
        response = client.get(
            "/news",
            params={"query": "bitcoin"},
            headers={"Authorization": "Bearer valid"},
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    news_service_module.NewsService.search_coin_news = original_search_coin_news
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert response.json() == {"message": "Coin news provider is rate limited."}
