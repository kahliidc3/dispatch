from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.core.db.base import Base
from libs.core.domains.models import Domain, IPPool, SESConfigurationSet


class SenderProfile(Base):
    __tablename__ = "sender_profiles"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    from_name: Mapped[str] = mapped_column(Text, nullable=False)
    from_email: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    reply_to: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("domains.id", ondelete="RESTRICT"),
        nullable=False,
    )
    configuration_set_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("ses_configuration_sets.id", ondelete="SET NULL"),
        nullable=True,
    )
    ip_pool_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("ip_pools.id", ondelete="SET NULL"),
        nullable=True,
    )
    allowed_campaign_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)).with_variant(JSON, "sqlite"),
        nullable=False,
        default=list,
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    daily_send_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_send_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
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

    domain: Mapped[Domain] = relationship(back_populates="sender_profiles")
    configuration_set: Mapped[SESConfigurationSet | None] = relationship(
        back_populates="sender_profiles",
    )
    ip_pool: Mapped[IPPool | None] = relationship(back_populates="sender_profiles")
