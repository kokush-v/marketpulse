from fastapi import APIRouter

from app.features.system.schemas import HealthResponse
from app.features.system.service import SystemService

router = APIRouter(prefix="/health", tags=["system"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    service = SystemService()
    return service.get_health()
