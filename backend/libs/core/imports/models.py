from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.core.db.base import Base

if TYPE_CHECKING:
    from libs.core.auth.models import User
    from libs.core.contacts.models import Contact


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (Index("idx_import_jobs_created", "created_at"),)

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    created_by: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    column_mapping: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    source_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_list_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("lists.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    total_rows: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suppressed_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    rows: Mapped[list[ImportRow]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    creator: Mapped[User] = relationship()


class ImportRow(Base):
    __tablename__ = "import_rows"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    import_job_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("import_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    parsed_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_id: Mapped[str | None] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped[ImportJob] = relationship(back_populates="rows")
    contact: Mapped[Contact | None] = relationship()
