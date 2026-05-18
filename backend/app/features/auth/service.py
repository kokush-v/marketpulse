import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient
from supabase_auth.errors import (
    AuthApiError,
    AuthError,
    AuthInvalidCredentialsError,
    AuthRetryableError,
    AuthSessionMissingError,
    AuthUnknownError,
    AuthWeakPasswordError,
)

from app.db.session import get_async_session
from app.features.auth.models import User
from app.features.auth.repository import AuthRepository
from app.features.auth.schemas import (
    AuthSessionResponse,
    SignOutResponse,
)
from app.features.auth.supabase_client import get_supabase_client


def get_auth_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AuthRepository:
    return AuthRepository(session)


class AuthService:
    def __init__(
        self,
        repository: Annotated[AuthRepository, Depends(get_auth_repository)],
        supabase: Annotated[AsyncClient, Depends(get_supabase_client)],
    ) -> None:
        self.repository = repository
        self.supabase = supabase

    def _raise_auth_provider_error(
        self,
        exc: Exception,
        *,
        default_status: int,
    ) -> None:
        if isinstance(exc, AuthWeakPasswordError):
            raise HTTPException(
                status_code=exc.status,
                detail={
                    "message": exc.message,
                    "code": exc.code,
                    "reasons": exc.reasons,
                },
            ) from exc

        if isinstance(exc, AuthInvalidCredentialsError):
            raise HTTPException(
                status_code=default_status,
                detail=exc.message,
            ) from exc

        if isinstance(exc, (AuthApiError, AuthRetryableError)):
            raise HTTPException(
                status_code=exc.status,
                detail={
                    "message": exc.message,
                    "code": getattr(exc, "code", None),
                },
            ) from exc

        if isinstance(exc, AuthSessionMissingError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing active session",
            ) from exc

        if isinstance(exc, AuthUnknownError):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Authentication provider error",
            ) from exc

        if isinstance(exc, AuthError):
            raise HTTPException(
                status_code=default_status,
                detail=exc.message,
            ) from exc

        raise HTTPException(
            status_code=default_status,
            detail=str(exc),
        ) from exc

    async def _get_or_create_user(
        self, supabase_user_id: uuid.UUID, email: str
    ) -> tuple[User, bool]:
        existing = await self.repository.get_user_by_supabase_id(supabase_user_id=supabase_user_id)
        if existing:
            normalized_email = email.lower()
            if existing.email != normalized_email:
                existing = await self.repository.update_user_email(existing, normalized_email)
            return existing, False
        user = await self.repository.create_user(supabase_user_id=supabase_user_id, email=email)
        return user, True

    async def get_authenticated_user(self, supabase_user_id: uuid.UUID) -> User:
        existing = await self.repository.get_user_by_supabase_id(supabase_user_id=supabase_user_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not registered in local system",
            )
        return existing

    async def ensure_local_user(self, supabase_user_id: uuid.UUID, email: str) -> User:
        user, _ = await self._get_or_create_user(
            supabase_user_id=supabase_user_id,
            email=email,
        )
        return user

    async def sync_local_user(self, supabase_user_id: uuid.UUID, email: str) -> tuple[User, bool]:
        return await self._get_or_create_user(
            supabase_user_id=supabase_user_id,
            email=email,
        )

    def _extract_session_payload(self, auth_response: object) -> AuthSessionResponse:
        session = getattr(auth_response, "session", None)
        if not session:
            return AuthSessionResponse(requires_email_verification=True)

        access_token = getattr(session, "access_token", None)
        refresh_token = getattr(session, "refresh_token", None)
        if not access_token or not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication session is incomplete",
            )

        return AuthSessionResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=getattr(session, "token_type", "bearer"),
            expires_in=getattr(session, "expires_in", 3600),
        )

    async def _ensure_local_user_from_auth_response(self, auth_response: object) -> None:
        user = getattr(auth_response, "user", None)
        if user is None:
            session = getattr(auth_response, "session", None)
            user = getattr(session, "user", None) if session is not None else None
        if user is None:
            return

        user_id = getattr(user, "id", None)
        email = getattr(user, "email", None)
        if not user_id or not isinstance(email, str) or not email:
            return

        try:
            supabase_user_id = uuid.UUID(str(user_id))
        except (TypeError, ValueError):
            return

        await self._get_or_create_user(supabase_user_id=supabase_user_id, email=email)

    async def register(self, email: str, password: str) -> AuthSessionResponse:
        try:
            response = await self.supabase.auth.sign_up({"email": email, "password": password})
        except Exception as exc:
            self._raise_auth_provider_error(
                exc,
                default_status=status.HTTP_400_BAD_REQUEST,
            )
        await self._ensure_local_user_from_auth_response(response)
        return self._extract_session_payload(response)

    async def sign_in(self, email: str, password: str) -> AuthSessionResponse:
        try:
            response = await self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
        except Exception as exc:
            self._raise_auth_provider_error(
                exc,
                default_status=status.HTTP_401_UNAUTHORIZED,
            )
        await self._ensure_local_user_from_auth_response(response)
        return self._extract_session_payload(response)

    async def request_password_reset(self, email: str, redirect_to: str | None) -> SignOutResponse:
        options: dict[str, str] | None = None
        if redirect_to:
            options = {"redirect_to": redirect_to}
        try:
            await self.supabase.auth.reset_password_email(email, options=options)
        except Exception as exc:
            self._raise_auth_provider_error(
                exc,
                default_status=status.HTTP_400_BAD_REQUEST,
            )
        return SignOutResponse(success=True)

    async def update_user_password(
        self,
        authorization: str | None,
        refresh_token: str | None,
        new_password: str,
    ) -> SignOutResponse:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing access token",
            )
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing refresh token",
            )

        access_token = authorization.split(" ", 1)[1]
        try:
            await self.supabase.auth.set_session(access_token, refresh_token)
            await self.supabase.auth.update_user({"password": new_password})
        except Exception as exc:
            self._raise_auth_provider_error(
                exc,
                default_status=status.HTTP_400_BAD_REQUEST,
            )
        return SignOutResponse(success=True)
