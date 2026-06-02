from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.features.auth.models import User
from app.features.notifications.repository import NotificationRepository
from app.features.notifications.schemas import NotificationListResponse, NotificationResponse


def get_notification_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> NotificationRepository:
    return NotificationRepository(session)


class NotificationService:
    def __init__(
        self,
        repository: Annotated[NotificationRepository, Depends(get_notification_repository)],
    ) -> None:
        self.repository = repository

    async def list_notifications(self, user: User) -> NotificationListResponse:
        notifications = await self.repository.list_notifications_for_user(user.id)
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(item) for item in notifications]
        )
