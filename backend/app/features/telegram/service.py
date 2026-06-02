from __future__ import annotations

import asyncio
import hashlib
import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient

from app.core.config import settings
from app.db.session import AsyncSessionLocal, get_async_session
from app.features.auth.models import User
from app.features.auth.repository import AuthRepository
from app.features.auth.supabase_client import get_supabase_admin_client
from app.features.notifications.repository import NotificationRepository
from app.features.notifications.schemas import NotificationResponse
from app.features.notifications.service import get_notification_repository
from app.features.telegram.bot import TelegramBotApp, TelegramBotFlowService
from app.features.telegram.models import TelegramConnectionToken
from app.features.telegram.repository import TelegramRepository
from app.features.telegram.schemas import (
    TelegramBotProfile,
    TelegramBotResult,
    TelegramConnectionSummary,
    TelegramDisconnectResponse,
    TelegramIntegrationResponse,
    TelegramTestNotificationResponse,
)

logger = logging.getLogger("uvicorn.error")


def get_telegram_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> TelegramRepository:
    return TelegramRepository(session)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


TEST_NOTIFICATION_SUMMARY = "Telegram test notification"


@asynccontextmanager
async def _transaction_context(repository: object) -> AsyncIterator[None]:
    session = getattr(repository, "session", None)
    if session is None:
        yield
        return

    if session.in_transaction():
        try:
            yield
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
        return

    async with session.begin():
        yield


class TelegramServiceError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class TelegramService:
    def __init__(
        self,
        repository: Annotated[TelegramRepository, Depends(get_telegram_repository)],
        notification_repository: Annotated[
            NotificationRepository, Depends(get_notification_repository)
        ],
    ) -> None:
        self.repository = repository
        self.notification_repository = notification_repository

    @asynccontextmanager
    async def _transaction(self) -> AsyncIterator[None]:
        async with _transaction_context(self.repository):
            yield

    async def get_integration_state(self, user: User) -> TelegramIntegrationResponse:
        active_connection = await self.repository.get_active_connection_for_user(user.id)
        if active_connection is not None:
            return TelegramIntegrationResponse(
                state="connected",
                bot_username=settings.telegram_bot_username,
                connection=TelegramConnectionSummary(
                    telegram_username=active_connection.telegram_username,
                    connected_at=active_connection.connected_at,
                ),
            )

        return TelegramIntegrationResponse(
            state="not_connected",
            bot_username=settings.telegram_bot_username,
        )

    async def start_connection(self, user: User) -> TelegramIntegrationResponse:
        await self.repository.revoke_tokens_for_user(user.id)

        raw_token = secrets.token_urlsafe(24)
        expires_at = datetime.now(tz=UTC) + timedelta(
            seconds=settings.telegram_link_token_ttl_seconds
        )
        active_token = await self.repository.create_token(
            user_id=user.id,
            token_hash=_token_hash(raw_token),
            expires_at=expires_at,
        )
        return self._build_token_ready_response(active_token=active_token, raw_token=raw_token)

    async def disconnect(self, user: User) -> TelegramDisconnectResponse:
        await self.repository.deactivate_active_connection_for_user(user.id)
        await self.repository.revoke_tokens_for_user(user.id)
        return TelegramDisconnectResponse(success=True, state="not_connected")

    async def send_test_notification(self, user: User) -> TelegramTestNotificationResponse:
        bot_app = get_telegram_bot_app()
        async with self._transaction():
            active_connection = await self.repository.get_active_connection_for_user_for_update(
                user.id
            )
            if active_connection is None:
                raise TelegramServiceError(
                    status_code=409,
                    message="Connect Telegram before sending a test notification.",
                )

            latest_attempt = await self.notification_repository.get_latest_notification_for_user(
                user_id=user.id,
                channel="telegram",
                message_summary=TEST_NOTIFICATION_SUMMARY,
            )
            cooldown_seconds = settings.telegram_test_notification_cooldown_seconds
            cooldown_threshold = datetime.now(tz=UTC) - timedelta(seconds=cooldown_seconds)
            if latest_attempt is not None and latest_attempt.created_at > cooldown_threshold:
                raise TelegramServiceError(
                    status_code=429,
                    message=(
                        f"Wait {cooldown_seconds} seconds before sending another test notification."
                    ),
                )

            if active_connection.last_test_message_id is not None:
                try:
                    await bot_app.delete_message(
                        chat_id=active_connection.telegram_chat_id,
                        message_id=active_connection.last_test_message_id,
                    )
                except Exception:
                    logger.info(
                        "Telegram test message cleanup failed for user %s",
                        user.id,
                        exc_info=True,
                    )

            notification = await self.notification_repository.create_notification(
                user_id=user.id,
                notification_type="alert",
                channel="telegram",
                delivery_status="pending",
                message_summary=TEST_NOTIFICATION_SUMMARY,
                related_alert_id=None,
                commit=False,
            )
            try:
                message_id = await bot_app.send_message(
                    chat_id=active_connection.telegram_chat_id,
                    text=(
                        "MarketPulse test notification\n\n"
                        "Your Telegram connection is active and ready for alert delivery."
                    ),
                )
            except Exception as exc:
                await self.notification_repository.mark_failed(
                    notification,
                    safe_error_message="Telegram test notification failed.",
                    commit=False,
                )
                raise TelegramServiceError(
                    status_code=502,
                    message="Telegram test notification could not be delivered right now.",
                ) from exc

            await self.repository.update_last_test_message_id(
                active_connection,
                last_test_message_id=message_id,
                commit=False,
            )
            await self.notification_repository.mark_delivered(notification, commit=False)
        return TelegramTestNotificationResponse(
            success=True,
            message="Test notification sent to your linked Telegram chat.",
        )

    def _build_token_ready_response(
        self,
        *,
        active_token: TelegramConnectionToken,
        raw_token: str | None,
    ) -> TelegramIntegrationResponse:
        visible_token = raw_token or f"pending-{active_token.id}"
        return TelegramIntegrationResponse(
            state="token_ready",
            bot_username=settings.telegram_bot_username,
            deep_link=f"https://t.me/{settings.telegram_bot_username}?start={visible_token}",
            fallback_code=visible_token,
            expires_at=active_token.expires_at,
        )


