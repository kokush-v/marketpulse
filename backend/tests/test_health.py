from fastapi.testclient import TestClient

from app.api import health
from app.main import app


def test_health_check_reports_service_and_database_status(monkeypatch):
    monkeypatch.setattr(health, "check_database_connection", lambda: True)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": {"status": "ok"},
        "database": {"status": "ok"},
    }


def test_health_check_handles_database_failure_without_leaking_secrets(monkeypatch):
    monkeypatch.setattr(health, "check_database_connection", lambda: False)

    response = TestClient(app).get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body == {
        "status": "unhealthy",
        "service": {"status": "ok"},
        "database": {"status": "unavailable"},
    }
    assert "postgresql" not in response.text
    assert "marketpulse" not in response.text

