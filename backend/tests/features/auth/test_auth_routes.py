from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError, AuthInvalidCredentialsError, AuthWeakPasswordError

from app.db.session import get_async_session
from app.features.auth.models import User
from app.main import app


def _make_token(*, subject: str, email: str, expired: bool = False) -> str:
    _ = expired
    return f"fake-token-{subject}-{email}"


def test_protected_api_missing_token_returns_401() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    with TestClient(app) as client:
        response = client.get("/auth/me")
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing access token"


def test_protected_api_invalid_token_returns_401() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session
    with TestClient(app) as client:
        response = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
    app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"


def test_protected_api_valid_token_resolves_authenticated_user() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session

    fake_user = User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="user@example.com",
        created_at=datetime.now(tz=UTC),
    )

    from app.features.auth import dependencies as auth_dependencies

    original = auth_dependencies.AuthService.get_authenticated_user
    original_decode = auth_dependencies._decode_access_token

    async def fake_get_authenticated_user(self, supabase_user_id):
        assert str(supabase_user_id)
        return fake_user

    def fake_decode_access_token(_token: str):
        return {"sub": str(uuid4()), "email": "user@example.com", "exp": 4102444800}

    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    auth_dependencies._decode_access_token = fake_decode_access_token

    token = _make_token(subject=str(uuid4()), email="user@example.com")
    with TestClient(app) as client:
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    auth_dependencies.AuthService.get_authenticated_user = original
    auth_dependencies._decode_access_token = original_decode
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(fake_user.id)
    assert response.json()["email"] == fake_user.email


def test_ownership_comes_from_authenticated_context() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session

    fake_user = User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="owner@example.com",
        created_at=datetime.now(tz=UTC),
    )

    from app.features.auth import dependencies as auth_dependencies

    original = auth_dependencies.AuthService.get_authenticated_user
    original_decode = auth_dependencies._decode_access_token

    async def fake_get_authenticated_user(self, supabase_user_id):
        return fake_user

    def fake_decode_access_token(_token: str):
        return {"sub": str(uuid4()), "email": "owner@example.com", "exp": 4102444800}

    auth_dependencies.AuthService.get_authenticated_user = fake_get_authenticated_user
    auth_dependencies._decode_access_token = fake_decode_access_token

    token = _make_token(subject=str(uuid4()), email="owner@example.com")
    with TestClient(app) as client:
        response = client.get(
            "/auth/me?user_id=00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"},
        )

    auth_dependencies.AuthService.get_authenticated_user = original
    auth_dependencies._decode_access_token = original_decode
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(fake_user.id)


def test_sync_user_creates_or_updates_local_user_from_authenticated_token() -> None:
    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session

    fake_user = User(
        id=uuid4(),
        supabase_user_id=uuid4(),
        email="owner@example.com",
        created_at=datetime.now(tz=UTC),
    )

    from app.features.auth import dependencies as auth_dependencies
    from app.features.auth import service as auth_service_module

    original_decode = auth_dependencies._decode_access_token
    original_sync = auth_service_module.AuthService.sync_local_user

    def fake_decode_access_token(_token: str):
        return {"sub": str(fake_user.supabase_user_id), "email": fake_user.email, "exp": 4102444800}

    async def fake_sync_local_user(self, supabase_user_id, email):
        assert supabase_user_id == fake_user.supabase_user_id
        assert email == fake_user.email
        return fake_user, True

    auth_dependencies._decode_access_token = fake_decode_access_token
    auth_service_module.AuthService.sync_local_user = fake_sync_local_user

    token = _make_token(subject=str(fake_user.supabase_user_id), email=fake_user.email)
    with TestClient(app) as client:
        response = client.post("/auth/sync-user", headers={"Authorization": f"Bearer {token}"})

    auth_dependencies._decode_access_token = original_decode
    auth_service_module.AuthService.sync_local_user = original_sync
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(fake_user.id)
    assert response.json()["email"] == fake_user.email
    assert response.json()["is_new_user"] is True


def test_sign_up_without_immediate_session_requests_email_verification() -> None:
    async def fake_register(self, email, password):
        assert email == "pending@example.com"
        assert password == "secret123"
        return {
            "access_token": None,
            "refresh_token": None,
            "token_type": None,
            "expires_in": None,
            "requires_email_verification": True,
        }

    from app.features.auth import service as auth_service_module

    original_register = auth_service_module.AuthService.register
    auth_service_module.AuthService.register = fake_register

    with TestClient(app) as client:
        response = client.post(
            "/auth/sign-up",
            json={"email": "pending@example.com", "password": "secret123"},
        )

    auth_service_module.AuthService.register = original_register

    assert response.status_code == 202
    assert response.json()["requires_email_verification"] is True
    assert response.json()["access_token"] is None


def test_extract_session_payload_without_session_returns_verification_state() -> None:
    from app.features.auth.service import AuthService

    service = AuthService(repository=object(), supabase=object())

    result = service._extract_session_payload(SimpleNamespace(session=None))

    assert result.requires_email_verification is True
    assert result.access_token is None


def test_auth_provider_rate_limit_error_maps_to_429() -> None:
    from app.features.auth.service import AuthService

    service = AuthService(repository=object(), supabase=object())

    with pytest.raises(Exception) as exc_info:
        service._raise_auth_provider_error(
            AuthApiError(
                "email rate limit exceeded",
                429,
                "over_email_send_rate_limit",
            ),
            default_status=400,
        )

    response = exc_info.value
    assert response.status_code == 429
    assert response.detail == {
        "message": "email rate limit exceeded",
        "code": "over_email_send_rate_limit",
    }


def test_auth_provider_invalid_credentials_maps_to_default_status() -> None:
    from app.features.auth.service import AuthService

    service = AuthService(repository=object(), supabase=object())

    with pytest.raises(Exception) as exc_info:
        service._raise_auth_provider_error(
            AuthInvalidCredentialsError("Invalid login credentials"),
            default_status=401,
        )

    response = exc_info.value
    assert response.status_code == 401
    assert response.detail == "Invalid login credentials"


def test_auth_provider_weak_password_includes_reasons() -> None:
    from app.features.auth.service import AuthService

    service = AuthService(repository=object(), supabase=object())

    with pytest.raises(Exception) as exc_info:
        service._raise_auth_provider_error(
            AuthWeakPasswordError("Password is too weak", 422, ["too short"]),
            default_status=400,
        )

    response = exc_info.value
    assert response.status_code == 422
    assert response.detail == {
        "message": "Password is too weak",
        "code": "weak_password",
        "reasons": ["too short"],
    }


def test_sign_up_request_rejects_invalid_email_and_short_password() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/auth/sign-up",
            json={"email": "not-an-email", "password": "short"},
        )

    assert response.status_code == 422


def test_reset_password_request_rejects_invalid_email() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/auth/reset-password",
            json={"email": "not-an-email"},
        )

    assert response.status_code == 422
