from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.domains.models import Domain
from libs.core.postmaster.models import PostmasterMetric


class PostmasterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_verified_domains(self) -> list[Domain]:
        stmt = select(Domain).where(Domain.verification_status == "verified")
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_metric_for_date(
        self,
        *,
        domain_id: str,
        report_date: date,
    ) -> PostmasterMetric | None:
        stmt = (
            select(PostmasterMetric)
            .where(PostmasterMetric.domain_id == domain_id)
            .where(PostmasterMetric.date == report_date)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_metric(self, *, metric: PostmasterMetric) -> PostmasterMetric:
        existing = await self.get_metric_for_date(
            domain_id=metric.domain_id,
            report_date=metric.date,
        )
        if existing is None:
            self.session.add(metric)
            await self.session.flush()
            return metric

        existing.domain_reputation = metric.domain_reputation
        existing.spam_rate = metric.spam_rate
        existing.dkim_success_ratio = metric.dkim_success_ratio
        existing.spf_success_ratio = metric.spf_success_ratio
        existing.dmarc_success_ratio = metric.dmarc_success_ratio
        existing.inbound_encryption_ratio = metric.inbound_encryption_ratio
        existing.raw_json = metric.raw_json
        existing.fetched_at = metric.fetched_at
        await self.session.flush()
        return existing

    async def list_metrics_for_domain(
        self,
        *,
        domain_id: str,
        limit: int = 30,
    ) -> list[PostmasterMetric]:
        stmt = (
            select(PostmasterMetric)
            .where(PostmasterMetric.domain_id == domain_id)
            .order_by(PostmasterMetric.date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
