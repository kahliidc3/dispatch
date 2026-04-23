from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from apps.workers.celery_app import celery_app
from libs.core.domains.service import DomainVerificationResult, get_domain_service


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
