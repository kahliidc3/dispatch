from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.core.db.base import Base

if TYPE_CHECKING:
    from libs.core.lists.models import ListMembership


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ux_contacts_email_lower", text("lower(email)"), unique=True),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email_domain: Mapped[str] = mapped_column(Text, nullable=False)
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    country_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_attributes: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    lifecycle_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    validation_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    validation_score: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_engaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_sends: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_opens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_replies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sources: Mapped[list[ContactSource]] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    preferences: Mapped[Preference | None] = relationship(
        back_populates="contact",
        uselist=False,
        cascade="all, delete-orphan",
    )
    subscription_statuses: Mapped[list[SubscriptionStatus]] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    list_memberships: Mapped[list[ListMembership]] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
    )


class ContactSource(Base):
    __tablename__ = "contact_sources"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    contact_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_list: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    contact: Mapped[Contact] = relationship(back_populates="sources")


class SubscriptionStatus(Base):
    __tablename__ = "subscription_statuses"
    __table_args__ = (
        UniqueConstraint("contact_id", "channel", name="uq_subscription_contact_channel"),
    )

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    contact_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="subscribed")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    contact: Mapped[Contact] = relationship(back_populates="subscription_statuses")


class Preference(Base):
    __tablename__ = "preferences"
    __table_args__ = (UniqueConstraint("contact_id", name="uq_preferences_contact_id"),)

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    contact_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    campaign_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)).with_variant(JSON, "sqlite"),
        nullable=False,
        default=list,
    )
    max_frequency_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    contact: Mapped[Contact] = relationship(back_populates="preferences")
