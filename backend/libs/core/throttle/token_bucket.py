from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol, cast

from redis import asyncio as redis_async

from libs.core.config import Settings, get_settings
from libs.core.logging import get_logger

logger = get_logger("core.throttle")

_DAILY_CAP_LUA = """
local key = KEYS[1]
local daily_limit = tonumber(ARGV[1])
local ttl_seconds = tonumber(ARGV[2])

local count = redis.call("INCR", key)
if count == 1 then
    redis.call("EXPIRE", key, ttl_seconds)
end

if count > daily_limit then
    redis.call("DECR", key)
    return {0, count - 1}
end

return {1, daily_limit - count}
"""

_TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate_per_sec = tonumber(ARGV[2])
local now_ms = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])
local ttl_seconds = tonumber(ARGV[5])

local state = redis.call("HMGET", key, "tokens", "ts_ms")
local tokens = tonumber(state[1])
local last_ms = tonumber(state[2])

if tokens == nil then
    tokens = capacity
end
if last_ms == nil then
    last_ms = now_ms
end

local elapsed_ms = now_ms - last_ms
if elapsed_ms < 0 then
    elapsed_ms = 0
end

tokens = math.min(capacity, tokens + (elapsed_ms / 1000.0) * refill_rate_per_sec)

local allowed = 0
local retry_after_seconds = 0

if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
else
    local deficit = requested - tokens
    retry_after_seconds = math.ceil(deficit / refill_rate_per_sec)
end

redis.call("HMSET", key, "tokens", tokens, "ts_ms", now_ms)
redis.call("EXPIRE", key, ttl_seconds)

