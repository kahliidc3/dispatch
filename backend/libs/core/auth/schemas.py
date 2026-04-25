from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal, cast

from pydantic import BaseModel, Field

from libs.core.auth.models import ApiKey, User

UserRole = Literal["admin", "user"]
ActorType = Literal["user", "api_key"]


class AuthFlow(StrEnum):
    LOGIN = "login"
    ENROLL = "enroll"


@dataclass(slots=True)
class CurrentActor:
    actor_type: ActorType
    user: User
    api_key: ApiKey | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    requires_mfa: bool = False
    mfa_token: str | None = None


class MFAEnrollResponse(BaseModel):
    enrollment_token: str
    otp_auth_uri: str


class MFAVerifyRequest(BaseModel):
    flow: AuthFlow
    code: str = Field(min_length=6, max_length=8)
    token: str


class MessageResponse(BaseModel):
    message: str


class UserCreateRequest(BaseModel):
    email: str
    password: str = Field(min_length=12)
    role: UserRole = "user"


class UserDisableRequest(BaseModel):
    reason: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12)


class UserResponse(BaseModel):
    id: str
    email: str
    role: UserRole
    mfa_enabled: bool
    last_login_at: datetime | None
    created_at: datetime
    deleted_at: datetime | None

    @classmethod
    def from_model(cls, user: User) -> UserResponse:
        return cls(
            id=user.id,
            email=user.email,
            role=cast(UserRole, user.role),
            mfa_enabled=bool(user.mfa_secret),
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            deleted_at=user.deleted_at,
        )


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    expires_at: datetime | None = None


class ApiKeyRotateRequest(BaseModel):
    name: str | None = None
    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    key_last4: str
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    last_used_at: datetime | None

    @classmethod
    def from_model(cls, api_key: ApiKey) -> ApiKeyResponse:
        return cls(
            id=api_key.id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            key_last4=api_key.key_last4,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            revoked_at=api_key.revoked_at,
            last_used_at=api_key.last_used_at,
        )


class ApiKeyCreateResponse(BaseModel):
    api_key: ApiKeyResponse
    plaintext_key: str


class APIKeyAuthCredentials(BaseModel):
    token: str


class UserListResponse(BaseModel):
    items: list[UserResponse]
