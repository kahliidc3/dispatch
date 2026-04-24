from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.auth.models import AuditLog
from libs.core.suppression.models import SuppressionEntry


class SuppressionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entry_id: str) -> SuppressionEntry | None:
        stmt = select(SuppressionEntry).where(SuppressionEntry.id == entry_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> SuppressionEntry | None:
        stmt = select(SuppressionEntry).where(func.lower(SuppressionEntry.email) == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_email(self, email: str) -> SuppressionEntry | None:
        now = datetime.now(UTC)
        stmt = (
            select(SuppressionEntry)
            .where(func.lower(SuppressionEntry.email) == email.lower())
            .where(
                or_(
                    SuppressionEntry.expires_at.is_(None),
                    SuppressionEntry.expires_at > now,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_entries(
        self,
        *,
        limit: int,
        offset: int,
        stored_reason: str | None,
    ) -> list[SuppressionEntry]:
        stmt = select(SuppressionEntry).order_by(
            SuppressionEntry.created_at.desc(),
            SuppressionEntry.id.desc(),
        )
        if stored_reason is not None:
            stmt = stmt.where(SuppressionEntry.reason == stored_reason)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_entries(self, *, stored_reason: str | None) -> int:
        stmt = select(func.count()).select_from(SuppressionEntry)
        if stored_reason is not None:
            stmt = stmt.where(SuppressionEntry.reason == stored_reason)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_active_entries(
        self,
        *,
        limit: int,
        offset: int,
    ) -> list[SuppressionEntry]:
        now = datetime.now(UTC)
        stmt = (
            select(SuppressionEntry)
            .where(
                or_(
                    SuppressionEntry.expires_at.is_(None),
                    SuppressionEntry.expires_at > now,
                )
            )
            .order_by(SuppressionEntry.created_at.asc(), SuppressionEntry.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_entry(
        self,
        *,
        email: str,
        reason: str,
        source_event_id: str | None,
        campaign_id: str | None,
        notes: str | None,
        expires_at: datetime | None,
    ) -> SuppressionEntry:
        entry = SuppressionEntry(
            email=email,
            reason=reason,
            source_event_id=source_event_id,
            campaign_id=campaign_id,
            notes=notes,
            expires_at=expires_at,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def update_entry(
        self,
        *,
        entry_id: str,
        values: dict[str, object],
    ) -> bool:
        stmt = (
            update(SuppressionEntry)
            .where(SuppressionEntry.id == entry_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def delete_entry(self, *, entry_id: str) -> bool:
        stmt = delete(SuppressionEntry).where(SuppressionEntry.id == entry_id)
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def count_audit_actions_since(
        self,
        *,
        action: str,
        occurred_after: datetime,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == action)
            .where(AuditLog.occurred_at >= occurred_after)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_remote_sync_candidates(
        self,
        *,
        after: datetime | None,
        limit: int,
    ) -> list[SuppressionEntry]:
        stmt = select(SuppressionEntry).where(
            or_(
                SuppressionEntry.expires_at.is_(None),
                SuppressionEntry.expires_at > datetime.now(UTC),
            )
        )
        if after is not None:
            stmt = stmt.where(SuppressionEntry.created_at >= after)
        stmt = stmt.order_by(
            SuppressionEntry.created_at.asc(),
            SuppressionEntry.id.asc(),
        ).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_many_active_by_emails(self, *, emails: list[str]) -> list[SuppressionEntry]:
        if not emails:
            return []
        lowered = [item.lower() for item in emails]
        now = datetime.now(UTC)
        stmt = (
            select(SuppressionEntry)
            .where(
                func.lower(SuppressionEntry.email).in_(lowered),
            )
            .where(
                or_(
                    SuppressionEntry.expires_at.is_(None),
                    SuppressionEntry.expires_at > now,
                )
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
