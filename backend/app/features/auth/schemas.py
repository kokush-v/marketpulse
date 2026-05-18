from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


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
    email: EmailStr
    password: str = Field(min_length=8)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    redirect_to: str | None = None


class UpdatePasswordRequest(BaseModel):
    password: str = Field(min_length=8)


class AuthSessionResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    requires_email_verification: bool = False
