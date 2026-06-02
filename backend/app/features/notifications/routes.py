from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.notifications.schemas import NotificationListResponse
from app.features.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])
current_user_dependency = Depends(get_current_user)


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List the authenticated user's notifications",
)
async def list_notifications(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[NotificationService, Depends()],
) -> NotificationListResponse:
    return await service.list_notifications(current_user)
