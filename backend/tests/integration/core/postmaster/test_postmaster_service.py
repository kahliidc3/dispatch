from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain
from libs.core.postmaster.models import PostmasterMetric
from libs.core.postmaster.repository import PostmasterRepository
from libs.core.postmaster.schemas import PostmasterAdapter, PostmasterDomainData
from libs.core.postmaster.service import PostmasterService

AuthTestContext = Any


class FakePostmasterAdapter:
    """Adapter that returns fixed data for any domain."""

    def __init__(self, reputation: str = "HIGH") -> None:
        self._reputation = reputation
        self.call_count = 0

    async def fetch_domain_reputation(
        self,
        *,
        domain_name: str,
        report_date: date,
    ) -> PostmasterDomainData:
        self.call_count += 1
        return PostmasterDomainData(
            domain_reputation=self._reputation,
            spam_rate=Decimal("0.000100"),
            dkim_success_ratio=Decimal("0.9990"),
            spf_success_ratio=Decimal("0.9985"),
            dmarc_success_ratio=Decimal("0.9975"),
            inbound_encryption_ratio=Decimal("1.0000"),
            raw_json={"domain": domain_name, "date": str(report_date)},
        )


async def _seed_verified_domain(ctx: AuthTestContext) -> Domain:
    unique = uuid4().hex[:8]
    async with UnitOfWork(ctx.session_factory) as uow:
        domain = Domain(
            name=f"pm-{unique}.dispatch.test",
            verification_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()
        return domain


@pytest.mark.asyncio
async def test_fetch_stores_expected_fields(
    auth_test_context: AuthTestContext,
) -> None:
    domain = await _seed_verified_domain(auth_test_context)
    adapter = FakePostmasterAdapter(reputation="HIGH")
    service = PostmasterService(auth_test_context.settings, adapter=adapter)

    report_date = date(2026, 4, 24)
    result = await service.fetch_domain_metrics(
        domain_id=domain.id,
        domain_name=domain.name,
        report_date=report_date,
    )

    assert result.stored is True
    assert result.domain_reputation == "HIGH"
    assert result.report_date == report_date

    async with auth_test_context.session_factory() as session:
        repo = PostmasterRepository(session)
        metrics = await repo.list_metrics_for_domain(domain_id=domain.id)

    assert len(metrics) == 1
    m = metrics[0]
    assert m.domain_reputation == "HIGH"
    assert m.spam_rate == Decimal("0.000100")
    assert m.dkim_success_ratio == Decimal("0.9990")
    assert m.date == report_date


@pytest.mark.asyncio
async def test_fetch_is_idempotent_on_same_day(
    auth_test_context: AuthTestContext,
) -> None:
    domain = await _seed_verified_domain(auth_test_context)
    adapter = FakePostmasterAdapter(reputation="MEDIUM")
    service = PostmasterService(auth_test_context.settings, adapter=adapter)

    report_date = date(2026, 4, 24)

    await service.fetch_domain_metrics(
        domain_id=domain.id,
        domain_name=domain.name,
        report_date=report_date,
    )
    await service.fetch_domain_metrics(
        domain_id=domain.id,
        domain_name=domain.name,
        report_date=report_date,
    )

    async with auth_test_context.session_factory() as session:
        repo = PostmasterRepository(session)
        metrics = await repo.list_metrics_for_domain(domain_id=domain.id)

    assert len(metrics) == 1


@pytest.mark.asyncio
async def test_fetch_all_domain_metrics_covers_verified_domains(
    auth_test_context: AuthTestContext,
) -> None:
    domain_a = await _seed_verified_domain(auth_test_context)
    domain_b = await _seed_verified_domain(auth_test_context)

    adapter = FakePostmasterAdapter(reputation="LOW")
    service = PostmasterService(auth_test_context.settings, adapter=adapter)

    report_date = date(2026, 4, 24)
    result = await service.fetch_all_domain_metrics(report_date=report_date)

    assert result["metrics_stored"] >= 2


@pytest.mark.asyncio
async def test_fetch_gracefully_handles_adapter_error(
    auth_test_context: AuthTestContext,
) -> None:
    class FailingAdapter:
        async def fetch_domain_reputation(
            self, *, domain_name: str, report_date: date
        ) -> PostmasterDomainData:
            raise RuntimeError("API unavailable")

    domain = await _seed_verified_domain(auth_test_context)
    service = PostmasterService(auth_test_context.settings, adapter=FailingAdapter())

    result = await service.fetch_domain_metrics(
        domain_id=domain.id,
        domain_name=domain.name,
        report_date=date(2026, 4, 24),
    )

    assert result.stored is False

    async with auth_test_context.session_factory() as session:
        repo = PostmasterRepository(session)
        metrics = await repo.list_metrics_for_domain(domain_id=domain.id)

    assert len(metrics) == 0
