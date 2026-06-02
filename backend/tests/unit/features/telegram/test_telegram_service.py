from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.config import settings
from app.features.auth.models import User
from app.features.notifications.models import NotificationRecord
from app.features.telegram.models import TelegramConnection, TelegramConnectionToken
from app.features.telegram.service import (
    TelegramBotFlow,
    TelegramNotificationDispatcher,
    TelegramService,
)


def _make_user(email: str = "telegram@example.com") -> User:
    return User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email=email,
        created_at=datetime.now(tz=UTC),
    )


class FakeTelegramRepository:
    def __init__(self) -> None:
        self.active_user_connections: dict = {}
        self.active_telegram_connections: dict = {}
        self.tokens: dict[str, TelegramConnectionToken] = {}
        self.revoked_user_ids: list = []

    async def get_active_connection_for_user(self, user_id):
        return self.active_user_connections.get(user_id)

    async def get_active_connection_for_user_for_update(self, user_id):
        return self.active_user_connections.get(user_id)

    async def get_active_connection_for_telegram_user(self, telegram_user_id):
        return self.active_telegram_connections.get(telegram_user_id)

    async def revoke_tokens_for_user(self, user_id):
        self.revoked_user_ids.append(user_id)
        for token in self.tokens.values():
            if token.user_id == user_id and token.used_at is None:
                token.revoked_at = datetime.now(tz=UTC)

    async def create_token(self, *, user_id, token_hash, expires_at):
        token = TelegramConnectionToken(
            id=uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.now(tz=UTC),
            used_at=None,
            revoked_at=None,
        )
        self.tokens[token_hash] = token
        return token

    async def get_token_by_hash(self, token_hash):
        return self.tokens.get(token_hash)

    async def mark_token_used(self, token, *, commit=True):
        _ = commit
        token.used_at = datetime.now(tz=UTC)
        return token

    async def revoke_token(self, token, *, commit=True):
        _ = commit
        token.revoked_at = datetime.now(tz=UTC)
        return token

    async def deactivate_connection(self, connection, *, commit=True):
        _ = commit
        connection.status = "disconnected"
        connection.disconnected_at = datetime.now(tz=UTC)
        self.active_user_connections.pop(connection.user_id, None)
        self.active_telegram_connections.pop(connection.telegram_user_id, None)
        return connection

    async def deactivate_active_connection_for_user(self, user_id, *, commit=True):
        _ = commit
        connection = self.active_user_connections.get(user_id)
        if connection is not None:
            await self.deactivate_connection(connection)

    async def create_connection(
        self,
        *,
        user_id,
        telegram_user_id,
        telegram_chat_id,
        telegram_username,
        commit=True,
    ):
        _ = commit
        connection = TelegramConnection(
            id=uuid4(),
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
            telegram_username=telegram_username,
            status="active",
            connected_at=datetime.now(tz=UTC),
            disconnected_at=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        self.active_user_connections[user_id] = connection
        self.active_telegram_connections[telegram_user_id] = connection
        return connection


class FakeNotificationRepository:
    def __init__(self) -> None:
        self.notifications: list[NotificationRecord] = []

    async def get_latest_notification_for_user(self, *, user_id, channel, message_summary):
        matching = [
            notification
            for notification in self.notifications
            if notification.user_id == user_id
            and notification.channel == channel
            and notification.message_summary == message_summary
        ]
        if not matching:
            return None
        return max(matching, key=lambda notification: notification.created_at)

    async def create_notification(
        self,
        *,
        user_id,
        notification_type,
        channel,
        delivery_status,
        message_summary,
        related_alert_id,
        commit=True,
    ):
        _ = commit
        notification = NotificationRecord(
            id=uuid4(),
            user_id=user_id,
            related_alert_id=related_alert_id,
            notification_type=notification_type,
            channel=channel,
            delivery_status=delivery_status,
            message_summary=message_summary,
            safe_error_message=None,
            delivered_at=None,
            failed_at=None,
            created_at=datetime.now(tz=UTC),
        )
        self.notifications.append(notification)
        return notification

    async def mark_delivered(self, notification, *, commit=True):
        _ = commit
        notification.delivery_status = "delivered"
        notification.delivered_at = datetime.now(tz=UTC)
        return notification

    async def mark_failed(self, notification, *, safe_error_message, commit=True):
        _ = commit
        notification.delivery_status = "failed"
        notification.safe_error_message = safe_error_message
        notification.failed_at = datetime.now(tz=UTC)
        return notification


class FakeBotApp:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, *, chat_id: int, text: str) -> None:
        if self.should_fail:
            raise RuntimeError("telegram failed")
        self.messages.append((chat_id, text))


