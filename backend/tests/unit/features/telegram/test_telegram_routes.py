from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import get_async_session
from app.features.auth import dependencies as auth_dependencies
from app.features.auth.models import User
from app.features.notifications import service as notifications_service_module
from app.features.telegram import service as telegram_service_module
from app.main import app


def _make_user() -> User:
    return User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="telegram@example.com",
        created_at=datetime.now(tz=UTC),
    )


def test_telegram_routes_require_access_token() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    with TestClient(app) as client:
        response = client.get("/integrations/telegram")
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing access token"


def test_telegram_connect_route_returns_token_ready_state() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_start_connection = telegram_service_module.TelegramService.start_connection

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        assert supabase_user_id == fake_user.supabase_user_id
        return fake_user

    async def fake_start_connection(self, user):
        assert user.id == fake_user.id
        return {
            "state": "token_ready",
            "bot_username": "marketpulse_bot",
            "deep_link": "https://t.me/marketpulse_bot?start=abc",
            "fallback_code": "abc",
            "expires_at": "2026-05-29T09:30:00Z",
            "connection": None,
        }

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    telegram_service_module.TelegramService.start_connection = fake_start_connection

    with TestClient(app) as client:
        response = client.post(
            "/integrations/telegram/connect",
            headers={"Authorization": "Bearer valid"},
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    telegram_service_module.TelegramService.start_connection = original_start_connection
    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["state"] == "token_ready"
    assert response.json()["fallback_code"] == "abc"


def test_notifications_route_returns_authenticated_user_records() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_list_notifications = (
        notifications_service_module.NotificationService.list_notifications
    )

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_list_notifications(self, user):
        assert user.id == fake_user.id
        return {
            "items": [
                {
                    "id": str(uuid4()),
                    "related_alert_id": str(uuid4()),
                    "notification_type": "alert",
                    "channel": "telegram",
                    "delivery_status": "delivered",
                    "message_summary": "BTC alert",
                    "safe_error_message": None,
                    "delivered_at": "2026-05-29T09:30:00Z",
                    "failed_at": None,
                    "created_at": "2026-05-29T09:29:00Z",
                }
            ]
        }

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    notifications_service_module.NotificationService.list_notifications = fake_list_notifications

    with TestClient(app) as client:
        response = client.get("/notifications", headers={"Authorization": "Bearer valid"})

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    notifications_service_module.NotificationService.list_notifications = (
        original_list_notifications
    )
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["channel"] == "telegram"


def test_telegram_test_notification_route_returns_success() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_send_test_notification = telegram_service_module.TelegramService.send_test_notification

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_send_test_notification(self, user):
        assert user.id == fake_user.id
        return {
            "success": True,
            "message": "Test notification sent to your linked Telegram chat.",
        }

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    telegram_service_module.TelegramService.send_test_notification = fake_send_test_notification

    with TestClient(app) as client:
        response = client.post(
            "/integrations/telegram/test-notification",
            headers={"Authorization": "Bearer valid"},
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    telegram_service_module.TelegramService.send_test_notification = original_send_test_notification
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_telegram_test_notification_route_returns_rate_limit_error() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_send_test_notification = telegram_service_module.TelegramService.send_test_notification

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_send_test_notification(self, user):
        assert user.id == fake_user.id
        raise telegram_service_module.TelegramServiceError(
            status_code=429,
            message="Wait 10 seconds before sending another test notification.",
        )

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    telegram_service_module.TelegramService.send_test_notification = fake_send_test_notification

    with TestClient(app) as client:
        response = client.post(
            "/integrations/telegram/test-notification",
            headers={"Authorization": "Bearer valid"},
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    telegram_service_module.TelegramService.send_test_notification = original_send_test_notification
    app.dependency_overrides.clear()

    assert response.status_code == 429
    assert response.json() == {
        "message": "Wait 10 seconds before sending another test notification.",
        "state": "error",
    }
