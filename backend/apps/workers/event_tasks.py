from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from apps.workers.celery_app import celery_app
from libs.core.domains.service import DomainVerificationResult, get_domain_service
from libs.core.events.schemas import EventProcessResult
from libs.core.events.service import get_event_service
from libs.core.suppression.schemas import SuppressionSesSyncSummary
from libs.core.suppression.service import get_suppression_service


def _run_async[T](awaitable: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(awaitable)


@celery_app.task(name="domains.verify_domain_dns")  # type: ignore[untyped-decorator]
def verify_domain_dns(domain_id: str) -> dict[str, Any]:
    result: DomainVerificationResult = _run_async(
        get_domain_service().verify_domain_system(domain_id),
    )
    return {
        "domain_id": result.domain.id,
        "fully_verified": result.fully_verified,
        "verified_records": result.verified_records,
        "total_records": result.total_records,
    }


@celery_app.task(name="suppression.reconcile_with_ses")  # type: ignore[untyped-decorator]
def reconcile_suppression_with_ses() -> dict[str, int]:
    result: SuppressionSesSyncSummary = _run_async(
        get_suppression_service().reconcile_with_ses(),
    )
    return result.model_dump()


@celery_app.task(name="events.process_event")  # type: ignore[untyped-decorator]
def process_event(payload: dict[str, object]) -> dict[str, object]:
    result: EventProcessResult = _run_async(
        get_event_service().process_ses_event(payload=payload),
    )
    return result.model_dump(mode="json")