@pytest.mark.asyncio
async def test_start_connection_returns_token_ready_state(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    service = TelegramService(
        repository=repository,
        notification_repository=FakeNotificationRepository(),
    )
    monkeypatch.setattr(
        "app.features.telegram.service.secrets.token_urlsafe",
        lambda _n: "raw-link-token",
    )

    response = await service.start_connection(user)

    assert response.state == "token_ready"
    assert response.fallback_code == "raw-link-token"
    assert response.deep_link == (
        f"https://t.me/{settings.telegram_bot_username}?start=raw-link-token"
    )
    assert repository.revoked_user_ids == [user.id]
    saved_token = next(iter(repository.tokens.values()))
    assert saved_token.token_hash != "raw-link-token"


@pytest.mark.asyncio
async def test_disconnect_returns_safe_noop_state() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    service = TelegramService(
        repository=repository,
        notification_repository=FakeNotificationRepository(),
    )

    response = await service.disconnect(user)

    assert response.success is True
    assert response.state == "not_connected"
    assert repository.revoked_user_ids == [user.id]


@pytest.mark.asyncio
async def test_bot_flow_requires_confirmation_for_cross_account() -> None:
    current_user = _make_user("current@example.com")
    target_user = _make_user("target@example.com")
    repository = FakeTelegramRepository()
    await repository.create_connection(
        user_id=current_user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="current_user",
    )
    token = await repository.create_token(
        user_id=target_user.id,
        token_hash="hashed-token",
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=10),
    )
    repository.tokens = {"hashed-token": token}

    flow = TelegramBotFlow(repository)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.features.telegram.service._token_hash",
            lambda _token: "hashed-token",
        )
        result = await flow.consume_start_token(
            token="raw",
            telegram_user_id=321,
            telegram_chat_id=654,
            telegram_username="next_user",
            confirmed_switch=False,
        )

    assert result.outcome == "switch_required"
    assert result.requires_confirmation is True


@pytest.mark.asyncio
async def test_bot_flow_switches_account_after_confirmation() -> None:
    current_user = _make_user("current@example.com")
    target_user = _make_user("target@example.com")
    repository = FakeTelegramRepository()
    await repository.create_connection(
        user_id=current_user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="current_user",
    )
    token = await repository.create_token(
        user_id=target_user.id,
        token_hash="hashed-token",
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=10),
    )
    repository.tokens = {"hashed-token": token}

    flow = TelegramBotFlow(repository)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.features.telegram.service._token_hash",
            lambda _token: "hashed-token",
        )
        result = await flow.consume_start_token(
            token="raw",
            telegram_user_id=321,
            telegram_chat_id=654,
            telegram_username="next_user",
            confirmed_switch=True,
        )

    assert result.outcome == "switched"
    assert repository.active_user_connections[target_user.id].telegram_username == "next_user"
    assert repository.active_telegram_connections[321].user_id == target_user.id
    assert token.used_at is not None


@pytest.mark.asyncio
async def test_notification_dispatch_records_failure_safely() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    notifications = FakeNotificationRepository()
    bot_app = FakeBotApp(should_fail=True)
    connection = await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    _ = connection
    dispatcher = TelegramNotificationDispatcher(repository, notifications, bot_app)

    response = await dispatcher.dispatch_alert_notification(
        alert_id=uuid4(),
        user_id=user.id,
        title="BTC alert",
        body="Bitcoin moved above your threshold.",
    )

    assert response is not None
    assert response.delivery_status == "failed"
    assert response.safe_error_message == "Telegram delivery failed."


@pytest.mark.asyncio
async def test_send_test_notification_requires_active_connection() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    service = TelegramService(
        repository=repository,
        notification_repository=FakeNotificationRepository(),
    )

    with pytest.raises(Exception) as exc_info:
        await service.send_test_notification(user)

    error = exc_info.value
    assert error.status_code == 409
    assert error.message == "Connect Telegram before sending a test notification."


@pytest.mark.asyncio
async def test_send_test_notification_delivers_message() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    notifications = FakeNotificationRepository()
    bot_app = FakeBotApp()
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    service = TelegramService(
        repository=repository,
        notification_repository=notifications,
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.features.telegram.service.get_telegram_bot_app",
            lambda: bot_app,
        )
        response = await service.send_test_notification(user)

    assert response.success is True
    assert response.message == "Test notification sent to your linked Telegram chat."
    assert bot_app.messages == [
        (
            654,
            "MarketPulse test notification\n\n"
            "Your Telegram connection is active and ready for alert delivery.",
        )
    ]
    assert notifications.notifications[-1].delivery_status == "delivered"
    assert notifications.notifications[-1].message_summary == "Telegram test notification"


@pytest.mark.asyncio
async def test_send_test_notification_enforces_cooldown() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    notifications = FakeNotificationRepository()
    bot_app = FakeBotApp()
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    notifications.notifications.append(
        NotificationRecord(
            id=uuid4(),
            user_id=user.id,
            related_alert_id=None,
            notification_type="alert",
            channel="telegram",
            delivery_status="delivered",
            message_summary="Telegram test notification",
            safe_error_message=None,
            delivered_at=datetime.now(tz=UTC),
            failed_at=None,
            created_at=datetime.now(tz=UTC),
        )
    )
    service = TelegramService(
        repository=repository,
        notification_repository=notifications,
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.features.telegram.service.get_telegram_bot_app",
            lambda: bot_app,
        )
        with pytest.raises(Exception) as exc_info:
            await service.send_test_notification(user)

    error = exc_info.value
    assert error.status_code == 429
    assert error.message == (
        "Wait "
        f"{settings.telegram_test_notification_cooldown_seconds} seconds before sending "
        "another test notification."
    )
    assert bot_app.messages == []


@pytest.mark.asyncio
async def test_send_test_notification_records_safe_failure() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    notifications = FakeNotificationRepository()
    bot_app = FakeBotApp(should_fail=True)
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    service = TelegramService(
        repository=repository,
        notification_repository=notifications,
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.features.telegram.service.get_telegram_bot_app",
            lambda: bot_app,
        )
        with pytest.raises(Exception) as exc_info:
            await service.send_test_notification(user)

    error = exc_info.value
    assert error.status_code == 502
    assert error.message == "Telegram test notification could not be delivered right now."
    assert notifications.notifications[-1].delivery_status == "failed"
    assert notifications.notifications[-1].safe_error_message == (
        "Telegram test notification failed."
    )
