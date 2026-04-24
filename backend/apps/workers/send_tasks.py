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
def send_message(message_id: str) -> dict[str, Any]:
    result: MessageSendResult = _run_async(
        get_campaign_service().send_queued_message(message_id=message_id),
    )
    return {
        "message_id": result.message_id,
        "status": result.status,
        "ses_message_id": result.ses_message_id,
        "error_code": result.error_code,
        "error_message": result.error_message,
    }
