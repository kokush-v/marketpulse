from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.notifications.models import NotificationRecord


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_notifications_for_user(self, user_id: uuid.UUID) -> list[NotificationRecord]:
        stmt = (
            select(NotificationRecord)
            .where(NotificationRecord.user_id == user_id)
            .order_by(NotificationRecord.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_notification_for_user(
        self,
        *,
        user_id: uuid.UUID,
        channel: str,
        message_summary: str,
    ) -> NotificationRecord | None:
        stmt = (
            select(NotificationRecord)
            .where(
                NotificationRecord.user_id == user_id,
                NotificationRecord.channel == channel,
                NotificationRecord.message_summary == message_summary,
            )
            .order_by(NotificationRecord.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_notification(
        self,
        *,
        user_id: uuid.UUID,
        notification_type: str,
        channel: str,
        delivery_status: str,
        message_summary: str,
        related_alert_id: uuid.UUID | None,
        commit: bool = True,
    ) -> NotificationRecord:
        stmt = (
            insert(NotificationRecord)
            .values(
                user_id=user_id,
                notification_type=notification_type,
                channel=channel,
                delivery_status=delivery_status,
                message_summary=message_summary,
                related_alert_id=related_alert_id,
            )
            .returning(NotificationRecord)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()

    async def mark_delivered(
        self,
        notification: NotificationRecord,
        *,
        commit: bool = True,
    ) -> NotificationRecord:
        stmt = (
            update(NotificationRecord)
            .where(NotificationRecord.id == notification.id)
            .values(
                delivery_status="delivered",
                delivered_at=datetime.now(tz=UTC),
            )
            .returning(NotificationRecord)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()

    async def mark_failed(
        self,
        notification: NotificationRecord,
        *,
        safe_error_message: str,
        commit: bool = True,
    ) -> NotificationRecord:
        stmt = (
            update(NotificationRecord)
            .where(NotificationRecord.id == notification.id)
            .values(
                delivery_status="failed",
                safe_error_message=safe_error_message,
                failed_at=datetime.now(tz=UTC),
            )
            .returning(NotificationRecord)
        )
        result = await self.session.execute(stmt)
        if commit:
            await self.session.commit()
        return result.scalar_one()
