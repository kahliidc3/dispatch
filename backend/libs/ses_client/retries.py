from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable

from libs.ses_client.errors import SesMessageRejectedError, SesTransientError


async def run_with_retry[T](
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.25,
    max_delay_seconds: float = 3.0,
) -> T:
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    attempt = 0
    while True:
        attempt += 1
        try:
            return await operation()
        except SesMessageRejectedError:
            raise
        except SesTransientError:
            if attempt >= max_attempts:
                raise

            delay = min(base_delay_seconds * (2 ** (attempt - 1)), max_delay_seconds)
            jitter = random.uniform(0.0, delay * 0.2)
            await asyncio.sleep(delay + jitter)
