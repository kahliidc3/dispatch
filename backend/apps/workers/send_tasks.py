from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

from apps.workers.celery_app import celery_app
from libs.core.campaigns.service import MessageSendResult, get_campaign_service
from libs.ses_client.errors import SesTransientError


def _run_async[T](awaitable: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(awaitable)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="send.send_message",
    autoretry_for=(SesTransientError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_message(
    message_id: str,
    domain_id: str | None = None,
    domain_name: str | None = None,
) -> dict[str, Any]:
    result: MessageSendResult = _run_async(
        get_campaign_service().send_queued_message(message_id=message_id),
    )

    retry_after = result.retry_after_seconds
    if result.error_code in {"rate_limited_domain", "circuit_open"} and retry_after is not None:
        next_kwargs: dict[str, str] = {"message_id": result.message_id}
        effective_domain_id = result.domain_id or domain_id
        effective_domain_name = result.domain_name or domain_name
        if effective_domain_id:
            next_kwargs["domain_id"] = effective_domain_id
        if effective_domain_name:
            next_kwargs["domain_name"] = effective_domain_name

        celery_app.send_task(
            "send.send_message",
            kwargs=next_kwargs,
            countdown=max(retry_after, 1),
        )

    return {
        "message_id": result.message_id,
        "status": result.status,
        "ses_message_id": result.ses_message_id,
        "error_code": result.error_code,
        "error_message": result.error_message,
        "retry_after_seconds": result.retry_after_seconds,
        "domain_id": result.domain_id or domain_id,
        "domain_name": result.domain_name or domain_name,
    }
