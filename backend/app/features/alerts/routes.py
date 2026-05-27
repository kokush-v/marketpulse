from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.features.alerts.schemas import (
    AlertErrorResponse,
    AlertListResponse,
    AlertOperationResponse,
    AlertResponse,
    CreateAlertRequest,
    UpdateAlertRequest,
)
from app.features.alerts.service import AlertService, AlertServiceError
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User

router = APIRouter(prefix="/alerts", tags=["alerts"])
current_user_dependency = Depends(get_current_user)


def _service_error_response(error: AlertServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=AlertErrorResponse(message=error.message).model_dump(),
    )


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List the authenticated user's alerts",
)
async def list_alerts(
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AlertService, Depends()],
) -> AlertListResponse:
    try:
        return await service.list_alerts(current_user)
    except AlertServiceError as error:
        return _service_error_response(error)


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": AlertErrorResponse, "description": "Invalid alert payload"}},
    summary="Create a personal alert",
)
async def create_alert(
    payload: CreateAlertRequest,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AlertService, Depends()],
) -> AlertResponse:
    try:
        return await service.create_alert(current_user, payload)
    except AlertServiceError as error:
        return _service_error_response(error)


@router.put(
    "/{alert_id}",
    response_model=AlertResponse,
    responses={
        404: {"model": AlertErrorResponse, "description": "Alert not found"},
        422: {"model": AlertErrorResponse, "description": "Invalid alert payload"},
    },
    summary="Update a personal alert",
)
async def update_alert(
    alert_id: UUID,
    payload: UpdateAlertRequest,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AlertService, Depends()],
) -> AlertResponse:
    try:
        return await service.update_alert(current_user, alert_id, payload)
    except AlertServiceError as error:
        return _service_error_response(error)


@router.post(
    "/{alert_id}/pause",
    response_model=AlertResponse,
    responses={404: {"model": AlertErrorResponse, "description": "Alert not found"}},
    summary="Pause a personal alert",
)
async def pause_alert(
    alert_id: UUID,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AlertService, Depends()],
) -> AlertResponse:
    try:
        return await service.pause_alert(current_user, alert_id)
    except AlertServiceError as error:
        return _service_error_response(error)


@router.post(
    "/{alert_id}/resume",
    response_model=AlertResponse,
    responses={404: {"model": AlertErrorResponse, "description": "Alert not found"}},
    summary="Resume a personal alert",
)
async def resume_alert(
    alert_id: UUID,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AlertService, Depends()],
) -> AlertResponse:
    try:
        return await service.resume_alert(current_user, alert_id)
    except AlertServiceError as error:
        return _service_error_response(error)


@router.delete(
    "/{alert_id}",
    response_model=AlertOperationResponse,
    responses={404: {"model": AlertErrorResponse, "description": "Alert not found"}},
    summary="Delete a personal alert",
)
async def delete_alert(
    alert_id: UUID,
    current_user: Annotated[User, current_user_dependency],
    service: Annotated[AlertService, Depends()],
) -> AlertOperationResponse:
    try:
        return await service.delete_alert(current_user, alert_id)
    except AlertServiceError as error:
        return _service_error_response(error)
