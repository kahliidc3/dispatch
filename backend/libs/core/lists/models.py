from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from libs.core.contacts.models import Contact
from libs.core.db.base import Base


class List(Base):
    __tablename__ = "lists"

    id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    memberships: Mapped[list[ListMembership]] = relationship(
        back_populates="list_entity",
        cascade="all, delete-orphan",
    )


class ListMembership(Base):
    __tablename__ = "list_members"

    list_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("lists.id", ondelete="CASCADE"),
        primary_key=True,
    )
    contact_id: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    list_entity: Mapped[List] = relationship(back_populates="memberships")
    contact: Mapped[Contact] = relationship(back_populates="list_memberships")
