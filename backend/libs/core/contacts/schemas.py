from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from libs.core.contacts.models import Contact, Preference, SubscriptionStatus

ContactLifecycleStatus = Literal[
    "active",
    "bounced",
    "complained",
    "unsubscribed",
    "suppressed",
    "deleted",
]
ContactValidationStatus = Literal["pending", "valid", "invalid", "risky", "unknown"]
ContactSourceType = Literal["csv_import", "api", "webhook", "manual", "integration"]
SubscriptionState = Literal["subscribed", "unsubscribed", "pending", "unconfirmed"]


class ContactCreateRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    company: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    country_code: str | None = Field(default=None, max_length=4)
    timezone: str | None = Field(default=None, max_length=64)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)
    source_type: ContactSourceType = "api"
    source_detail: str | None = Field(default=None, max_length=255)
    source_list: str | None = Field(default=None, max_length=255)


class ContactUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    company: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    country_code: str | None = Field(default=None, max_length=4)
    timezone: str | None = Field(default=None, max_length=64)
    custom_attributes: dict[str, Any] | None = None
    lifecycle_status: ContactLifecycleStatus | None = None


class ContactResponse(BaseModel):
    id: str
    email: str
    email_domain: str
    first_name: str | None
    last_name: str | None
    company: str | None
    title: str | None
    phone: str | None
    country_code: str | None
    timezone: str | None
    custom_attributes: dict[str, Any]
    lifecycle_status: ContactLifecycleStatus
    validation_status: ContactValidationStatus
    validation_score: float | None
    last_validated_at: datetime | None
    last_engaged_at: datetime | None
    total_sends: int
    total_opens: int
    total_clicks: int
    total_replies: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @classmethod
    def from_model(cls, contact: Contact) -> ContactResponse:
        return cls(
            id=contact.id,
            email=contact.email,
            email_domain=contact.email_domain,
            first_name=contact.first_name,
            last_name=contact.last_name,
            company=contact.company,
            title=contact.title,
            phone=contact.phone,
            country_code=contact.country_code,
            timezone=contact.timezone,
            custom_attributes=dict(contact.custom_attributes),
            lifecycle_status=cast(ContactLifecycleStatus, contact.lifecycle_status),
            validation_status=cast(ContactValidationStatus, contact.validation_status),
            validation_score=float(contact.validation_score)
            if contact.validation_score is not None
            else None,
            last_validated_at=contact.last_validated_at,
            last_engaged_at=contact.last_engaged_at,
            total_sends=contact.total_sends,
            total_opens=contact.total_opens,
            total_clicks=contact.total_clicks,
            total_replies=contact.total_replies,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
            deleted_at=contact.deleted_at,
        )


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    limit: int
    offset: int


class ContactPreferenceUpdateRequest(BaseModel):
    campaign_types: list[str] = Field(default_factory=list)
    max_frequency_per_week: int | None = Field(default=None, ge=1, le=100)
    language: str = Field(default="en", min_length=2, max_length=10)


class ContactPreferenceResponse(BaseModel):
    contact_id: str
    campaign_types: list[str]
    max_frequency_per_week: int | None
    language: str
    updated_at: datetime

    @classmethod
    def from_model(cls, preference: Preference) -> ContactPreferenceResponse:
        return cls(
            contact_id=preference.contact_id,
            campaign_types=list(preference.campaign_types),
            max_frequency_per_week=preference.max_frequency_per_week,
            language=preference.language,
            updated_at=preference.updated_at,
        )


class SubscriptionStatusResponse(BaseModel):
    contact_id: str
    channel: str
    status: SubscriptionState
    reason: str | None
    effective_at: datetime

    @classmethod
    def from_model(cls, status: SubscriptionStatus) -> SubscriptionStatusResponse:
        return cls(
            contact_id=status.contact_id,
            channel=status.channel,
            status=cast(SubscriptionState, status.status),
            reason=status.reason,
            effective_at=status.effective_at,
        )


class ContactUnsubscribeRequest(BaseModel):
    reason: str = Field(default="user_request", min_length=3, max_length=255)


class ContactDeleteRequest(BaseModel):
    reason: str = Field(default="gdpr_request", min_length=3, max_length=255)


class ContactUnsubscribeTokenResponse(BaseModel):
    token: str
    unsubscribe_url: str


class PublicUnsubscribeRequest(BaseModel):
    token: str = Field(min_length=16, max_length=4096)


class ContactQueryParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    lifecycle_status: ContactLifecycleStatus | None = None
    search: str | None = Field(default=None, max_length=320)
    email_domain: str | None = Field(default=None, max_length=255)
