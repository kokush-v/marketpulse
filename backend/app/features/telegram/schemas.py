from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

TelegramIntegrationState = Literal["not_connected", "token_ready", "connected", "error"]
TelegramBotOutcome = Literal[
    "linked",
    "already_linked",
    "switch_required",
    "switched",
    "switch_cancelled",
    "invalid",
    "expired",
]


class TelegramConnectionSummary(BaseModel):
    telegram_username: str | None = None
    connected_at: datetime


class TelegramIntegrationResponse(BaseModel):
    state: TelegramIntegrationState
    bot_username: str
    deep_link: str | None = None
    fallback_code: str | None = None
    expires_at: datetime | None = None
    connection: TelegramConnectionSummary | None = None


class TelegramDisconnectResponse(BaseModel):
    success: bool
    state: TelegramIntegrationState


class TelegramTestNotificationResponse(BaseModel):
    success: bool
    message: str


class TelegramErrorResponse(BaseModel):
    message: str
    state: TelegramIntegrationState = "error"


class TelegramBotResult(BaseModel):
    outcome: TelegramBotOutcome
    message: str
    requires_confirmation: bool = False
