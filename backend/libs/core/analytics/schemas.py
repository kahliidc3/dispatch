from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ReadinessResponse(BaseModel):
    status: str


class RollingWindowSchema(BaseModel):
    window: str
    sends: int
    deliveries: int
    bounces: int
    complaints: int
    opens: int
    clicks: int
    bounce_rate: Decimal | None = None
    complaint_rate: Decimal | None = None
    window_end: datetime


class CampaignAnalyticsResponse(BaseModel):
    campaign_id: str
    campaign_name: str
    status: str
    total_sent: int
    total_delivered: int
    total_bounced: int
    total_complained: int
    total_opened: int
    total_clicked: int
    total_replied: int
    total_unsubscribed: int
    rolling_windows: list[RollingWindowSchema]
    last_updated_at: datetime


class DomainAnalyticsResponse(BaseModel):
    domain_id: str
    domain_name: str
    reputation_status: str
    circuit_breaker_state: str | None = None
    rolling_windows: list[RollingWindowSchema]
    last_updated_at: datetime


class TopCampaignItem(BaseModel):
    campaign_id: str
    name: str
    sends_today: int
    delivered: int


class TopFailingDomainItem(BaseModel):
    domain_id: str
    name: str
    bounce_rate: Decimal | None = None
    circuit_breaker_state: str | None = None


class OverviewResponse(BaseModel):
    sends_today: int
    sends_7d: int
    top_campaigns: list[TopCampaignItem]
    top_failing_domains: list[TopFailingDomainItem]
    last_updated_at: datetime


class MessageListItem(BaseModel):
    message_id: str
    to_email: str
    status: str
    created_at: datetime
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    bounce_type: str | None = None
    complaint_type: str | None = None


class MessageListResponse(BaseModel):
    items: list[MessageListItem]
    next_cursor: str | None = None
