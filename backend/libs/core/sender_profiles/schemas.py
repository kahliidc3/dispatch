from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from libs.core.sender_profiles.models import SenderProfile


class SenderProfileCreateRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    from_name: str = Field(min_length=1, max_length=120)
    from_email: str = Field(min_length=3, max_length=320)
    reply_to: str | None = None
    domain_id: str
    configuration_set_id: str | None = None
    ip_pool_id: str | None = None
    allowed_campaign_types: list[str] = Field(default_factory=list)
    daily_send_limit: int = Field(default=50, ge=1, le=100000)


class SenderProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    from_name: str | None = Field(default=None, min_length=1, max_length=120)
    reply_to: str | None = None
    configuration_set_id: str | None = None
    ip_pool_id: str | None = None
    allowed_campaign_types: list[str] | None = None
    daily_send_limit: int | None = Field(default=None, ge=1, le=100000)
    is_active: bool | None = None
    paused_reason: str | None = None


class SenderProfileDeleteRequest(BaseModel):
    reason: str = Field(default="soft_delete", min_length=3, max_length=255)


class SenderProfileResponse(BaseModel):
    id: str
    display_name: str
    from_name: str
    from_email: str
    reply_to: str | None
    domain_id: str
    configuration_set_id: str | None
    ip_pool_id: str | None
    allowed_campaign_types: list[str]
    is_active: bool
    paused_at: datetime | None
    paused_reason: str | None
    daily_send_count: int
    daily_send_limit: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, profile: SenderProfile) -> SenderProfileResponse:
        return cls(
            id=profile.id,
            display_name=profile.display_name,
            from_name=profile.from_name,
            from_email=profile.from_email,
            reply_to=profile.reply_to,
            domain_id=profile.domain_id,
            configuration_set_id=profile.configuration_set_id,
            ip_pool_id=profile.ip_pool_id,
            allowed_campaign_types=list(profile.allowed_campaign_types),
            is_active=profile.is_active,
            paused_at=profile.paused_at,
            paused_reason=profile.paused_reason,
            daily_send_count=profile.daily_send_count,
            daily_send_limit=profile.daily_send_limit,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


class SenderProfileListResponse(BaseModel):
    items: list[SenderProfileResponse]
