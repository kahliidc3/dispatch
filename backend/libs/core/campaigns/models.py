from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    DDL,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.core.db.base import Base

if TYPE_CHECKING:
    from libs.core.contacts.models import Contact


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(30), nullable=False)
    sender_profile_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("sender_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    template_version_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("template_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    segment_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("segments.id", ondelete="SET NULL"),
        nullable=True,
    )
    list_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("lists.id", ondelete="SET NULL"),
        nullable=True,
    )
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False, default="immediate")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str | None] = mapped_column(Text, nullable=True, default="UTC")
    send_rate_per_hour: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    tracking_opens: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tracking_clicks: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_eligible: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_delivered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_bounced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_complained: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_opened: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_clicked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_replied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_unsubscribed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    runs: Mapped[list[CampaignRun]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    messages: Mapped[list[Message]] = relationship(back_populates="campaign")


class CampaignRun(Base):
    __tablename__ = "campaign_runs"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "run_number",
            name="uq_campaign_runs_campaign_id_run_number",
        ),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    campaign_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    eligible_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")

    campaign: Mapped[Campaign] = relationship(back_populates="runs")
    batches: Mapped[list[SendBatch]] = relationship(
        back_populates="campaign_run",
        cascade="all, delete-orphan",
    )


class SendBatch(Base):
    __tablename__ = "send_batches"
    __table_args__ = (
        UniqueConstraint(
            "campaign_run_id",
            "batch_number",
            name="uq_send_batches_campaign_run_id_batch_number",
        ),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    campaign_run_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("campaign_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    batch_number: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sender_profile_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("sender_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ip_pool_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("ip_pools.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    enqueued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign_run: Mapped[CampaignRun] = relationship(back_populates="batches")
    messages: Mapped[list[Message]] = relationship(back_populates="send_batch")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    campaign_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    send_batch_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("send_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    contact_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    sender_profile_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("sender_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    domain_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("domains.id", ondelete="RESTRICT"),
        nullable=False,
    )
    to_email: Mapped[str] = mapped_column(Text, nullable=False)
    from_email: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    ses_message_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    ml_spam_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    personalization_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    headers: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_clicked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bounce_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    complaint_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    campaign: Mapped[Campaign | None] = relationship(back_populates="messages")
    send_batch: Mapped[SendBatch | None] = relationship(back_populates="messages")
    contact: Mapped[Contact | None] = relationship()


_SQLITE_MESSAGE_STATUS_TRANSITION_TRIGGER = DDL(  # type: ignore[no-untyped-call]
    """
    CREATE TRIGGER trg_messages_status_transition_guard
    BEFORE UPDATE OF status ON messages
    FOR EACH ROW
    WHEN NOT (
        NEW.status = OLD.status
        OR (OLD.status = 'queued' AND NEW.status = 'paused')
        OR (OLD.status = 'queued' AND NEW.status = 'sending')
        OR (OLD.status = 'paused' AND NEW.status IN ('queued','failed'))
        OR (OLD.status = 'sending' AND NEW.status IN ('sent','failed'))
        OR (OLD.status = 'sent' AND NEW.status IN ('delivered','bounced','complained'))
    )
    BEGIN
        SELECT RAISE(FAIL, 'invalid message status transition');
    END
    """
)

_POSTGRES_MESSAGE_STATUS_TRANSITION_TRIGGER = DDL(  # type: ignore[no-untyped-call]
    """
    CREATE OR REPLACE FUNCTION messages_status_transition_guard()
    RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        IF NEW.status = OLD.status THEN
            RETURN NEW;
        END IF;

        IF (OLD.status = 'queued' AND NEW.status = 'paused')
            OR (OLD.status = 'queued' AND NEW.status = 'sending')
            OR (OLD.status = 'paused' AND NEW.status IN ('queued','failed'))
            OR (OLD.status = 'sending' AND NEW.status IN ('sent','failed'))
            OR (OLD.status = 'sent' AND NEW.status IN ('delivered','bounced','complained'))
        THEN
            RETURN NEW;
        END IF;

        RAISE EXCEPTION 'invalid message status transition: % -> %', OLD.status, NEW.status;
    END;
    $$;

    CREATE TRIGGER trg_messages_status_transition_guard
    BEFORE UPDATE OF status ON messages
    FOR EACH ROW
    EXECUTE FUNCTION messages_status_transition_guard();
    """
)

event.listen(
    Message.__table__,
    "after_create",
    _SQLITE_MESSAGE_STATUS_TRANSITION_TRIGGER.execute_if(dialect="sqlite"),
)
event.listen(
    Message.__table__,
    "after_create",
    _POSTGRES_MESSAGE_STATUS_TRANSITION_TRIGGER.execute_if(dialect="postgresql"),
)
