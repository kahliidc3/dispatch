from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.campaigns.models import CampaignRun
from libs.core.segments.models import Segment, SegmentSnapshot


class SegmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_segment(
        self,
        *,
        name: str,
        description: str | None,
        definition: dict[str, object],
    ) -> Segment:
        segment = Segment(
            name=name,
            description=description,
            definition=definition,
            updated_at=datetime.now(UTC),
        )
        self.session.add(segment)
        await self.session.flush()
        return segment

    async def get_segment_by_id(self, segment_id: str) -> Segment | None:
        stmt = select(Segment).where(Segment.id == segment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_segments(self) -> list[Segment]:
        stmt = select(Segment).order_by(Segment.updated_at.desc(), Segment.id.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_segment(self, *, segment_id: str, values: dict[str, object]) -> bool:
        if not values:
            return False
        next_values = dict(values)
        next_values["updated_at"] = datetime.now(UTC)
        stmt = (
            update(Segment)
            .where(Segment.id == segment_id)
            .values(**next_values)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def get_campaign_run_by_id(self, campaign_run_id: str) -> CampaignRun | None:
        stmt = select(CampaignRun).where(CampaignRun.id == campaign_run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_campaign_run(
        self,
        *,
        campaign_run_id: str,
        eligible_count: int,
    ) -> bool:
        stmt = (
            update(CampaignRun)
            .where(CampaignRun.id == campaign_run_id)
            .values(eligible_count=eligible_count)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def count_snapshots_for_run(self, *, campaign_run_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(SegmentSnapshot)
            .where(SegmentSnapshot.campaign_run_id == campaign_run_id)
            .where(SegmentSnapshot.included.is_(True))
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create_snapshots(self, *, rows: list[SegmentSnapshot]) -> None:
        self.session.add_all(rows)
        await self.session.flush()
