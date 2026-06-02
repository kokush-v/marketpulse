from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Response, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User
from app.features.telegram.schemas import (
    TelegramDisconnectResponse,
    TelegramErrorResponse,
    TelegramIntegrationResponse,
    TelegramTestNotificationResponse,
)
from app.features.telegram.service import (
    TelegramService,
    TelegramServiceError,
    get_telegram_bot_app,
)

router = APIRouter(tags=["telegram"])
current_user_dependency = Depends(get_current_user)


def _service_error_response(error: TelegramServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=TelegramErrorResponse(message=error.message).model_dump(),
    )


@router.get(
    "/integrations/telegram",
    response_model=TelegramIntegrationResponse,
    summary="Read the authenticated user's Telegram integration state",
)
async def get_telegram_integration_state(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[TelegramService, Depends()],
) -> TelegramIntegrationResponse:
    try:
        return await service.get_integration_state(current_user)
    except TelegramServiceError as error:
        return _service_error_response(error)


@router.post(
    "/integrations/telegram/connect",
    response_model=TelegramIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a Telegram connection flow for the authenticated user",
)
async def start_telegram_connection(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[TelegramService, Depends()],
) -> TelegramIntegrationResponse:
    try:
        return await service.start_connection(current_user)
    except TelegramServiceError as error:
        return _service_error_response(error)


@router.delete(
    "/integrations/telegram",
    response_model=TelegramDisconnectResponse,
    summary="Disconnect the authenticated user's Telegram account",
)
async def disconnect_telegram(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[TelegramService, Depends()],
) -> TelegramDisconnectResponse:
    try:
        return await service.disconnect(current_user)
    except TelegramServiceError as error:
        return _service_error_response(error)


@router.post(
    "/integrations/telegram/test-notification",
    response_model=TelegramTestNotificationResponse,
    summary="Send a test Telegram notification to the authenticated user",
)
async def send_telegram_test_notification(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[TelegramService, Depends()],
) -> TelegramTestNotificationResponse:
    try:
        return await service.send_test_notification(current_user)
    except TelegramServiceError as error:
        return _service_error_response(error)


@router.post(
    "/telegram/webhook",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Handle Telegram bot webhook events",
)
async def telegram_webhook(
    payload: dict[str, Any],
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
) -> Response:
    if (
        settings.telegram_webhook_secret
        and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret
    ):
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    bot_app = get_telegram_bot_app()
    await bot_app.handle_update(payload)
    return Response(status_code=status.HTTP_202_ACCEPTED)
