from __future__ import annotations

from uuid import uuid4

import pytest
from redis import asyncio as redis_async

from libs.core.config import Settings
from libs.core.throttle.token_bucket import DomainTokenBucket


@pytest.mark.asyncio
async def test_token_bucket_redis_denies_after_capacity_exhausted() -> None:
    settings = Settings(app_env="local", redis_url="redis://localhost:6379/0")
    redis = redis_async.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]

    try:
        try:
            await redis.ping()
        except Exception:
            pytest.skip("Redis is not available on localhost:6379")

        bucket = DomainTokenBucket(settings, redis_client=redis)
        domain_id = f"redis-throttle-{uuid4().hex}"
        key = bucket.queue_key_for_domain(domain_id)

        await redis.delete(key)
        first = await bucket.try_take(domain_id=domain_id, capacity_per_hour=1)
        second = await bucket.try_take(domain_id=domain_id, capacity_per_hour=1)

        assert first.allowed is True
        assert second.allowed is False
        assert second.retry_after_seconds > 0
    finally:
        await redis.aclose()