class TelegramBotFlow(TelegramBotFlowService):
    def __init__(
        self,
        repository: TelegramRepository,
        auth_repository: AuthRepository,
        supabase_admin_client: AsyncClient,
    ) -> None:
        self.repository = repository
        self.auth_repository = auth_repository
        self.supabase_admin_client = supabase_admin_client

    async def consume_start_token(
        self,
        *,
        token: str,
        telegram_user_id: int,
        telegram_chat_id: int,
        telegram_username: str | None,
        confirmed_switch: bool,
    ) -> TelegramBotResult:
        now = datetime.now(tz=UTC)
        token_record = await self.repository.get_token_by_hash(_token_hash(token))
        if token_record is None:
            return TelegramBotResult(
                outcome="invalid",
                message=(
                    "This linking code is invalid. "
                    "Start a new Telegram connection from the web app."
                ),
            )

        if token_record.used_at is not None or token_record.revoked_at is not None:
            return TelegramBotResult(
                outcome="invalid",
                message=(
                    "This linking code is no longer active. "
                    "Start a new Telegram connection from the web app."
                ),
            )

        if token_record.expires_at <= now:
            return TelegramBotResult(
                outcome="expired",
                message=(
                    "This linking code expired. Start a new Telegram connection from the web app."
                ),
            )

        current_connection = await self.repository.get_active_connection_for_telegram_user(
            telegram_user_id
        )
        if current_connection is not None and current_connection.user_id != token_record.user_id:
            if not confirmed_switch:
                return TelegramBotResult(
                    outcome="switch_required",
                    message=(
                        "This Telegram account is already linked to another MarketPulse "
                        "account. Confirm if you want to switch it."
                    ),
                    requires_confirmation=True,
                )

        async with _transaction_context(self.repository):
            if (
                current_connection is not None
                and current_connection.user_id != token_record.user_id
            ):
                await self.repository.deactivate_connection(current_connection, commit=False)

            user_connection = await self.repository.get_active_connection_for_user(
                token_record.user_id
            )
            if user_connection is not None and user_connection.telegram_user_id == telegram_user_id:
                await self.repository.mark_token_used(token_record, commit=False)
                return TelegramBotResult(
                    outcome="already_linked",
                    message="This Telegram account is already linked to your MarketPulse account.",
                )

            if user_connection is not None:
                await self.repository.deactivate_connection(user_connection, commit=False)

            await self.repository.create_connection(
                user_id=token_record.user_id,
                telegram_user_id=telegram_user_id,
                telegram_chat_id=telegram_chat_id,
                telegram_username=telegram_username,
                commit=False,
            )
            await self.repository.mark_token_used(token_record, commit=False)
        return TelegramBotResult(
            outcome="switched" if confirmed_switch else "linked",
            message="Telegram is now linked to your MarketPulse account.",
        )

    async def cancel_switch(self, *, token: str) -> TelegramBotResult:
        token_record = await self.repository.get_token_by_hash(_token_hash(token))
        if (
            token_record is not None
            and token_record.used_at is None
            and token_record.revoked_at is None
        ):
            await self.repository.revoke_token(token_record)
        return TelegramBotResult(
            outcome="switch_cancelled",
            message="The current Telegram link was left unchanged.",
        )

    async def get_profile(
        self,
        *,
        telegram_user_id: int,
    ) -> tuple[TelegramBotResult, TelegramBotProfile | None]:
        connection = await self.repository.get_active_connection_for_telegram_user(telegram_user_id)
        if connection is None:
            return (
                TelegramBotResult(
                    outcome="not_linked",
                    message="This Telegram account is not linked to a MarketPulse profile.",
                ),
                None,
            )

        user = await self.auth_repository.get_user_by_id(connection.user_id)
        if user is None:
            logger.warning(
                "Linked Telegram profile lookup failed: local user %s is missing.",
                connection.user_id,
            )
            return (
                TelegramBotResult(
                    outcome="profile_unavailable",
                    message="The linked MarketPulse profile is temporarily unavailable.",
                ),
                None,
            )

        try:
            auth_user = await self.supabase_admin_client.auth.admin.get_user_by_id(
                str(user.supabase_user_id)
            )
        except Exception:
            logger.exception(
                "Supabase profile lookup failed for Telegram user %s.",
                telegram_user_id,
            )
            return (
                TelegramBotResult(
                    outcome="profile_unavailable",
                    message="The linked MarketPulse profile is temporarily unavailable.",
                ),
                None,
            )

        metadata = auth_user.user.user_metadata or {}
        display_name = (
            metadata.get("display_name") or metadata.get("full_name") or metadata.get("name")
        )
        if not isinstance(display_name, str) or not display_name.strip():
            logger.warning(
                "Supabase profile for user %s is missing a display name.",
                user.supabase_user_id,
            )
            return (
                TelegramBotResult(
                    outcome="profile_unavailable",
                    message="The linked MarketPulse profile is temporarily unavailable.",
                ),
                None,
            )

        avatar_url = metadata.get("avatar_url") or metadata.get("picture")
        if avatar_url is not None and not isinstance(avatar_url, str):
            avatar_url = None

        return (
            TelegramBotResult(
                outcome="profile_shown",
                message="Profile loaded.",
            ),
            TelegramBotProfile(
                avatar_url=avatar_url,
                email=user.email,
                display_name=display_name.strip(),
            ),
        )

    async def request_unlink(self, *, telegram_user_id: int) -> TelegramBotResult:
        connection = await self.repository.get_active_connection_for_telegram_user(telegram_user_id)
        if connection is None:
            return TelegramBotResult(
                outcome="not_linked",
                message="This Telegram account is not linked to a MarketPulse profile.",
            )
        return TelegramBotResult(
            outcome="unlink_confirmation_required",
            message="Unlink this Telegram account from your MarketPulse profile?",
            requires_confirmation=True,
        )

    async def confirm_unlink(self, *, telegram_user_id: int) -> TelegramBotResult:
        async with _transaction_context(self.repository):
            connection = await self.repository.get_active_connection_for_telegram_user_for_update(
                telegram_user_id
            )
            if connection is None:
                return TelegramBotResult(
                    outcome="not_linked",
                    message="This Telegram account is not linked to a MarketPulse profile.",
                )
            await self.repository.deactivate_connection(connection, commit=False)
            await self.repository.revoke_tokens_for_user(connection.user_id, commit=False)
        return TelegramBotResult(
            outcome="unlinked",
            message="Telegram was unlinked from your MarketPulse profile.",
        )

    async def cancel_unlink(self, *, telegram_user_id: int) -> TelegramBotResult:
        connection = await self.repository.get_active_connection_for_telegram_user(telegram_user_id)
        if connection is None:
            return TelegramBotResult(
                outcome="not_linked",
                message="This Telegram account is not linked to a MarketPulse profile.",
            )
        return TelegramBotResult(
            outcome="unlink_cancelled",
            message="The current Telegram link was left unchanged.",
        )


