from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from apps.workers.celery_app import celery_app
from libs.core.domains.provisioning import DomainProvisioningStatus
from libs.core.domains.service import get_domain_service


def _run_async[T](awaitable: Coroutine[Any, Any, T]) -> T:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    # Async tests can invoke task callables directly under a running loop.
    # Run the coroutine in a dedicated thread to preserve sync task semantics.
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, awaitable).result()


@celery_app.task(  # type: ignore[untyped-decorator]
    name="domains.provision_domain",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def provision_domain(domain_id: str, run_id: str | None = None) -> dict[str, object]:
    status: DomainProvisioningStatus = _run_async(
        get_domain_service().provision_domain_system(domain_id=domain_id, run_id=run_id)
    )
    return {
        "domain_id": status.domain_id,
        "run_id": status.run_id,
        "status": status.status,
        "reason_code": status.reason_code,
        "started_at": status.started_at.isoformat() if status.started_at else None,
        "completed_at": status.completed_at.isoformat() if status.completed_at else None,
        "steps": [step.to_dict() for step in status.steps],
    }
