from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

NotificationChannel = Literal["telegram"]
NotificationDeliveryStatus = Literal["pending", "delivered", "failed"]
NotificationType = Literal["alert"]


class NotificationResponse(BaseModel):
    id: UUID
    related_alert_id: UUID | None = None
    notification_type: NotificationType
    channel: NotificationChannel
    delivery_status: NotificationDeliveryStatus
    message_summary: str
    safe_error_message: str | None = None
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
