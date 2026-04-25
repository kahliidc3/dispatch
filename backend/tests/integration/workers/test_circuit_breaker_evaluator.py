from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from apps.workers.circuit_breaker_tasks import evaluate_circuit_breakers
from libs.core.circuit_breaker.models import AnomalyAlert, CircuitBreakerState
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain
from libs.core.events.models import RollingMetric

AuthTestContext = Any


async def _seed_domain_with_breach_metric(auth_test_context: AuthTestContext) -> str:
    unique = uuid4().hex[:8]
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        domain = Domain(
            name=f"cb-eval-{unique}.dispatch.test",
            verification_status="verified",
            spf_status="verified",
            dkim_status="verified",
            dmarc_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()

        metric = RollingMetric(
            scope_type="domain",
            scope_id=domain.id,
            window="24h",
            window_end=datetime.now(UTC),
            sends=100,
            deliveries=98,
            bounces=2,
            complaints=0,
            opens=0,
            clicks=0,
            replies=0,
            unsubscribes=0,
            bounce_rate=Decimal("0.0200"),
            complaint_rate=Decimal("0.0000"),
            updated_at=datetime.now(UTC),
        )
        uow.require_session().add(metric)
        await uow.require_session().flush()
        return domain.id


def test_circuit_breaker_evaluator_trips_within_one_cycle(
    auth_test_context: AuthTestContext,
) -> None:
    domain_id = asyncio.run(_seed_domain_with_breach_metric(auth_test_context))

    result = evaluate_circuit_breakers()
    assert result["tripped"] >= 1

    async def _assert_state() -> None:
        async with UnitOfWork(auth_test_context.session_factory) as uow:
            state = (
                await uow.require_session().execute(
                    CircuitBreakerState.__table__.select()
                    .where(CircuitBreakerState.scope_type == "domain")
                    .where(CircuitBreakerState.scope_id == domain_id)
                )
            ).mappings().first()
            alert = (
                await uow.require_session().execute(
                    AnomalyAlert.__table__.select()
                    .where(AnomalyAlert.scope_type == "domain")
                    .where(AnomalyAlert.scope_id == domain_id)
                )
            ).mappings().first()
            assert state is not None
            assert state["state"] == "open"
            assert alert is not None

    asyncio.run(_assert_state())
