from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
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


def _make_shared_fake_session() -> SimpleNamespace:
    async def _commit_noop() -> None:
        return None

    return SimpleNamespace(commit=_commit_noop)


class FakeTelegramRepository:
    def __init__(self, session: SimpleNamespace | None = None) -> None:
        self.session = session or _make_shared_fake_session()
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

    async def revoke_tokens_for_user(self, user_id, *, commit=True):
        _ = commit
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
            last_test_message_id=None,
            status="active",
            connected_at=datetime.now(tz=UTC),
            disconnected_at=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        self.active_user_connections[user_id] = connection
        self.active_telegram_connections[telegram_user_id] = connection
        return connection

    async def get_active_connection_for_telegram_user_for_update(self, telegram_user_id):
        return self.active_telegram_connections.get(telegram_user_id)

    async def update_last_test_message_id(self, connection, *, last_test_message_id, commit=True):
        _ = commit
        connection.last_test_message_id = last_test_message_id
        return connection


class FakeTransactionalSession:
    def __init__(self, on_commit) -> None:
        self._in_transaction = False
        self.begin_calls = 0
        self.commit_calls = 0
        self._on_commit = on_commit

    def in_transaction(self) -> bool:
        return self._in_transaction

    def autobegin(self) -> None:
        self._in_transaction = True

    def begin(self):
        session = self

        class _BeginContext:
            async def __aenter__(self_inner):
                session.begin_calls += 1
                session._in_transaction = True
                return None

            async def __aexit__(self_inner, exc_type, exc, tb):
                if exc_type is None:
                    session._on_commit()
                session._in_transaction = False
                return False

        return _BeginContext()

    async def commit(self) -> None:
        self.commit_calls += 1
        self._on_commit()
        self._in_transaction = False


class FakeTransactionalTelegramRepository(FakeTelegramRepository):
    def __init__(self, session: FakeTransactionalSession | None = None) -> None:
        super().__init__()
        self.session = session or FakeTransactionalSession(self.finalize_transaction)
        self._staged_connection_args = None
        self._staged_last_test_message_ids: dict = {}

    async def get_active_connection_for_user(self, user_id):
        self.session.autobegin()
        return await super().get_active_connection_for_user(user_id)

    async def get_active_connection_for_user_for_update(self, user_id):
        self.session.autobegin()
        return await super().get_active_connection_for_user_for_update(user_id)

    async def get_active_connection_for_telegram_user(self, telegram_user_id):
        self.session.autobegin()
        return await super().get_active_connection_for_telegram_user(telegram_user_id)

    async def get_token_by_hash(self, token_hash):
        self.session.autobegin()
        return await super().get_token_by_hash(token_hash)

    async def create_connection(
        self,
        *,
        user_id,
        telegram_user_id,
        telegram_chat_id,
        telegram_username,
        commit=True,
    ):
        if commit:
            return await super().create_connection(
                user_id=user_id,
                telegram_user_id=telegram_user_id,
                telegram_chat_id=telegram_chat_id,
                telegram_username=telegram_username,
                commit=commit,
            )

        self._staged_connection_args = {
            "user_id": user_id,
            "telegram_user_id": telegram_user_id,
            "telegram_chat_id": telegram_chat_id,
            "telegram_username": telegram_username,
        }
        return TelegramConnection(
            id=uuid4(),
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
            telegram_username=telegram_username,
            last_test_message_id=None,
            status="active",
            connected_at=datetime.now(tz=UTC),
            disconnected_at=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

    def finalize_transaction(self) -> None:
        if self._staged_connection_args is None:
            for connection_id, last_test_message_id in self._staged_last_test_message_ids.items():
                for connection in self.active_user_connections.values():
                    if connection.id == connection_id:
                        connection.last_test_message_id = last_test_message_id
            self._staged_last_test_message_ids = {}
            return
        connection = TelegramConnection(
            id=uuid4(),
            user_id=self._staged_connection_args["user_id"],
            telegram_user_id=self._staged_connection_args["telegram_user_id"],
            telegram_chat_id=self._staged_connection_args["telegram_chat_id"],
            telegram_username=self._staged_connection_args["telegram_username"],
            last_test_message_id=None,
            status="active",
            connected_at=datetime.now(tz=UTC),
            disconnected_at=None,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        self.active_user_connections[connection.user_id] = connection
        self.active_telegram_connections[connection.telegram_user_id] = connection
        self._staged_connection_args = None
        for connection_id, last_test_message_id in self._staged_last_test_message_ids.items():
            if connection.id == connection_id:
                connection.last_test_message_id = last_test_message_id
        self._staged_last_test_message_ids = {}

    async def update_last_test_message_id(self, connection, *, last_test_message_id, commit=True):
        if commit:
            return await super().update_last_test_message_id(
                connection,
                last_test_message_id=last_test_message_id,
                commit=commit,
            )

        self._staged_last_test_message_ids[connection.id] = last_test_message_id
        return connection


class FakeAuthRepository:
    def __init__(self) -> None:
        self.users: dict = {}

    async def get_user_by_id(self, user_id):
        return self.users.get(user_id)


class FakeNotificationRepository:
    def __init__(self, session: SimpleNamespace | None = None) -> None:
        self.session = session or _make_shared_fake_session()
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
        event_key=None,
        event_timestamp=None,
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
            event_key=event_key,
            event_timestamp=event_timestamp,
            safe_error_message=None,
            delivered_at=None,
            failed_at=None,
            created_at=datetime.now(tz=UTC),
        )
        self.notifications.append(notification)
        return notification

    async def get_notification_by_event_key(self, event_key):
        for notification in self.notifications:
            if notification.event_key == event_key:
                return notification
        return None

    async def create_or_get_notification(
        self,
        *,
        user_id,
        notification_type,
        channel,
        delivery_status,
        message_summary,
        related_alert_id,
        event_key,
        event_timestamp,
        commit=True,
    ):
        _ = commit
        existing = await self.get_notification_by_event_key(event_key)
        if existing is not None:
            return existing, False
        created = await self.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            delivery_status=delivery_status,
            message_summary=message_summary,
            related_alert_id=related_alert_id,
            event_key=event_key,
            event_timestamp=event_timestamp,
            commit=commit,
        )
        return created, True

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


