from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from libs.core.db.base import Base


class DeliveryEvent(Base):
    __tablename__ = "delivery_events"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    smtp_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BounceEvent(Base):
    __tablename__ = "bounce_events"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bounce_type: Mapped[str] = mapped_column(String(20), nullable=False)
    bounce_subtype: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostic_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ComplaintEvent(Base):
    __tablename__ = "complaint_events"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    complaint_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OpenEvent(Base):
    __tablename__ = "open_events"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_machine_open: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    link_url: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RollingMetric(Base):
    __tablename__ = "rolling_metrics"
    __table_args__ = (
        UniqueConstraint(
            "scope_type", "scope_id", "window", name="uq_rolling_metrics_scope_window"
        ),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    scope_type: Mapped[str] = mapped_column(Text, nullable=False)
    scope_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), nullable=False)
    window: Mapped[str] = mapped_column("window", String(8), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sends: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deliveries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bounces: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    complaints: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    opens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    replies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unsubscribes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bounce_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    complaint_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
