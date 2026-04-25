from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SesEventType = Literal[
    "Delivery",
    "Bounce",
    "Complaint",
    "Open",
    "Click",
    "Reject",
    "Rendering",
    "DeliveryDelay",
]


class EventProcessResult(BaseModel):
    event_type: SesEventType
    ses_message_id: str
    deduplicated: bool
    message_found: bool
    status_updated: bool = False
    suppression_written: bool = False
    metrics_updated: bool = False
    occurred_at: datetime


class NormalizedSesEvent(BaseModel):
    event_type: SesEventType
    ses_message_id: str
    occurred_at: datetime
    recipient_email: str | None = None
    smtp_response: str | None = None
    processing_time_ms: int | None = None
    bounce_type: str | None = None
    bounce_subtype: str | None = None
    diagnostic_code: str | None = None
    complaint_type: str | None = None
    feedback_type: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None
    link_url: str | None = None
    is_machine_open: bool = False
    raw_payload: dict[str, object]
