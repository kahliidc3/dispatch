from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache

from libs.core.config import Settings, get_settings
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain
from libs.core.errors import NotFoundError
from libs.core.logging import get_logger
from libs.core.warmup.repository import WarmupRepository
from libs.core.warmup.schemas import (
    GRADUATION_CLEAN_DAYS,
    WARMUP_BOUNCE_RATE_THRESHOLD,
    WARMUP_COMPLAINT_RATE_THRESHOLD,
    WARMUP_EXTENSION_DAYS,
    WarmupSchedule,
    custom_warmup_schedule,
    default_warmup_schedule,
)

logger = get_logger("core.warmup")


@dataclass(slots=True, frozen=True)
class DailyBudgetResult:
    domain_id: str
    domain_name: str
    day: int
    budget: int


@dataclass(slots=True, frozen=True)
class GraduationResult:
    domain_id: str
    domain_name: str
    graduated: bool
    extended: bool
    extended_days: int


class WarmupService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._session_factory = get_session_factory()

    async def start_warmup(
        self,
        *,
        domain_id: str,
        schedule_volumes: list[int] | None = None,
    ) -> Domain:
        """Enrol a domain in warmup and set the initial daily budget."""
        schedule = (
            custom_warmup_schedule(schedule_volumes)
            if schedule_volumes
            else default_warmup_schedule()
        )
        now = datetime.now(UTC)
        first_budget = schedule.budget_for_day(1)

        async with UnitOfWork(self._session_factory) as uow:
            repo = WarmupRepository(uow.require_session())
            domain = await repo.get_domain(domain_id=domain_id)
            if domain is None:
                raise NotFoundError(f"Domain {domain_id} not found")

            await repo.update_domain_warmup(
                domain_id=domain_id,
                values={
                    "warmup_stage": "warming",
                    "warmup_schedule": schedule.volumes,
                    "warmup_started_at": now,
                    "warmup_completed_at": None,
                    "daily_send_limit": first_budget,
                },
            )
            refreshed = await repo.get_domain(domain_id=domain_id)
            if refreshed is None:
                raise NotFoundError(f"Domain {domain_id} not found")
            logger.info(
                "warmup.started",
                domain_id=domain_id,
                domain_name=refreshed.name,
                schedule_days=schedule.total_days(),
                day1_budget=first_budget,
            )
            return refreshed

    async def compute_daily_budgets(self) -> dict[str, object]:
        """Nightly task: update daily_send_limit for every warming domain."""
        updated: list[DailyBudgetResult] = []

        async with UnitOfWork(self._session_factory) as uow:
            repo = WarmupRepository(uow.require_session())
            domains = await repo.list_warming_domains()

            for domain in domains:
                if domain.warmup_started_at is None:
                    continue

                schedule = self._schedule_from_domain(domain)
                day = WarmupRepository.warmup_day_number(domain.warmup_started_at)
                budget = schedule.budget_for_day(day)

                await repo.update_domain_warmup(
                    domain_id=domain.id,
                    values={"daily_send_limit": budget},
                )
                updated.append(
                    DailyBudgetResult(
                        domain_id=domain.id,
                        domain_name=domain.name,
                        day=day,
                        budget=budget,
                    )
                )
                logger.info(
                    "warmup.budget_computed",
                    domain_id=domain.id,
                    domain_name=domain.name,
                    day=day,
                    budget=budget,
                )

        return {"domains_updated": len(updated), "budgets": [dataclasses.asdict(r) for r in updated]}

    async def check_graduation(self) -> dict[str, object]:
        """Daily task: graduate domains that passed the schedule with clean metrics,
        or extend warmup for domains with bad signals."""
        results: list[GraduationResult] = []

        async with UnitOfWork(self._session_factory) as uow:
            repo = WarmupRepository(uow.require_session())
            domains = await repo.list_warming_domains()

            for domain in domains:
                if domain.warmup_started_at is None:
                    continue

                schedule = self._schedule_from_domain(domain)
                day = WarmupRepository.warmup_day_number(domain.warmup_started_at)

                metric = await repo.get_24h_rolling_metric(domain_id=domain.id)
                bounce_rate = float(metric.bounce_rate) if metric and metric.bounce_rate else 0.0
                complaint_rate = (
                    float(metric.complaint_rate) if metric and metric.complaint_rate else 0.0
                )

                health_ok = (
                    bounce_rate <= WARMUP_BOUNCE_RATE_THRESHOLD
                    and complaint_rate <= WARMUP_COMPLAINT_RATE_THRESHOLD
                )

                if not health_ok:
                    new_days = len(schedule.volumes) + WARMUP_EXTENSION_DAYS
                    extended_volumes = list(schedule.volumes) + [
                        schedule.volumes[-1]
                    ] * WARMUP_EXTENSION_DAYS
                    await repo.update_domain_warmup(
                        domain_id=domain.id,
                        values={"warmup_schedule": extended_volumes},
                    )
                    logger.warning(
                        "warmup.extended",
                        domain_id=domain.id,
                        domain_name=domain.name,
                        bounce_rate=bounce_rate,
                        complaint_rate=complaint_rate,
                        extended_by_days=WARMUP_EXTENSION_DAYS,
                    )
                    results.append(
                        GraduationResult(
                            domain_id=domain.id,
                            domain_name=domain.name,
                            graduated=False,
                            extended=True,
                            extended_days=WARMUP_EXTENSION_DAYS,
                        )
                    )
                    continue

                if day >= schedule.total_days() + GRADUATION_CLEAN_DAYS:
                    await repo.update_domain_warmup(
                        domain_id=domain.id,
                        values={
                            "warmup_stage": "graduated",
                            "warmup_completed_at": datetime.now(UTC),
                            "daily_send_limit": 0,
                        },
                    )
                    logger.info(
                        "warmup.graduated",
                        domain_id=domain.id,
                        domain_name=domain.name,
                        day=day,
                    )
                    results.append(
                        GraduationResult(
                            domain_id=domain.id,
                            domain_name=domain.name,
                            graduated=True,
                            extended=False,
                            extended_days=0,
                        )
                    )

        graduated = sum(1 for r in results if r.graduated)
        extended = sum(1 for r in results if r.extended)
        return {
            "graduated": graduated,
            "extended": extended,
        }

    async def extend_warmup(self, *, domain_id: str, extra_days: int) -> Domain:
        """Manually extend a warming domain's schedule."""
        if extra_days <= 0:
            raise ValueError("extra_days must be positive")

        async with UnitOfWork(self._session_factory) as uow:
            repo = WarmupRepository(uow.require_session())
            domain = await repo.get_domain(domain_id=domain_id)
            if domain is None:
                raise NotFoundError(f"Domain {domain_id} not found")
            if domain.warmup_stage != "warming":
                raise ValueError(f"Domain {domain_id} is not in warming stage")

            schedule = self._schedule_from_domain(domain)
            last_vol = schedule.volumes[-1] if schedule.volumes else 0
            extended = list(schedule.volumes) + [last_vol] * extra_days

            await repo.update_domain_warmup(
                domain_id=domain_id,
                values={"warmup_schedule": extended},
            )
            refreshed = await repo.get_domain(domain_id=domain_id)
            if refreshed is None:
                raise NotFoundError(f"Domain {domain_id} not found")

            logger.info(
                "warmup.manually_extended",
                domain_id=domain_id,
                extra_days=extra_days,
            )
            return refreshed

    @staticmethod
    def _schedule_from_domain(domain: Domain) -> WarmupSchedule:
        raw = domain.warmup_schedule
        volumes = raw if isinstance(raw, list) and raw else []
        if not volumes:
            return default_warmup_schedule()
        return custom_warmup_schedule([int(v) for v in volumes])


@lru_cache(maxsize=1)
def get_warmup_service() -> WarmupService:
    return WarmupService(settings=get_settings())


def reset_warmup_service_cache() -> None:
    get_warmup_service.cache_clear()
