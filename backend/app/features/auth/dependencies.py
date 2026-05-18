import uuid
from dataclasses import dataclass
from typing import Annotated, Any

import jwt
from fastapi import HTTPException, status
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient

from app.core.config import settings
from app.features.auth.models import User
from app.features.auth.service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)
credentials_dependency = Depends(bearer_scheme)
jwks_client = PyJWKClient(settings.supabase_jwks_url)


@dataclass(frozen=True)
class AuthenticatedIdentity:
    supabase_user_id: uuid.UUID
    email: str


def _decode_access_token(token: str) -> dict[str, Any]:
    signing_key = jwks_client.get_signing_key_from_jwt(token).key
    return jwt.decode(
        token,
        signing_key,
        algorithms=[settings.supabase_jwt_algorithm],
        audience=settings.supabase_jwt_audience,
        issuer=settings.supabase_jwt_issuer,
        options={"require": ["exp", "sub"]},
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, credentials_dependency],
    auth_service: Annotated[AuthService, Depends()],
) -> User:
    identity = get_authenticated_identity(credentials)
    return await auth_service.get_authenticated_user(supabase_user_id=identity.supabase_user_id)


def get_authenticated_identity(
    credentials: HTTPAuthorizationCredentials | None,
) -> AuthenticatedIdentity:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing access token")

    try:
        payload = _decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        email = payload.get("email")
        supabase_user_id = uuid.UUID(subject)
        if not isinstance(email, str) or not email:
            raise ValueError("Email is missing")
    except (InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token"
        ) from None

    return AuthenticatedIdentity(supabase_user_id=supabase_user_id, email=email)


async def get_current_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, credentials_dependency],
) -> AuthenticatedIdentity:
    return get_authenticated_identity(credentials)
