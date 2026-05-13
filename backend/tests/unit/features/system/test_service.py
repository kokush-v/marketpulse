from unittest.mock import MagicMock

from app.features.system.service import SystemService


def test_get_health_returns_expected_payload() -> None:
    service = SystemService()

    result = service.get_health()

    assert result.status == "ok"
    assert result.service == "marketpulse-backend"


def test_service_method_can_be_mocked_for_callers() -> None:
    service = SystemService()
    service.get_health = MagicMock(return_value=service.get_health())

    result = service.get_health()

    service.get_health.assert_called_once_with()
    assert result.status == "ok"
