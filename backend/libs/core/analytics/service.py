from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from functools import lru_cache
from typing import cast

from redis import asyncio as redis_async

from libs.core.analytics.repository import (
    CAMPAIGN_WINDOWS,
    DOMAIN_WINDOWS,
    AnalyticsRepository,
)
from libs.core.config import Settings, get_settings
from libs.core.db.pagination import CursorPage, decode_cursor, encode_cursor
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.errors import NotFoundError
from libs.core.events.models import RollingMetric
from libs.core.logging import get_logger

logger = get_logger("core.analytics")

_CACHE_TTL_SECONDS = 60
_MESSAGE_PAGE_LIMIT_MAX = 200


@dataclass(slots=True, frozen=True)
class RollingWindowStats:
    window: str
    sends: int
    deliveries: int
    bounces: int
    complaints: int
    opens: int
    clicks: int
    bounce_rate: Decimal | None
    complaint_rate: Decimal | None
    window_end: datetime


@dataclass(slots=True, frozen=True)
class CampaignAnalyticsResult:
    campaign_id: str
    campaign_name: str
    status: str
    total_sent: int
    total_delivered: int
    total_bounced: int
    total_complained: int
    total_opened: int
    total_clicked: int
    total_replied: int
    total_unsubscribed: int
    rolling_windows: list[RollingWindowStats]
    last_updated_at: datetime


@dataclass(slots=True, frozen=True)
class DomainAnalyticsResult:
    domain_id: str
    domain_name: str
    reputation_status: str
    circuit_breaker_state: str | None
    rolling_windows: list[RollingWindowStats]
    last_updated_at: datetime


@dataclass(slots=True, frozen=True)
class TopCampaignStats:
    campaign_id: str
    name: str
    sends_today: int
    delivered: int


@dataclass(slots=True, frozen=True)
class TopFailingDomainStats:
    domain_id: str
    name: str
    bounce_rate: Decimal | None
    circuit_breaker_state: str | None


@dataclass(slots=True, frozen=True)
class OverviewResult:
    sends_today: int
    sends_7d: int
    top_campaigns: list[TopCampaignStats]
    top_failing_domains: list[TopFailingDomainStats]
    last_updated_at: datetime


def _to_rolling_window_stats(metric: RollingMetric) -> RollingWindowStats:
    return RollingWindowStats(
        window=metric.window,
        sends=metric.sends,
        deliveries=metric.deliveries,
        bounces=metric.bounces,
        complaints=metric.complaints,
        opens=metric.opens,
        clicks=metric.clicks,
        bounce_rate=metric.bounce_rate,
        complaint_rate=metric.complaint_rate,
        window_end=metric.window_end,
    )


