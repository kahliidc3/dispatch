from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    DDL,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    Uuid,
    event,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.core.db.base import Base

if TYPE_CHECKING:
    from libs.core.campaigns.models import CampaignRun
    from libs.core.contacts.models import Contact


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    definition: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    cached_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class SegmentSnapshot(Base):
    __tablename__ = "segment_snapshots"

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
    contact_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    included: Mapped[bool] = mapped_column(Boolean, nullable=False)
    exclusion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    frozen_attributes: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    campaign_run: Mapped[CampaignRun] = relationship()
    contact: Mapped[Contact] = relationship()


_SQLITE_APPEND_ONLY_UPDATE_TRIGGER = DDL(  # type: ignore[no-untyped-call]
    """
    CREATE TRIGGER trg_segment_snapshots_no_update
    BEFORE UPDATE ON segment_snapshots
    BEGIN
        SELECT RAISE(FAIL, 'segment_snapshots is append-only');
    END
    """
)

_SQLITE_APPEND_ONLY_DELETE_TRIGGER = DDL(  # type: ignore[no-untyped-call]
    """
    CREATE TRIGGER trg_segment_snapshots_no_delete
    BEFORE DELETE ON segment_snapshots
    BEGIN
        SELECT RAISE(FAIL, 'segment_snapshots is append-only');
    END
    """
)

_POSTGRES_APPEND_ONLY_TRIGGER = DDL(  # type: ignore[no-untyped-call]
    """
    CREATE OR REPLACE FUNCTION segment_snapshots_block_mutation()
    RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RAISE EXCEPTION 'segment_snapshots is append-only';
    END;
    $$;

    CREATE TRIGGER trg_segment_snapshots_no_update_delete
    BEFORE UPDATE OR DELETE ON segment_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION segment_snapshots_block_mutation();
    """
)

event.listen(
    SegmentSnapshot.__table__,
    "after_create",
    _SQLITE_APPEND_ONLY_UPDATE_TRIGGER.execute_if(dialect="sqlite"),
)
event.listen(
    SegmentSnapshot.__table__,
    "after_create",
    _SQLITE_APPEND_ONLY_DELETE_TRIGGER.execute_if(dialect="sqlite"),
)
event.listen(
    SegmentSnapshot.__table__,
    "after_create",
    _POSTGRES_APPEND_ONLY_TRIGGER.execute_if(dialect="postgresql"),
)
