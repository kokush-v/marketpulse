from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db.session import check_database_connection

router = APIRouter(tags=["health"])


class ComponentHealth(BaseModel):
    status: Literal["ok", "unavailable"]


class HealthResponse(BaseModel):
    status: Literal["ok", "unhealthy"]
    service: ComponentHealth
    database: ComponentHealth


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
def health_check() -> HealthResponse | JSONResponse:
    database_available = check_database_connection()
    payload = HealthResponse(
        status="ok" if database_available else "unhealthy",
        service=ComponentHealth(status="ok"),
        database=ComponentHealth(status="ok" if database_available else "unavailable"),
    )

    if database_available:
        return payload

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload.model_dump(),
    )

