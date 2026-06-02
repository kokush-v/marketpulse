from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.telegram.models import TelegramConnection, TelegramConnectionToken


class TelegramRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_connection_for_user(self, user_id: uuid.UUID) -> TelegramConnection | None:
        stmt = select(TelegramConnection).where(
            TelegramConnection.user_id == user_id,
            TelegramConnection.status == "active",
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_connection_for_user_for_update(
        self, user_id: uuid.UUID
    ) -> TelegramConnection | None:
        stmt = (
            select(TelegramConnection)
            .where(
                TelegramConnection.user_id == user_id,
                TelegramConnection.status == "active",
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_connection_for_telegram_user(
        self, telegram_user_id: int
    ) -> TelegramConnection | None:
        stmt = select(TelegramConnection).where(
            TelegramConnection.telegram_user_id == telegram_user_id,
            TelegramConnection.status == "active",
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_connection_for_telegram_user_for_update(
        self, telegram_user_id: int
    ) -> TelegramConnection | None:
        stmt = (
            select(TelegramConnection)
            .where(
                TelegramConnection.telegram_user_id == telegram_user_id,
                TelegramConnection.status == "active",
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_valid_token_for_user(
        self, user_id: uuid.UUID, now: datetime
    ) -> TelegramConnectionToken | None:
        stmt = (
            select(TelegramConnectionToken)
            .where(
                TelegramConnectionToken.user_id == user_id,
                TelegramConnectionToken.used_at.is_(None),
                TelegramConnectionToken.revoked_at.is_(None),
                TelegramConnectionToken.expires_at > now,
            )
            .order_by(TelegramConnectionToken.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_token_by_hash(self, token_hash: str) -> TelegramConnectionToken | None:
        stmt = select(TelegramConnectionToken).where(
            TelegramConnectionToken.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        commit: bool = True,
    ) -> TelegramConnectionToken:
        stmt = (
            insert(TelegramConnectionToken)
            .values(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            .returning(TelegramConnectionToken)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()

    async def revoke_tokens_for_user(self, user_id: uuid.UUID, *, commit: bool = True) -> None:
        now = datetime.now(tz=UTC)
        stmt = (
            update(TelegramConnectionToken)
            .where(
                TelegramConnectionToken.user_id == user_id,
                TelegramConnectionToken.used_at.is_(None),
                TelegramConnectionToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await self.session.execute(stmt)
        if commit:
            await self.session.commit()

    async def mark_token_used(
        self,
        token: TelegramConnectionToken,
        *,
        commit: bool = True,
    ) -> TelegramConnectionToken:
        stmt = (
            update(TelegramConnectionToken)
            .where(TelegramConnectionToken.id == token.id)
            .values(used_at=datetime.now(tz=UTC))
            .returning(TelegramConnectionToken)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()

    async def create_connection(
        self,
        *,
        user_id: uuid.UUID,
        telegram_user_id: int,
        telegram_chat_id: int,
        telegram_username: str | None,
        commit: bool = True,
    ) -> TelegramConnection:
        stmt = (
            insert(TelegramConnection)
            .values(
                user_id=user_id,
                telegram_user_id=telegram_user_id,
                telegram_chat_id=telegram_chat_id,
                telegram_username=telegram_username,
                last_test_message_id=None,
            )
            .returning(TelegramConnection)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()

    async def deactivate_connection(
        self,
        connection: TelegramConnection,
        *,
        commit: bool = True,
    ) -> TelegramConnection:
        now = datetime.now(tz=UTC)
        stmt = (
            update(TelegramConnection)
            .where(TelegramConnection.id == connection.id)
            .values(status="disconnected", disconnected_at=now)
            .returning(TelegramConnection)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()

    async def deactivate_active_connection_for_user(
        self,
        user_id: uuid.UUID,
        *,
        commit: bool = True,
    ) -> None:
        connection = await self.get_active_connection_for_user(user_id)
        if connection is None:
            return
        await self.deactivate_connection(connection, commit=commit)

    async def deactivate_active_connection_for_telegram_user(self, telegram_user_id: int) -> None:
        connection = await self.get_active_connection_for_telegram_user(telegram_user_id)
        if connection is None:
            return
        await self.deactivate_connection(connection)

    async def update_last_test_message_id(
        self,
        connection: TelegramConnection,
        *,
        last_test_message_id: int | None,
        commit: bool = True,
    ) -> TelegramConnection:
        stmt = (
            update(TelegramConnection)
            .where(TelegramConnection.id == connection.id)
            .values(last_test_message_id=last_test_message_id)
            .returning(TelegramConnection)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()

    async def has_active_connection_conflict(
        self,
        *,
        telegram_user_id: int,
        target_user_id: uuid.UUID,
    ) -> bool:
        stmt = select(TelegramConnection.id).where(
            TelegramConnection.telegram_user_id == telegram_user_id,
            TelegramConnection.status == "active",
            TelegramConnection.user_id != target_user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_active_connections_for_user_ids(
        self, user_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, TelegramConnection]:
        if not user_ids:
            return {}

        stmt = select(TelegramConnection).where(
            TelegramConnection.user_id.in_(user_ids),
            TelegramConnection.status == "active",
        )
        result = await self.session.execute(stmt)
        return {connection.user_id: connection for connection in result.scalars().all()}

    async def revoke_token(
        self,
        token: TelegramConnectionToken,
        *,
        commit: bool = True,
    ) -> TelegramConnectionToken:
        stmt = (
            update(TelegramConnectionToken)
            .where(TelegramConnectionToken.id == token.id)
            .values(revoked_at=datetime.now(tz=UTC))
            .returning(TelegramConnectionToken)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()

    def token_is_currently_valid(self, token: TelegramConnectionToken, now: datetime) -> bool:
        return token.used_at is None and token.revoked_at is None and token.expires_at > now
