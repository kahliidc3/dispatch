from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from apps.workers.celery_app import celery_app
from libs.core.postmaster.service import get_postmaster_service
from libs.core.warmup.service import get_warmup_service


def _run_async[T](awaitable: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(awaitable)


@celery_app.task(name="warmup.compute_daily_budgets")
def compute_daily_budgets() -> dict[str, Any]:
    return _run_async(get_warmup_service().compute_daily_budgets())


@celery_app.task(name="warmup.check_graduation")
def check_graduation() -> dict[str, Any]:
    return _run_async(get_warmup_service().check_graduation())


@celery_app.task(name="warmup.fetch_postmaster_metrics")
def fetch_postmaster_metrics() -> dict[str, Any]:
    return _run_async(get_postmaster_service().fetch_all_domain_metrics())
