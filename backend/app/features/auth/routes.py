from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.features.auth.dependencies import (
    AuthenticatedIdentity,
    get_current_identity,
    get_current_user,
)
from app.features.auth.models import User
from app.features.auth.schemas import (
    AuthSessionResponse,
    CurrentUserResponse,
    ResetPasswordRequest,
    SignInRequest,
    SignOutResponse,
    SignUpRequest,
    SyncUserResponse,
    UpdatePasswordRequest,
)
from app.features.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
current_user_dependency = Depends(get_current_user)
current_identity_dependency = Depends(get_current_identity)


@router.post(
    "/sign-up",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AuthSessionResponse,
    summary="Register user via Supabase",
)
async def sign_up(
    payload: SignUpRequest,
    service: Annotated[AuthService, Depends()],
) -> AuthSessionResponse:
    return await service.register(payload.email, payload.password)


@router.post("/sign-in", response_model=AuthSessionResponse)
async def sign_in(
    payload: SignInRequest,
    service: Annotated[AuthService, Depends()],
) -> AuthSessionResponse:
    return await service.sign_in(payload.email, payload.password)


@router.post("/sync-user", response_model=SyncUserResponse)
async def sync_user(
    service: Annotated[AuthService, Depends()],
    identity: Annotated[AuthenticatedIdentity, current_identity_dependency],
) -> SyncUserResponse:
    user, is_new_user = await service.sync_local_user(
        supabase_user_id=identity.supabase_user_id,
        email=identity.email,
    )
    return SyncUserResponse(
        **CurrentUserResponse.model_validate(user).model_dump(),
        is_new_user=is_new_user,
    )


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    service: Annotated[AuthService, Depends()],
) -> SignOutResponse:
    return await service.request_password_reset(payload.email, payload.redirect_to)


@router.post("/update-password")
async def update_password(
    payload: UpdatePasswordRequest,
    service: Annotated[AuthService, Depends()],
    authorization: str | None = Header(default=None),
    x_refresh_token: str | None = Header(default=None, alias="X-Refresh-Token"),
) -> SignOutResponse:
    return await service.update_user_password(
        authorization=authorization,
        refresh_token=x_refresh_token,
        new_password=payload.password,
    )


@router.get("/me", response_model=CurrentUserResponse)
async def me(
    current_user: Annotated[User, current_user_dependency],
) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


@router.post("/sign-out", response_model=SignOutResponse)
async def sign_out(
    current_user: Annotated[User, current_user_dependency],
) -> SignOutResponse:
    return SignOutResponse(success=bool(current_user.id))