class FakeTransactionalNotificationRepository(FakeNotificationRepository):
    def __init__(self, session: FakeTransactionalSession) -> None:
        super().__init__()
        self.session = session
        self._staged_notifications: list[NotificationRecord] = []

    async def get_latest_notification_for_user(self, *, user_id, channel, message_summary):
        self.session.autobegin()
        return await super().get_latest_notification_for_user(
            user_id=user_id,
            channel=channel,
            message_summary=message_summary,
        )

    async def create_notification(
        self,
        *,
        user_id,
        notification_type,
        channel,
        delivery_status,
        message_summary,
        related_alert_id,
        event_key=None,
        event_timestamp=None,
        commit=True,
    ):
        if commit:
            return await super().create_notification(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                delivery_status=delivery_status,
                message_summary=message_summary,
                related_alert_id=related_alert_id,
                event_key=event_key,
                event_timestamp=event_timestamp,
                commit=commit,
            )

        notification = NotificationRecord(
            id=uuid4(),
            user_id=user_id,
            related_alert_id=related_alert_id,
            notification_type=notification_type,
            channel=channel,
            delivery_status=delivery_status,
            message_summary=message_summary,
            event_key=event_key,
            event_timestamp=event_timestamp,
            safe_error_message=None,
            delivered_at=None,
            failed_at=None,
            created_at=datetime.now(tz=UTC),
        )
        self._staged_notifications.append(notification)
        return notification

    def finalize_transaction(self) -> None:
        self.notifications.extend(self._staged_notifications)
        self._staged_notifications = []