return {allowed, retry_after_seconds, math.floor(tokens)}
"""


@dataclass(frozen=True, slots=True)
class DailyCapDecision:
    allowed: bool
    tokens_remaining: int | None


@dataclass(frozen=True, slots=True)
class TokenBucketDecision:
    allowed: bool
    retry_after_seconds: int
    tokens_remaining: int | None


@dataclass(frozen=True, slots=True)
class TokenBucketMetricEvent:
    domain_id: str
    allowed: bool
    retry_after_seconds: int
    tokens_remaining: int | None
    source: str


class TokenBucketMetricsRecorder(Protocol):
    def record(
        self,
        *,
        domain_id: str,
        allowed: bool,
        retry_after_seconds: int,
        tokens_remaining: int | None,
        source: str,
    ) -> None: ...


class NoopTokenBucketMetricsRecorder:
    def record(
        self,
        *,
        domain_id: str,
        allowed: bool,
        retry_after_seconds: int,
        tokens_remaining: int | None,
        source: str,
    ) -> None:
        _ = (domain_id, allowed, retry_after_seconds, tokens_remaining, source)


@dataclass(slots=True)
class InMemoryTokenBucketMetricsRecorder:
    events: list[TokenBucketMetricEvent] = field(default_factory=list)

    def record(
        self,
        *,
        domain_id: str,
        allowed: bool,
        retry_after_seconds: int,
        tokens_remaining: int | None,
        source: str,
    ) -> None:
        self.events.append(
            TokenBucketMetricEvent(
                domain_id=domain_id,
                allowed=allowed,
                retry_after_seconds=retry_after_seconds,
                tokens_remaining=tokens_remaining,
                source=source,
            )
        )


@dataclass(slots=True)
class _FallbackBucketState:
    tokens: float
    timestamp_seconds: float


class _RedisTokenBucketClient(Protocol):
    async def script_load(self, script: str) -> str: ...

    async def evalsha(self, sha: str, numkeys: int, *keys_and_args: object) -> object: ...


class DomainTokenBucket:
    def __init__(
        self,
        settings: Settings,
        *,
        redis_client: _RedisTokenBucketClient | None = None,
        metrics: TokenBucketMetricsRecorder | None = None,
        now_seconds: Callable[[], float] | None = None,
    ) -> None:
        self._settings = settings
        self._redis_client = redis_client or cast(
            _RedisTokenBucketClient,
            redis_async.from_url(settings.redis_url, decode_responses=True),  # type: ignore[no-untyped-call]
        )
        self._metrics = metrics or NoopTokenBucketMetricsRecorder()
        self._now_seconds = now_seconds or time.time
        self._script_sha: str | None = None
        self._daily_cap_sha: str | None = None
        self._fallback_buckets: dict[str, _FallbackBucketState] = {}
        self._fallback_daily_counters: dict[str, int] = {}

    async def try_take(
        self,
        *,
        domain_id: str,
        capacity_per_hour: int,
        requested_tokens: int = 1,
    ) -> TokenBucketDecision:
        normalized_domain_id = domain_id.strip()
        if not normalized_domain_id:
            return self._record_and_return(
                domain_id="unknown",
                decision=TokenBucketDecision(
                    allowed=False,
                    retry_after_seconds=max(self._settings.throttle_fail_closed_retry_seconds, 1),
                    tokens_remaining=None,
                ),
                source="invalid_domain",
            )

        capacity = max(capacity_per_hour, 1)
        requested = max(requested_tokens, 1)
        refill_rate_per_sec = capacity / 3600.0

        if self._settings.app_env == "test":
            decision = self._try_take_fallback(
                domain_id=normalized_domain_id,
                capacity=capacity,
                requested=requested,
                refill_rate_per_sec=refill_rate_per_sec,
            )
            return self._record_and_return(
                domain_id=normalized_domain_id,
                decision=decision,
                source="fallback",
            )

        try:
            decision = await self._try_take_redis(
                domain_id=normalized_domain_id,
                capacity=capacity,
                requested=requested,
                refill_rate_per_sec=refill_rate_per_sec,
            )
            return self._record_and_return(
                domain_id=normalized_domain_id,
                decision=decision,
                source="redis",
            )
        except Exception as exc:
            logger.warning(
                "throttle.redis_unavailable_fail_closed",
                domain_id=normalized_domain_id,
                error=str(exc),
            )
            decision = TokenBucketDecision(
                allowed=False,
                retry_after_seconds=max(self._settings.throttle_fail_closed_retry_seconds, 1),
                tokens_remaining=None,
            )
            return self._record_and_return(
                domain_id=normalized_domain_id,
                decision=decision,
                source="redis_error",
            )

    async def try_take_daily(
        self,
        *,
        domain_id: str,
        daily_limit: int,
    ) -> DailyCapDecision:
        """Atomically check and increment a domain's daily send counter.

        Returns allowed=False once the counter reaches daily_limit. The counter
        expires automatically at the configured TTL (one day) so it resets each day.
        Only called for domains in warmup_stage='warming'.
        """
        if daily_limit <= 0:
            return DailyCapDecision(allowed=True, tokens_remaining=None)

        normalized = domain_id.strip().lower()
        if not normalized:
            return DailyCapDecision(allowed=False, tokens_remaining=None)

        if self._settings.app_env == "test":
            return self._try_take_daily_fallback(domain_id=normalized, daily_limit=daily_limit)

        try:
            return await self._try_take_daily_redis(
                domain_id=normalized, daily_limit=daily_limit
            )
        except Exception as exc:
            logger.warning(
                "throttle.daily_cap_redis_error",
                domain_id=normalized,
                error=str(exc),
            )
            return DailyCapDecision(allowed=False, tokens_remaining=None)

    def _try_take_daily_fallback(
        self, *, domain_id: str, daily_limit: int
    ) -> DailyCapDecision:
        key = f"daily:{domain_id}"
        current = self._fallback_daily_counters.get(key, 0)
        if current >= daily_limit:
            return DailyCapDecision(allowed=False, tokens_remaining=0)
        self._fallback_daily_counters[key] = current + 1
        return DailyCapDecision(allowed=True, tokens_remaining=daily_limit - (current + 1))

    async def _try_take_daily_redis(
        self, *, domain_id: str, daily_limit: int
    ) -> DailyCapDecision:
        if self._daily_cap_sha is None:
            self._daily_cap_sha = await self._redis_client.script_load(_DAILY_CAP_LUA)

        from datetime import UTC, datetime

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        key = f"throttle:daily:{domain_id}:{today}"
        ttl = self._settings.throttle_bucket_ttl_seconds
        raw = await self._redis_client.evalsha(
            self._daily_cap_sha, 1, key, str(daily_limit), str(ttl)
        )
        if not isinstance(raw, list) or len(raw) != 2:
            raise RuntimeError("Unexpected daily cap Lua response")
        allowed = int(raw[0]) == 1
        remaining = int(raw[1])
        return DailyCapDecision(allowed=allowed, tokens_remaining=max(remaining, 0))

    def reset_daily_counters(self) -> None:
        """Test helper to clear all in-memory daily counters."""
        self._fallback_daily_counters.clear()

    @staticmethod
    def queue_key_for_domain(domain_id: str) -> str:
        return f"throttle:domain:{domain_id.strip().lower()}"

    async def _try_take_redis(
        self,
        *,
        domain_id: str,
        capacity: int,
        requested: int,
        refill_rate_per_sec: float,
    ) -> TokenBucketDecision:
        if self._script_sha is None:
            self._script_sha = await self._redis_client.script_load(_TOKEN_BUCKET_LUA)

        now_ms = int(self._now_seconds() * 1000)
        key = self.queue_key_for_domain(domain_id)
        args: tuple[object, ...] = (
            key,
            str(capacity),
            f"{refill_rate_per_sec:.10f}",
            str(now_ms),
            str(requested),
            str(self._settings.throttle_bucket_ttl_seconds),
        )
        raw = await self._redis_client.evalsha(self._script_sha, 1, *args)
        return self._parse_script_result(raw)

    def _try_take_fallback(
        self,
        *,
        domain_id: str,
        capacity: int,
        requested: int,
        refill_rate_per_sec: float,
    ) -> TokenBucketDecision:
        now = self._now_seconds()
        key = self.queue_key_for_domain(domain_id)
        state = self._fallback_buckets.get(key)
        if state is None:
            state = _FallbackBucketState(tokens=float(capacity), timestamp_seconds=now)
            self._fallback_buckets[key] = state

        elapsed = max(0.0, now - state.timestamp_seconds)
        state.tokens = min(float(capacity), state.tokens + elapsed * refill_rate_per_sec)
        state.timestamp_seconds = now

        if state.tokens >= requested:
            state.tokens -= requested
            return TokenBucketDecision(
                allowed=True,
                retry_after_seconds=0,
                tokens_remaining=max(int(state.tokens), 0),
            )

        deficit = requested - state.tokens
        retry_after_seconds = int(math.ceil(deficit / refill_rate_per_sec))
        return TokenBucketDecision(
            allowed=False,
            retry_after_seconds=max(retry_after_seconds, 1),
            tokens_remaining=max(int(state.tokens), 0),
        )

    @staticmethod
    def _parse_script_result(raw: object) -> TokenBucketDecision:
        if not isinstance(raw, list) or len(raw) != 3:
            raise RuntimeError("Unexpected token bucket Lua response format")

        allowed_raw = int(raw[0])
        retry_raw = int(raw[1])
        remaining_raw = int(raw[2])
        return TokenBucketDecision(
            allowed=allowed_raw == 1,
            retry_after_seconds=max(retry_raw, 0),
            tokens_remaining=max(remaining_raw, 0),
        )

    def _record_and_return(
        self,
        *,
        domain_id: str,
        decision: TokenBucketDecision,
        source: str,
    ) -> TokenBucketDecision:
        self._metrics.record(
            domain_id=domain_id,
            allowed=decision.allowed,
            retry_after_seconds=decision.retry_after_seconds,
            tokens_remaining=decision.tokens_remaining,
            source=source,
        )
        return decision


@lru_cache(maxsize=1)
def get_domain_token_bucket() -> DomainTokenBucket:
    return DomainTokenBucket(get_settings())


def reset_domain_token_bucket_cache() -> None:
    get_domain_token_bucket.cache_clear()
