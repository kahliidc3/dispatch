from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from apps.workers.celery_app import celery_app
from libs.core.imports.schemas import ImportRunSummary
from libs.core.imports.service import get_import_service


def _run_async[T](awaitable: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(awaitable)


@celery_app.task(name="imports.run_import")  # type: ignore[untyped-decorator]
def run_import(job_id: str) -> dict[str, Any]:
    result: ImportRunSummary = _run_async(
        get_import_service().run_import_job(job_id=job_id),
    )
    return result.model_dump()
