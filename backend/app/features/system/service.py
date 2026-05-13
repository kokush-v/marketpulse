from app.features.system.schemas import HealthResponse


class SystemService:
    def get_health(self) -> HealthResponse:
        return HealthResponse(status="ok", service="marketpulse-backend")