class TelegramDeliveryError(Exception):
    pass


class TelegramNotificationDispatcher:
    def __init__(
        self,
        telegram_repository: TelegramRepository,
        notification_repository: NotificationRepository,
        bot_app: TelegramBotApp,
    ) -> None:
        self.telegram_repository = telegram_repository
        self.notification_repository = notification_repository
        self.bot_app = bot_app

    def dispatch_alert_notification_in_background(
        self,
        *,
        alert_id: UUID,
        user_id: UUID,
        title: str,
        body: str,
    ) -> asyncio.Task[NotificationResponse | None]:
        task = asyncio.create_task(
            self.dispatch_alert_notification(
                alert_id=alert_id,
                user_id=user_id,
                title=title,
                body=body,
            )
        )
        task.add_done_callback(self._handle_background_task_result)
        return task

    async def dispatch_alert_notification(
        self,
        *,
        alert_id: UUID,
        user_id: UUID,
        title: str,
        body: str,
    ) -> NotificationResponse | None:
        connection = await self.telegram_repository.get_active_connection_for_user(user_id)
        if connection is None:
            return None

        notification = await self.notification_repository.create_notification(
            user_id=user_id,
            notification_type="alert",
            channel="telegram",
            delivery_status="pending",
            message_summary=title,
            related_alert_id=alert_id,
        )
        try:
            await self.bot_app.send_message(
                chat_id=connection.telegram_chat_id,
                text=f"{title}\n\n{body}",
            )
        except Exception:
            updated = await self.notification_repository.mark_failed(
                notification,
                safe_error_message="Telegram delivery failed.",
            )
            return NotificationResponse.model_validate(updated)

        updated = await self.notification_repository.mark_delivered(notification)
        return NotificationResponse.model_validate(updated)

    def _handle_background_task_result(
        self,
        task: asyncio.Task[NotificationResponse | None],
    ) -> None:
        try:
            task.result()
        except Exception:
            logger.exception("Telegram background notification dispatch failed unexpectedly.")


@asynccontextmanager
async def _build_bot_flow_service() -> AsyncIterator[TelegramBotFlow]:
    async with AsyncSessionLocal() as session:
        yield TelegramBotFlow(
            TelegramRepository(session),
            AuthRepository(session),
            await get_supabase_admin_client(),
        )


def get_telegram_bot_app() -> TelegramBotApp:
    return _get_cached_telegram_bot_app()


@lru_cache(maxsize=1)
def _get_cached_telegram_bot_app() -> TelegramBotApp:
    return TelegramBotApp(service_factory=_build_bot_flow_service)
