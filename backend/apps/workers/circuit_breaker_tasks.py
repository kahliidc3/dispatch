from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from apps.workers.celery_app import celery_app
from libs.core.circuit_breaker.service import (
    CircuitBreakerEvaluationSummary,
    get_circuit_breaker_service,
)


def _run_async[T](awaitable: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(awaitable)


@celery_app.task(name="circuit_breakers.evaluate")  # type: ignore[untyped-decorator]
def evaluate_circuit_breakers() -> dict[str, int]:
    result: CircuitBreakerEvaluationSummary = _run_async(
        get_circuit_breaker_service().evaluate_circuit_breakers()
    )
    return {
        "evaluated_scopes": result.evaluated_scopes,
        "tripped": result.tripped,
        "moved_to_half_open": result.moved_to_half_open,
        "closed": result.closed,
    }
