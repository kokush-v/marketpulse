from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_async_session
from app.features.alerts import service as alerts_service_module
from app.features.alerts.service import AlertServiceError
from app.features.auth import dependencies as auth_dependencies
from app.features.auth.models import User
from app.main import app


def _make_user() -> User:
    return User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="alerts@example.com",
        created_at=datetime.now(tz=UTC),
    )


def _alert_payload() -> dict[str, object]:
    return {
        "asset_id": "bitcoin",
        "symbol": "BTC",
        "name": "Bitcoin",
        "image_url": "https://example.com/asset.png",
        "scenario": "price_above",
        "time_behavior": "one_time",
        "trigger_mode": "percent",
        "threshold_value": 15,
    }


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("get", "/alerts", None),
        ("post", "/alerts", _alert_payload()),
        ("put", f"/alerts/{uuid4()}", _alert_payload()),
        ("post", f"/alerts/{uuid4()}/pause", None),
        ("post", f"/alerts/{uuid4()}/resume", None),
        ("delete", f"/alerts/{uuid4()}", None),
    ],
)
def test_alert_routes_require_access_token(
    method: str,
    path: str,
    json_body: dict[str, object] | None,
) -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    with TestClient(app) as client:
        response = client.request(method.upper(), path, json=json_body)
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing access token"


def test_list_alerts_route_returns_authenticated_user_alerts() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_list_alerts = alerts_service_module.AlertService.list_alerts

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        assert supabase_user_id == fake_user.supabase_user_id
        return fake_user

    async def fake_list_alerts(self, user, **filters):
        assert user.id == fake_user.id
        assert filters == {"status_filter": None, "scenario": None, "query": None}
        return {
            "counts": {"all": 1, "active": 1, "paused": 0},
            "items": [
                {
                    "id": str(uuid4()),
                    "asset_id": "bitcoin",
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "image_url": "https://example.com/asset.png",
                    "status": "active",
                    "scenario": "price_above",
                    "time_behavior": "one_time",
                    "recurring_start_date": None,
                    "recurring_end_date": None,
                    "trigger_mode": "currency",
                    "threshold_value": 100000.0,
                    "baseline_price": None,
                    "rule_summary": "Price above $100,000.00",
                    "time_summary": "One-time alert",
                    "available_actions": ["edit", "pause", "delete"],
                    "created_at": "2026-05-26T08:00:00Z",
                    "updated_at": "2026-05-26T08:00:00Z",
                }
            ],
        }

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    alerts_service_module.AlertService.list_alerts = fake_list_alerts

    with TestClient(app) as client:
        response = client.get("/alerts", headers={"Authorization": "Bearer valid"})

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    alerts_service_module.AlertService.list_alerts = original_list_alerts
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"][0]["asset_id"] == "bitcoin"
    assert response.json()["items"][0]["scenario"] == "price_above"
    assert response.json()["counts"] == {"all": 1, "active": 1, "paused": 0}


def _call_list_alerts_route(query_string: str):
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()
    received: dict[str, object] = {}

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_list_alerts = alerts_service_module.AlertService.list_alerts

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_list_alerts(self, user, **filters):
        received.update(filters)
        return {"items": [], "counts": {"all": 0, "active": 0, "paused": 0}}

    auth_dependencies._decode_access_token = lambda _token: {
        "sub": str(fake_user.supabase_user_id),
        "email": fake_user.email,
        "exp": 4102444800,
    }
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    alerts_service_module.AlertService.list_alerts = fake_list_alerts

    try:
        with TestClient(app) as client:
            response = client.get(
                f"/alerts{query_string}", headers={"Authorization": "Bearer valid"}
            )
    finally:
        auth_dependencies._decode_access_token = original_decode
        auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
        alerts_service_module.AlertService.list_alerts = original_list_alerts
        app.dependency_overrides.clear()

    return response, received


def test_list_alerts_route_passes_filters_to_service() -> None:
    response, received = _call_list_alerts_route("?status=paused&scenario=price_below&q=sol")

    assert response.status_code == 200
    assert received == {"status_filter": "paused", "scenario": "price_below", "query": "sol"}


@pytest.mark.parametrize(
    "query_string",
    ["?status=archived", "?scenario=daily_change_above", f"?q={'a' * 101}"],
)
def test_list_alerts_route_rejects_invalid_filters(query_string: str) -> None:
    response, received = _call_list_alerts_route(query_string)

    assert response.status_code == 422
    assert received == {}


def test_create_alert_route_maps_validation_error() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_create_alert = alerts_service_module.AlertService.create_alert

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_create_alert(self, user, payload):
        assert user.id == fake_user.id
        assert payload.asset_id == "bitcoin"
        assert payload.scenario == "price_above"
        raise AlertServiceError(
            status_code=422,
            message="Current price is unavailable for the selected coin",
        )

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    alerts_service_module.AlertService.create_alert = fake_create_alert

    with TestClient(app) as client:
        response = client.post(
            "/alerts",
            headers={"Authorization": "Bearer valid"},
            json=_alert_payload(),
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    alerts_service_module.AlertService.create_alert = original_create_alert
    app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["message"] == "Current price is unavailable for the selected coin"


@pytest.mark.parametrize(
    ("method", "path_suffix", "service_name", "json_body"),
    [
        ("put", "", "update_alert", _alert_payload()),
        ("post", "/pause", "pause_alert", None),
        ("post", "/resume", "resume_alert", None),
        ("delete", "", "delete_alert", None),
    ],
)
def test_alert_mutation_routes_map_missing_user_owned_record(
    method: str,
    path_suffix: str,
    service_name: str,
    json_body: dict[str, object] | None,
) -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    fake_user = _make_user()
    alert_id = uuid4()

    original_decode = auth_dependencies._decode_access_token
    original_get_authenticated_user = auth_dependencies.AuthService.get_authenticated_user
    original_service_method = getattr(alerts_service_module.AlertService, service_name)

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    async def fake_service_method(self, user, route_alert_id, payload=None):
        assert user.id == fake_user.id
        assert route_alert_id == alert_id
        _ = payload
        raise AlertServiceError(status_code=404, message="Alert not found")

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    setattr(alerts_service_module.AlertService, service_name, fake_service_method)

    with TestClient(app) as client:
        response = client.request(
            method.upper(),
            f"/alerts/{alert_id}{path_suffix}",
            headers={"Authorization": "Bearer valid"},
            json=json_body,
        )

    auth_dependencies._decode_access_token = original_decode
    auth_dependencies.AuthService.get_authenticated_user = original_get_authenticated_user
    setattr(alerts_service_module.AlertService, service_name, original_service_method)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["message"] == "Alert not found"
