from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    id: UUID
    supabase_user_id: UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncUserResponse(CurrentUserResponse):
    is_new_user: bool


class SignOutResponse(BaseModel):
    success: bool


class SignUpRequest(BaseModel):
    email: str
    password: str


class SignInRequest(BaseModel):
    email: str
    password: str


class ResetPasswordRequest(BaseModel):
    email: str
    redirect_to: str | None = None


class UpdatePasswordRequest(BaseModel):
    password: str


class AuthSessionResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    requires_email_verification: bool = False