class FakeBotApp:
    def __init__(self, should_fail: bool = False, delete_should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.delete_should_fail = delete_should_fail
        self.messages: list[tuple[int, str]] = []
        self.deleted_messages: list[tuple[int, int]] = []
        self.next_message_id = 100

    async def send_message(self, *, chat_id: int, text: str) -> int:
        if self.should_fail:
            raise RuntimeError("telegram failed")
        self.messages.append((chat_id, text))
        self.next_message_id += 1
        return self.next_message_id

    async def delete_message(self, *, chat_id: int, message_id: int) -> None:
        if self.delete_should_fail:
            raise RuntimeError("delete failed")
        self.deleted_messages.append((chat_id, message_id))


class FakeSupabaseAdminClient:
    def __init__(
        self,
        *,
        display_name: str = "MarketPulse User",
        avatar_url: str | None = None,
        user_exists: bool = True,
    ):
        self._display_name = display_name
        self._avatar_url = avatar_url
        self._user_exists = user_exists
        self.auth = SimpleNamespace(admin=self)

    async def get_user_by_id(self, _uid: str):
        if not self._user_exists:
            return SimpleNamespace(user=None)
        return SimpleNamespace(
            user=SimpleNamespace(
                user_metadata={
                    "full_name": self._display_name,
                    "avatar_url": self._avatar_url,
                }
            )
        )


@pytest.mark.asyncio
async def test_start_connection_returns_token_ready_state(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _make_user()
    shared_session = _make_shared_fake_session()
    repository = FakeTelegramRepository(shared_session)
    service = TelegramService(
        repository=repository,
        notification_repository=FakeNotificationRepository(shared_session),
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
    shared_session = _make_shared_fake_session()
    repository = FakeTelegramRepository(shared_session)
    service = TelegramService(
        repository=repository,
        notification_repository=FakeNotificationRepository(shared_session),
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

    flow = TelegramBotFlow(
        repository,
        FakeAuthRepository(),
        FakeSupabaseAdminClient(),
    )

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

    flow = TelegramBotFlow(
        repository,
        FakeAuthRepository(),
        FakeSupabaseAdminClient(),
    )

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
async def test_bot_flow_persists_link_for_follow_up_profile_lookup() -> None:
    user = _make_user()
    repository = FakeTransactionalTelegramRepository()
    auth_repository = FakeAuthRepository()
    auth_repository.users[user.id] = user
    token = await repository.create_token(
        user_id=user.id,
        token_hash="hashed-token",
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=10),
    )
    repository.tokens = {"hashed-token": token}
    flow = TelegramBotFlow(
        repository,
        auth_repository,
        FakeSupabaseAdminClient(display_name="Persisted User"),
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.features.telegram.service._token_hash",
            lambda _token: "hashed-token",
        )
        result = await flow.consume_start_token(
            token="raw",
            telegram_user_id=321,
            telegram_chat_id=654,
            telegram_username="persisted_user",
            confirmed_switch=False,
        )

    follow_up_result, profile = await flow.get_profile(telegram_user_id=321)

    assert result.outcome == "linked"
    assert repository.session.commit_calls == 1
    assert follow_up_result.outcome == "profile_shown"
    assert profile is not None
    assert profile.display_name == "Persisted User"


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
async def test_scheduled_notification_dispatch_records_internal_history_without_telegram_link() -> (
    None
):
    user = _make_user()
    repository = FakeTelegramRepository()
    notifications = FakeNotificationRepository()
    dispatcher = TelegramNotificationDispatcher(repository, notifications, FakeBotApp())

    response = await dispatcher.dispatch_scheduled_alert_notification(
        alert_id=uuid4(),
        user_id=user.id,
        title="BTC alert triggered",
        body="Bitcoin moved above your threshold.",
        event_key="alert:test:one-time",
        event_timestamp=datetime.now(tz=UTC),
    )

    assert response.channel == "internal"
    assert response.delivery_status == "recorded"
    assert notifications.notifications[-1].channel == "internal"


@pytest.mark.asyncio
async def test_scheduled_notification_dispatch_is_idempotent_for_duplicate_event_keys() -> None:
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
    dispatcher = TelegramNotificationDispatcher(repository, notifications, bot_app)

    first = await dispatcher.dispatch_scheduled_alert_notification(
        alert_id=uuid4(),
        user_id=user.id,
        title="BTC alert triggered",
        body="Bitcoin moved above your threshold.",
        event_key="alert:test:daily:2026-06-04",
        event_timestamp=datetime.now(tz=UTC),
    )
    second = await dispatcher.dispatch_scheduled_alert_notification(
        alert_id=uuid4(),
        user_id=user.id,
        title="BTC alert triggered",
        body="Bitcoin moved above your threshold.",
        event_key="alert:test:daily:2026-06-04",
        event_timestamp=datetime.now(tz=UTC),
    )

    assert first.id == second.id
    assert len(bot_app.messages) == 1
    assert len(notifications.notifications) == 1


@pytest.mark.asyncio
async def test_send_test_notification_requires_active_connection() -> None:
    user = _make_user()
    shared_session = _make_shared_fake_session()
    repository = FakeTelegramRepository(shared_session)
    service = TelegramService(
        repository=repository,
        notification_repository=FakeNotificationRepository(shared_session),
    )

    with pytest.raises(Exception) as exc_info:
        await service.send_test_notification(user)

    error = exc_info.value
    assert error.status_code == 409
    assert error.message == "Connect Telegram before sending a test notification."


@pytest.mark.asyncio
async def test_send_test_notification_delivers_message() -> None:
    user = _make_user()
    shared_session = _make_shared_fake_session()
    repository = FakeTelegramRepository(shared_session)
    notifications = FakeNotificationRepository(shared_session)
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
    assert repository.active_user_connections[user.id].last_test_message_id == 101


@pytest.mark.asyncio
async def test_send_test_notification_persists_tracking_with_existing_transaction() -> None:
    user = _make_user()
    session = FakeTransactionalSession(lambda: None)
    repository = FakeTransactionalTelegramRepository(session)
    notifications = FakeTransactionalNotificationRepository(session)
    session._on_commit = lambda: (
        repository.finalize_transaction(),
        notifications.finalize_transaction(),
    )
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
    session.autobegin()

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "app.features.telegram.service.get_telegram_bot_app",
            lambda: bot_app,
        )
        response = await service.send_test_notification(user)
        begin_calls_after_first_send = session.begin_calls
        commit_calls_after_first_send = session.commit_calls

        with pytest.raises(Exception) as exc_info:
            await service.send_test_notification(user)

    assert response.success is True
    assert begin_calls_after_first_send == 0
    assert commit_calls_after_first_send == 1
    assert repository.active_user_connections[user.id].last_test_message_id == 101
    assert notifications.notifications[-1].delivery_status == "delivered"
    error = exc_info.value
    assert error.status_code == 429


@pytest.mark.asyncio
async def test_send_test_notification_replaces_previous_message_when_possible() -> None:
    user = _make_user()
    shared_session = _make_shared_fake_session()
    repository = FakeTelegramRepository(shared_session)
    notifications = FakeNotificationRepository(shared_session)
    bot_app = FakeBotApp()
    connection = await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    connection.last_test_message_id = 77
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
    assert bot_app.deleted_messages == [(654, 77)]
    assert repository.active_user_connections[user.id].last_test_message_id == 101


@pytest.mark.asyncio
async def test_send_test_notification_still_sends_when_cleanup_fails() -> None:
    user = _make_user()
    shared_session = _make_shared_fake_session()
    repository = FakeTelegramRepository(shared_session)
    notifications = FakeNotificationRepository(shared_session)
    bot_app = FakeBotApp(delete_should_fail=True)
    connection = await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    connection.last_test_message_id = 77
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
    assert bot_app.messages
    assert repository.active_user_connections[user.id].last_test_message_id == 101


@pytest.mark.asyncio
async def test_send_test_notification_enforces_cooldown() -> None:
    user = _make_user()
    shared_session = _make_shared_fake_session()
    repository = FakeTelegramRepository(shared_session)
    notifications = FakeNotificationRepository(shared_session)
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
    shared_session = _make_shared_fake_session()
    repository = FakeTelegramRepository(shared_session)
    notifications = FakeNotificationRepository(shared_session)
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


@pytest.mark.asyncio
async def test_bot_flow_returns_linked_profile() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    auth_repository = FakeAuthRepository()
    auth_repository.users[user.id] = user
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    flow = TelegramBotFlow(
        repository,
        auth_repository,
        FakeSupabaseAdminClient(
            display_name="Vitalii Lohoida",
            avatar_url="https://example.com/avatar.png",
        ),
    )

    result, profile = await flow.get_profile(telegram_user_id=321)

    assert result.outcome == "profile_shown"
    assert profile is not None
    assert profile.display_name == "Vitalii Lohoida"
    assert profile.email == user.email
    assert profile.avatar_url == "https://example.com/avatar.png"


@pytest.mark.asyncio
async def test_bot_flow_returns_safe_profile_outcome_when_not_linked() -> None:
    flow = TelegramBotFlow(
        FakeTelegramRepository(),
        FakeAuthRepository(),
        FakeSupabaseAdminClient(),
    )

    result, profile = await flow.get_profile(telegram_user_id=321)

    assert result.outcome == "not_linked"
    assert profile is None


@pytest.mark.asyncio
async def test_bot_flow_returns_safe_profile_outcome_when_supabase_user_missing() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    auth_repository = FakeAuthRepository()
    auth_repository.users[user.id] = user
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    flow = TelegramBotFlow(
        repository,
        auth_repository,
        FakeSupabaseAdminClient(user_exists=False),
    )

    result, profile = await flow.get_profile(telegram_user_id=321)

    assert result.outcome == "profile_unavailable"
    assert profile is None


@pytest.mark.asyncio
async def test_bot_flow_returns_safe_profile_outcome_when_admin_client_unavailable() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    auth_repository = FakeAuthRepository()
    auth_repository.users[user.id] = user
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )

    async def _raise_runtime_error():
        raise RuntimeError("SUPABASE_SECRET_KEY is not configured.")

    flow = TelegramBotFlow(
        repository,
        auth_repository,
        supabase_admin_client_factory=_raise_runtime_error,
    )

    result, profile = await flow.get_profile(telegram_user_id=321)

    assert result.outcome == "profile_unavailable"
    assert profile is None


@pytest.mark.asyncio
async def test_bot_flow_unlink_requires_confirmation() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    flow = TelegramBotFlow(
        repository,
        FakeAuthRepository(),
        FakeSupabaseAdminClient(),
    )

    result = await flow.request_unlink(telegram_user_id=321)

    assert result.outcome == "unlink_confirmation_required"
    assert result.requires_confirmation is True


@pytest.mark.asyncio
async def test_bot_flow_unlink_does_not_require_supabase_admin_client() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )

    async def _unexpected_admin_client_call():
        raise AssertionError("Supabase admin client should not be requested.")

    flow = TelegramBotFlow(
        repository,
        FakeAuthRepository(),
        supabase_admin_client_factory=_unexpected_admin_client_call,
    )

    result = await flow.request_unlink(telegram_user_id=321)

    assert result.outcome == "unlink_confirmation_required"


@pytest.mark.asyncio
async def test_bot_flow_confirm_unlink_deactivates_connection() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    flow = TelegramBotFlow(
        repository,
        FakeAuthRepository(),
        FakeSupabaseAdminClient(),
    )

    result = await flow.confirm_unlink(telegram_user_id=321)

    assert result.outcome == "unlinked"
    assert user.id not in repository.active_user_connections
    assert 321 not in repository.active_telegram_connections


@pytest.mark.asyncio
async def test_bot_flow_cancel_unlink_preserves_connection() -> None:
    user = _make_user()
    repository = FakeTelegramRepository()
    await repository.create_connection(
        user_id=user.id,
        telegram_user_id=321,
        telegram_chat_id=654,
        telegram_username="user_name",
    )
    flow = TelegramBotFlow(
        repository,
        FakeAuthRepository(),
        FakeSupabaseAdminClient(),
    )

    result = await flow.cancel_unlink(telegram_user_id=321)

    assert result.outcome == "unlink_cancelled"
    assert repository.active_telegram_connections[321].user_id == user.id
