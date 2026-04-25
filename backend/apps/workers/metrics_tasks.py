from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from apps.workers.celery_app import celery_app
from libs.core.analytics.service import get_analytics_service


def _run_async[T](awaitable: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(awaitable)


@celery_app.task(name="metrics.rollup_campaign_metrics")  # type: ignore[untyped-decorator]
def rollup_campaign_metrics() -> dict[str, int]:
    return _run_async(get_analytics_service().rollup_campaign_metrics())


@celery_app.task(name="metrics.rollup_domain_metrics")  # type: ignore[untyped-decorator]
def rollup_domain_metrics() -> dict[str, int]:
    return _run_async(get_analytics_service().rollup_domain_metrics())


@celery_app.task(name="metrics.rollup_account_metrics")  # type: ignore[untyped-decorator]
def rollup_account_metrics() -> dict[str, int]:
    return _run_async(get_analytics_service().rollup_account_metrics())
