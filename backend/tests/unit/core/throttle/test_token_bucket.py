from __future__ import annotations

from dataclasses import dataclass

import pytest

from libs.core.config import Settings
from libs.core.throttle.token_bucket import (
    DomainTokenBucket,
    InMemoryTokenBucketMetricsRecorder,
)


@dataclass(slots=True)
class _Clock:
    current: float = 0.0

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


class _FailingRedisClient:
    async def script_load(self, script: str) -> str:
        _ = script
        raise RuntimeError("redis unavailable")

    async def evalsha(self, sha: str, numkeys: int, *keys_and_args: object) -> object:
        _ = (sha, numkeys, keys_and_args)
        raise RuntimeError("redis unavailable")


@pytest.mark.asyncio
async def test_token_bucket_fallback_limits_and_refills() -> None:
    settings = Settings(app_env="test")
    metrics = InMemoryTokenBucketMetricsRecorder()
    clock = _Clock()
    bucket = DomainTokenBucket(settings, metrics=metrics, now_seconds=clock.now)

    first = await bucket.try_take(domain_id="domain-a", capacity_per_hour=1)
    second = await bucket.try_take(domain_id="domain-a", capacity_per_hour=1)

    assert first.allowed is True
    assert second.allowed is False
    assert second.retry_after_seconds == 3600

    clock.advance(3600)
    third = await bucket.try_take(domain_id="domain-a", capacity_per_hour=1)
    assert third.allowed is True

    assert metrics.events[0].allowed is True
    assert metrics.events[1].allowed is False


@pytest.mark.asyncio
async def test_token_bucket_isolated_per_domain() -> None:
    settings = Settings(app_env="test")
    bucket = DomainTokenBucket(settings)

    first_a = await bucket.try_take(domain_id="domain-a", capacity_per_hour=1)
    first_b = await bucket.try_take(domain_id="domain-b", capacity_per_hour=1)
    second_a = await bucket.try_take(domain_id="domain-a", capacity_per_hour=1)

    assert first_a.allowed is True
    assert first_b.allowed is True
    assert second_a.allowed is False


@pytest.mark.asyncio
async def test_token_bucket_fail_closed_when_redis_unavailable() -> None:
    settings = Settings(
        app_env="local",
        throttle_fail_closed_retry_seconds=45,
    )
    bucket = DomainTokenBucket(settings, redis_client=_FailingRedisClient())

    decision = await bucket.try_take(domain_id="domain-a", capacity_per_hour=10)

    assert decision.allowed is False
    assert decision.retry_after_seconds == 45
