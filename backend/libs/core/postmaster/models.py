from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.core.db.base import Base


class PostmasterMetric(Base):
    __tablename__ = "postmaster_metrics"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    domain_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("domains.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    domain_reputation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    spam_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    dkim_success_ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    spf_success_ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    dmarc_success_ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    inbound_encryption_ratio: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    raw_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
