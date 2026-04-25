from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from libs.core.contacts.models import Contact
from libs.core.segments.models import Segment


class SegmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    dsl_json: dict[str, Any]


class SegmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    dsl_json: dict[str, Any] | None = None


class SegmentContactSampleResponse(BaseModel):
    id: str
    email: str
    email_domain: str
    first_name: str | None
    last_name: str | None
    lifecycle_status: str

    @classmethod
    def from_model(cls, contact: Contact) -> SegmentContactSampleResponse:
        return cls(
            id=contact.id,
            email=contact.email,
            email_domain=contact.email_domain,
            first_name=contact.first_name,
            last_name=contact.last_name,
            lifecycle_status=contact.lifecycle_status,
        )


class SegmentResponse(BaseModel):
    id: str
    name: str
    description: str | None
    dsl_json: dict[str, Any]
    last_computed_count: int | None
    last_computed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(
        cls,
        segment: Segment,
        *,
        description: str | None,
    ) -> SegmentResponse:
        return cls(
            id=segment.id,
            name=segment.name,
            description=description,
            dsl_json=dict(segment.definition),
            last_computed_count=segment.cached_size,
            last_computed_at=segment.cached_at,
            created_at=segment.created_at,
            updated_at=segment.updated_at,
        )


class SegmentListResponse(BaseModel):
    items: list[SegmentResponse]


class SegmentPreviewResponse(BaseModel):
    total_count: int
    sample: list[SegmentContactSampleResponse]
