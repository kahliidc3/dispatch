from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import lru_cache

from libs.core.config import Settings, get_settings
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.logging import get_logger
from libs.core.postmaster.models import PostmasterMetric
from libs.core.postmaster.repository import PostmasterRepository
from libs.core.postmaster.schemas import NoopPostmasterAdapter, PostmasterAdapter

logger = get_logger("core.postmaster")


@dataclass(slots=True, frozen=True)
class PostmasterFetchResult:
    domain_id: str
    domain_name: str
    report_date: date
    stored: bool
    domain_reputation: str | None


class PostmasterService:
    def __init__(
        self,
        settings: Settings,
        *,
        adapter: PostmasterAdapter | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = get_session_factory()
        self._adapter: PostmasterAdapter = adapter or NoopPostmasterAdapter()

    async def fetch_all_domain_metrics(
        self,
        *,
        report_date: date | None = None,
    ) -> dict[str, object]:
        """Fetch yesterday's Postmaster data for all verified domains."""
        effective_date = report_date or datetime.now(UTC).date()
        results: list[PostmasterFetchResult] = []

        async with UnitOfWork(self._session_factory) as uow:
            repo = PostmasterRepository(uow.require_session())
            domains = await repo.list_verified_domains()

            for domain in domains:
                result = await self._fetch_and_store(
                    repo=repo,
                    domain_id=domain.id,
                    domain_name=domain.name,
                    report_date=effective_date,
                )
                results.append(result)

        stored = sum(1 for r in results if r.stored)
        logger.info(
            "postmaster.fetch_complete",
            domains_checked=len(results),
            metrics_stored=stored,
            report_date=str(effective_date),
        )
        return {"domains_checked": len(results), "metrics_stored": stored}

    async def fetch_domain_metrics(
        self,
        *,
        domain_id: str,
        domain_name: str,
        report_date: date | None = None,
    ) -> PostmasterFetchResult:
        """Fetch Postmaster data for a single domain."""
        effective_date = report_date or datetime.now(UTC).date()
        async with UnitOfWork(self._session_factory) as uow:
            repo = PostmasterRepository(uow.require_session())
            return await self._fetch_and_store(
                repo=repo,
                domain_id=domain_id,
                domain_name=domain_name,
                report_date=effective_date,
            )

    async def list_metrics(
        self,
        *,
        domain_id: str,
        limit: int = 30,
    ) -> list[PostmasterMetric]:
        async with self._session_factory() as session:
            repo = PostmasterRepository(session)
            return await repo.list_metrics_for_domain(domain_id=domain_id, limit=limit)

    async def _fetch_and_store(
        self,
        *,
        repo: PostmasterRepository,
        domain_id: str,
        domain_name: str,
        report_date: date,
    ) -> PostmasterFetchResult:
        try:
            data = await self._adapter.fetch_domain_reputation(
                domain_name=domain_name,
                report_date=report_date,
            )
        except Exception as exc:
            logger.warning(
                "postmaster.fetch_failed",
                domain_id=domain_id,
                domain_name=domain_name,
                error=str(exc),
            )
            return PostmasterFetchResult(
                domain_id=domain_id,
                domain_name=domain_name,
                report_date=report_date,
                stored=False,
                domain_reputation=None,
            )

        metric = PostmasterMetric(
            domain_id=domain_id,
            date=report_date,
            domain_reputation=data.domain_reputation,
            spam_rate=data.spam_rate,
            dkim_success_ratio=data.dkim_success_ratio,
            spf_success_ratio=data.spf_success_ratio,
            dmarc_success_ratio=data.dmarc_success_ratio,
            inbound_encryption_ratio=data.inbound_encryption_ratio,
            raw_json=data.raw_json,
            fetched_at=datetime.now(UTC),
        )
        await repo.upsert_metric(metric=metric)

        logger.info(
            "postmaster.metric_stored",
            domain_id=domain_id,
            domain_name=domain_name,
            report_date=str(report_date),
            reputation=data.domain_reputation,
        )
        return PostmasterFetchResult(
            domain_id=domain_id,
            domain_name=domain_name,
            report_date=report_date,
            stored=True,
            domain_reputation=data.domain_reputation,
        )


@lru_cache(maxsize=1)
def get_postmaster_service() -> PostmasterService:
    return PostmasterService(settings=get_settings())


def reset_postmaster_service_cache() -> None:
    get_postmaster_service.cache_clear()