class AnalyticsService:
    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self._settings = settings
        self._session_factory = get_session_factory()
        self._redis: redis_async.Redis | None = None
        try:
            self._redis = cast(
                redis_async.Redis,
                redis_async.from_url(settings.redis_url, decode_responses=True),  # type: ignore[no-untyped-call]
            )
        except Exception:
            logger.warning("analytics.redis_init_failed")

    async def is_ready(self) -> bool:
        async with UnitOfWork(self._session_factory) as uow:
            repo = AnalyticsRepository(uow.require_session())
            return await repo.database_ready()

    async def get_campaign_analytics(self, *, campaign_id: str) -> CampaignAnalyticsResult:
        cache_key = f"analytics:campaign:{campaign_id}"
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        async with UnitOfWork(self._session_factory) as uow:
            repo = AnalyticsRepository(uow.require_session())
            campaign = await repo.get_campaign(campaign_id=campaign_id)
            if campaign is None:
                raise NotFoundError(f"Campaign {campaign_id} not found")
            metrics = await repo.get_rolling_metrics(
                scope_type="campaign",
                scope_id=campaign_id,
                windows=CAMPAIGN_WINDOWS,
            )

        rolling = [_to_rolling_window_stats(m) for m in metrics]
        result = CampaignAnalyticsResult(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            status=campaign.status,
            total_sent=campaign.total_sent,
            total_delivered=campaign.total_delivered,
            total_bounced=campaign.total_bounced,
            total_complained=campaign.total_complained,
            total_opened=campaign.total_opened,
            total_clicked=campaign.total_clicked,
            total_replied=campaign.total_replied,
            total_unsubscribed=campaign.total_unsubscribed,
            rolling_windows=rolling,
            last_updated_at=datetime.now(UTC),
        )
        await self._set_cached(cache_key, result)
        return result

    async def get_domain_analytics(self, *, domain_id: str) -> DomainAnalyticsResult:
        cache_key = f"analytics:domain:{domain_id}"
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        async with UnitOfWork(self._session_factory) as uow:
            repo = AnalyticsRepository(uow.require_session())
            domain = await repo.get_domain(domain_id=domain_id)
            if domain is None:
                raise NotFoundError(f"Domain {domain_id} not found")
            metrics = await repo.get_rolling_metrics(
                scope_type="domain",
                scope_id=domain_id,
                windows=DOMAIN_WINDOWS,
            )
            circuit_breaker_state = await repo.get_circuit_breaker_state(
                scope_type="domain",
                scope_id=domain_id,
            )

        rolling = [_to_rolling_window_stats(m) for m in metrics]
        result = DomainAnalyticsResult(
            domain_id=domain.id,
            domain_name=domain.name,
            reputation_status=domain.reputation_status,
            circuit_breaker_state=circuit_breaker_state,
            rolling_windows=rolling,
            last_updated_at=datetime.now(UTC),
        )
        await self._set_cached(cache_key, result)
        return result

    async def get_overview(self) -> OverviewResult:
        cache_key = "analytics:overview"
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        async with UnitOfWork(self._session_factory) as uow:
            repo = AnalyticsRepository(uow.require_session())
            today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            seven_days_start = AnalyticsRepository.window_start("7d")

            sends_today = await repo.count_sends_in_window(since=today_start)
            sends_7d = await repo.count_sends_in_window(since=seven_days_start)

            top_campaign_rows = await repo.list_top_campaigns_by_sends_today(limit=5)
            top_failing_rows = await repo.list_top_failing_domains(window="24h", limit=5)
            top_failing_states: dict[str, str | None] = {}
            for domain, _ in top_failing_rows:
                top_failing_states[domain.id] = await repo.get_circuit_breaker_state(
                    scope_type="domain",
                    scope_id=domain.id,
                )

        top_campaigns = [
            TopCampaignStats(
                campaign_id=c.id,
                name=c.name,
                sends_today=sends,
                delivered=c.total_delivered,
            )
            for c, sends in top_campaign_rows
        ]
        top_failing = [
            TopFailingDomainStats(
                domain_id=d.id,
                name=d.name,
                bounce_rate=m.bounce_rate if m is not None else None,
                circuit_breaker_state=top_failing_states.get(d.id),
            )
            for d, m in top_failing_rows
        ]
        result = OverviewResult(
            sends_today=sends_today,
            sends_7d=sends_7d,
            top_campaigns=top_campaigns,
            top_failing_domains=top_failing,
            last_updated_at=datetime.now(UTC),
        )
        await self._set_cached(cache_key, result)
        return result

    async def list_campaign_messages(
        self,
        *,
        campaign_id: str,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[dict[str, object]]:
        limit = min(limit, _MESSAGE_PAGE_LIMIT_MAX)
        decoded_cursor = decode_cursor(cursor) if cursor else None

        async with UnitOfWork(self._session_factory) as uow:
            repo = AnalyticsRepository(uow.require_session())
            campaign = await repo.get_campaign(campaign_id=campaign_id)
            if campaign is None:
                raise NotFoundError(f"Campaign {campaign_id} not found")
            rows = await repo.list_campaign_messages(
                campaign_id=campaign_id,
                limit=limit,
                cursor=decoded_cursor,
            )

        has_more = len(rows) > limit
        page = rows[:limit]
        next_cursor = encode_cursor(page[-1].created_at, page[-1].id) if has_more and page else None
        items = [
            {
                "message_id": m.id,
                "to_email": m.to_email,
                "status": m.status,
                "created_at": m.created_at,
                "sent_at": m.sent_at,
                "delivered_at": m.delivered_at,
                "bounce_type": m.bounce_type,
                "complaint_type": m.complaint_type,
            }
            for m in page
        ]
        return CursorPage(items=items, next_cursor=next_cursor)

    async def rollup_campaign_metrics(self) -> dict[str, int]:
        async with UnitOfWork(self._session_factory) as uow:
            repo = AnalyticsRepository(uow.require_session())
            campaign_ids = await repo.get_active_campaign_ids()
            updated = 0
            for campaign_id in campaign_ids:
                for window in CAMPAIGN_WINDOWS:
                    since = AnalyticsRepository.window_start(window)
                    window_end = datetime.now(UTC)
                    counts = await repo.aggregate_campaign_window(
                        campaign_id=campaign_id, since=since
                    )
                    await repo.upsert_rolling_metric(
                        scope_type="campaign",
                        scope_id=campaign_id,
                        window=window,
                        window_end=window_end,
                        counts=counts,
                    )
                    updated += 1
        logger.info("analytics.campaign_rollup_done", campaigns=len(campaign_ids), rows=updated)
        return {"campaigns": len(campaign_ids), "rows_upserted": updated}

    async def rollup_domain_metrics(self) -> dict[str, int]:
        async with UnitOfWork(self._session_factory) as uow:
            repo = AnalyticsRepository(uow.require_session())
            domain_ids = await repo.get_verified_domain_ids()
            updated = 0
            for domain_id in domain_ids:
                for window in DOMAIN_WINDOWS:
                    since = AnalyticsRepository.window_start(window)
                    window_end = datetime.now(UTC)
                    counts = await repo.aggregate_domain_window(
                        domain_id=domain_id, since=since
                    )
                    await repo.upsert_rolling_metric(
                        scope_type="domain",
                        scope_id=domain_id,
                        window=window,
                        window_end=window_end,
                        counts=counts,
                    )
                    updated += 1
        logger.info("analytics.domain_rollup_done", domains=len(domain_ids), rows=updated)
        return {"domains": len(domain_ids), "rows_upserted": updated}

    async def rollup_account_metrics(self) -> dict[str, int]:
        account_scope_id = "00000000-0000-0000-0000-000000000000"
        account_windows = ["24h", "7d"]
        async with UnitOfWork(self._session_factory) as uow:
            repo = AnalyticsRepository(uow.require_session())
            for window in account_windows:
                since = AnalyticsRepository.window_start(window)
                window_end = datetime.now(UTC)
                counts = await repo.aggregate_account_window(since=since)
                await repo.upsert_rolling_metric(
                    scope_type="account",
                    scope_id=account_scope_id,
                    window=window,
                    window_end=window_end,
                    counts=counts,
                )
        logger.info("analytics.account_rollup_done")
        return {"rows_upserted": len(account_windows)}

    async def _get_cached(self, key: str) -> object | None:
        if self._redis is None:
            return None
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            return None

    async def _set_cached(self, key: str, value: object) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.setex(key, _CACHE_TTL_SECONDS, json.dumps(value, default=str))
        except Exception:
            pass


@lru_cache(maxsize=1)
def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(settings=get_settings())


def reset_analytics_service_cache() -> None:
    get_analytics_service.cache_clear()
