from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from functools import lru_cache
from typing import Protocol, cast

from redis import asyncio as redis_async

from libs.core.auth.repository import AuthRepository
from libs.core.circuit_breaker.models import CircuitBreakerState
from libs.core.circuit_breaker.repository import CircuitBreakerRepository
from libs.core.config import Settings, get_settings
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.errors import ValidationError
from libs.core.logging import get_logger

logger = get_logger("core.circuit_breaker")

_ACCOUNT_SCOPE_ID = "00000000-0000-0000-0000-000000000000"
_KNOWN_STATES = {"closed", "open", "half_open"}

_THRESHOLDS: dict[str, tuple[Decimal, Decimal]] = {
    "domain": (Decimal("0.0150"), Decimal("0.0005")),
    "ip_pool": (Decimal("0.0150"), Decimal("0.0005")),
    "sender_profile": (Decimal("0.0200"), Decimal("0.0005")),
    "account": (Decimal("0.0100"), Decimal("0.0003")),
}


class _RedisClientProtocol(Protocol):
    async def get(self, key: str) -> object: ...

    async def setex(self, key: str, ttl: int, value: str) -> object: ...

    async def delete(self, key: str) -> object: ...


@dataclass(frozen=True, slots=True)
class CircuitBreakerEvaluationSummary:
    evaluated_scopes: int
    tripped: int
    moved_to_half_open: int
    closed: int


@dataclass(frozen=True, slots=True)
class CircuitBreakerTripParams:
    scope_type: str
    scope_id: str
    reason_code: str
    bounce_rate_24h: Decimal | None
    complaint_rate_24h: Decimal | None


class CircuitBreakerService:
    def __init__(
        self,
        settings: Settings,
        *,
        redis_client: _RedisClientProtocol | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = get_session_factory()
        self._cache_ttl_seconds = max(settings.circuit_breaker_cache_ttl_seconds, 1)
        self._auto_reset_after = timedelta(hours=max(settings.circuit_breaker_auto_reset_hours, 1))
        self._recheck_delay_seconds = max(settings.circuit_breaker_recheck_delay_seconds, 1)
        self._trip_consecutive_evaluations = max(
            settings.circuit_breaker_trip_consecutive_evaluations, 1
        )

        self._redis: _RedisClientProtocol | None = redis_client
        if self._redis is None and settings.app_env != "test":
            try:
                self._redis = cast(
                    _RedisClientProtocol,
                    redis_async.from_url(settings.redis_url, decode_responses=True),  # type: ignore[no-untyped-call]
                )
            except Exception:
                logger.warning("circuit_breaker.redis_init_failed")

        self._cache_fallback: dict[str, tuple[str, float]] = {}
        self._breach_streaks: dict[str, int] = {}

    @property
    def recheck_delay_seconds(self) -> int:
        return self._recheck_delay_seconds

    async def is_open(self, *, scope_type: str, scope_id: str) -> bool:
        normalized_scope_id = str(scope_id).strip()
        state = await self._get_cached_state(scope_type=scope_type, scope_id=normalized_scope_id)
        if state is None:
            return False
        if state not in _KNOWN_STATES:
            logger.warning(
                "circuit_breaker.unknown_state_fail_closed",
                scope_type=scope_type,
                scope_id=normalized_scope_id,
                state=state,
            )
            return True
        return state == "open"

    async def first_open_scope(
        self,
        *,
        scopes: list[tuple[str, str]],
    ) -> tuple[str, str] | None:
        for scope_type, scope_id in scopes:
            normalized_scope_id = str(scope_id).strip()
            if await self.is_open(scope_type=scope_type, scope_id=normalized_scope_id):
                return scope_type, normalized_scope_id
        return None

    async def trip(
        self,
        *,
        scope_type: str,
        scope_id: str,
        reason_code: str,
        bounce_rate_24h: Decimal | None,
        complaint_rate_24h: Decimal | None,
    ) -> CircuitBreakerState:
        params = CircuitBreakerTripParams(
            scope_type=scope_type,
            scope_id=scope_id,
            reason_code=reason_code,
            bounce_rate_24h=bounce_rate_24h,
            complaint_rate_24h=complaint_rate_24h,
        )
        async with UnitOfWork(self._session_factory) as uow:
            repo = CircuitBreakerRepository(uow.require_session())
            auth_repo = AuthRepository(uow.require_session())
            state = await self._trip_with_repositories(
                repo=repo,
                auth_repo=auth_repo,
                params=params,
            )
        await self._invalidate_cache(scope_type=scope_type, scope_id=scope_id)
        return state

    async def reset(
        self,
        *,
        scope_type: str,
        scope_id: str,
        actor_user_id: str,
        reason: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> CircuitBreakerState:
        clean_reason = reason.strip()
        if not clean_reason:
            raise ValidationError("Manual reset reason is required")

        async with UnitOfWork(self._session_factory) as uow:
            repo = CircuitBreakerRepository(uow.require_session())
            auth_repo = AuthRepository(uow.require_session())
            before = await repo.get_state(scope_type=scope_type, scope_id=scope_id)
            state = await repo.upsert_state(
                scope_type=scope_type,
                scope_id=scope_id,
                state="closed",
                bounce_rate_24h=None,
                complaint_rate_24h=None,
                tripped_reason=f"manual_reset:{clean_reason}",
                tripped_at=None,
                auto_reset_at=None,
                manually_reset_by=actor_user_id,
            )
            await auth_repo.write_audit_log(
                actor_type="user",
                actor_id=actor_user_id,
                action="circuit_breaker.reset",
                resource_type="circuit_breaker_state",
                resource_id=state.id,
                before_state=self._serialize_state(before),
                after_state=self._serialize_state(state),
                ip_address=ip_address,
                user_agent=user_agent,
            )

        self._breach_streaks.pop(self._scope_key(scope_type=scope_type, scope_id=scope_id), None)
        await self._invalidate_cache(scope_type=scope_type, scope_id=scope_id)
        logger.info(
            "circuit_breaker.reset",
            scope_type=scope_type,
            scope_id=scope_id,
            actor_user_id=actor_user_id,
        )
        return state

    async def evaluate_circuit_breakers(self) -> CircuitBreakerEvaluationSummary:
        touched_scope_keys: set[tuple[str, str]] = set()
        evaluated_scopes = 0
        tripped = 0
        moved_to_half_open = 0
        closed = 0
        now = datetime.now(UTC)

        async with UnitOfWork(self._session_factory) as uow:
            repo = CircuitBreakerRepository(uow.require_session())
            auth_repo = AuthRepository(uow.require_session())

            for scope_type in _THRESHOLDS:
                scope_ids = await repo.list_scope_ids(scope_type=scope_type)
                for scope_id in scope_ids:
                    evaluated_scopes += 1
                    metric = await repo.get_rolling_metric_24h(
                        scope_type=scope_type,
                        scope_id=scope_id,
                    )
                    bounce_rate = metric.bounce_rate if metric is not None else None
                    complaint_rate = metric.complaint_rate if metric is not None else None
                    breached, reason_code = self._is_threshold_breached(
                        scope_type=scope_type,
                        bounce_rate_24h=bounce_rate,
                        complaint_rate_24h=complaint_rate,
                    )
                    scope_key = self._scope_key(scope_type=scope_type, scope_id=scope_id)

                    state = await repo.get_state(scope_type=scope_type, scope_id=scope_id)
                    if state is None:
                        state = await repo.upsert_state(
                            scope_type=scope_type,
                            scope_id=scope_id,
                            state="closed",
                            bounce_rate_24h=bounce_rate,
                            complaint_rate_24h=complaint_rate,
                            tripped_reason=None,
                            tripped_at=None,
                            auto_reset_at=None,
                            manually_reset_by=None,
                        )

                    if state.state not in _KNOWN_STATES:
                        tripped += 1
                        params = CircuitBreakerTripParams(
                            scope_type=scope_type,
                            scope_id=scope_id,
                            reason_code="unknown_state",
                            bounce_rate_24h=bounce_rate,
                            complaint_rate_24h=complaint_rate,
                        )
                        state = await self._trip_with_repositories(
                            repo=repo,
                            auth_repo=auth_repo,
                            params=params,
                        )
                        touched_scope_keys.add((scope_type, scope_id))
                        self._breach_streaks.pop(scope_key, None)
                        continue

                    if state.state == "open":
                        auto_reset_at = (
                            self._coerce_utc(state.auto_reset_at)
                            if state.auto_reset_at is not None
                            else None
                        )
                        should_move_half_open = (
                            auto_reset_at is not None
                            and auto_reset_at <= self._coerce_utc(now)
                        )
                        if should_move_half_open:
                            state = await repo.upsert_state(
                                scope_type=scope_type,
                                scope_id=scope_id,
                                state="half_open",
                                bounce_rate_24h=bounce_rate,
                                complaint_rate_24h=complaint_rate,
                                tripped_reason="auto_transition_half_open",
                                tripped_at=state.tripped_at,
                                auto_reset_at=state.auto_reset_at,
                                manually_reset_by=None,
                            )
                            moved_to_half_open += 1
                            touched_scope_keys.add((scope_type, scope_id))
                        else:
                            await repo.upsert_state(
                                scope_type=scope_type,
                                scope_id=scope_id,
                                state="open",
                                bounce_rate_24h=bounce_rate,
                                complaint_rate_24h=complaint_rate,
                                tripped_reason=state.tripped_reason,
                                tripped_at=state.tripped_at,
                                auto_reset_at=state.auto_reset_at,
                                manually_reset_by=None,
                            )
                        continue

                    if state.state == "half_open":
                        if breached and reason_code is not None:
                            tripped += 1
                            params = CircuitBreakerTripParams(
                                scope_type=scope_type,
                                scope_id=scope_id,
                                reason_code=f"half_open_{reason_code}",
                                bounce_rate_24h=bounce_rate,
                                complaint_rate_24h=complaint_rate,
                            )
                            state = await self._trip_with_repositories(
                                repo=repo,
                                auth_repo=auth_repo,
                                params=params,
                            )
                            touched_scope_keys.add((scope_type, scope_id))
                        else:
                            before = state
                            state = await repo.upsert_state(
                                scope_type=scope_type,
                                scope_id=scope_id,
                                state="closed",
                                bounce_rate_24h=bounce_rate,
                                complaint_rate_24h=complaint_rate,
                                tripped_reason="auto_recovered",
                                tripped_at=None,
                                auto_reset_at=None,
                                manually_reset_by=None,
                            )
                            await auth_repo.write_audit_log(
                                actor_type="system",
                                actor_id=None,
                                action="circuit_breaker.auto_close",
                                resource_type="circuit_breaker_state",
                                resource_id=state.id,
                                before_state=self._serialize_state(before),
                                after_state=self._serialize_state(state),
                            )
                            closed += 1
                            touched_scope_keys.add((scope_type, scope_id))
                        self._breach_streaks.pop(scope_key, None)
                        continue

                    if breached and reason_code is not None:
                        streak = self._breach_streaks.get(scope_key, 0) + 1
                        self._breach_streaks[scope_key] = streak
                        if streak >= self._trip_consecutive_evaluations:
                            tripped += 1
                            params = CircuitBreakerTripParams(
                                scope_type=scope_type,
                                scope_id=scope_id,
                                reason_code=reason_code,
                                bounce_rate_24h=bounce_rate,
                                complaint_rate_24h=complaint_rate,
                            )
                            state = await self._trip_with_repositories(
                                repo=repo,
                                auth_repo=auth_repo,
                                params=params,
                            )
                            touched_scope_keys.add((scope_type, scope_id))
                            self._breach_streaks.pop(scope_key, None)
                    else:
                        self._breach_streaks.pop(scope_key, None)
                        await repo.upsert_state(
                            scope_type=scope_type,
                            scope_id=scope_id,
                            state="closed",
                            bounce_rate_24h=bounce_rate,
                            complaint_rate_24h=complaint_rate,
                            tripped_reason=None,
                            tripped_at=None,
                            auto_reset_at=None,
                            manually_reset_by=None,
                        )

        for scope_type, scope_id in touched_scope_keys:
            await self._invalidate_cache(scope_type=scope_type, scope_id=scope_id)

        logger.info(
            "circuit_breaker.evaluate_complete",
            evaluated_scopes=evaluated_scopes,
            tripped=tripped,
            moved_to_half_open=moved_to_half_open,
            closed=closed,
        )
        return CircuitBreakerEvaluationSummary(
            evaluated_scopes=evaluated_scopes,
            tripped=tripped,
            moved_to_half_open=moved_to_half_open,
            closed=closed,
        )

    async def _get_cached_state(self, *, scope_type: str, scope_id: str) -> str | None:
        key = self._cache_key(scope_type=scope_type, scope_id=scope_id)
        now_ts = datetime.now(UTC).timestamp()

        fallback_entry = self._cache_fallback.get(key)
        if fallback_entry is not None and fallback_entry[1] > now_ts:
            return fallback_entry[0]

        if self._settings.app_env == "test":
            state = await self._fetch_state_from_db(scope_type=scope_type, scope_id=scope_id)
            if state is not None:
                self._cache_fallback[key] = (state, now_ts + self._cache_ttl_seconds)
            else:
                self._cache_fallback.pop(key, None)
            return state

        if self._redis is None:
            logger.warning(
                "circuit_breaker.redis_unavailable_fail_closed",
                scope_type=scope_type,
                scope_id=scope_id,
            )
            return "open"

        try:
            cached = await self._redis.get(key)
            if isinstance(cached, str) and cached:
                self._cache_fallback[key] = (cached, now_ts + self._cache_ttl_seconds)
                return cached
            if isinstance(cached, bytes):
                decoded = cached.decode("utf-8").strip()
                if decoded:
                    self._cache_fallback[key] = (decoded, now_ts + self._cache_ttl_seconds)
                    return decoded
        except Exception as exc:
            logger.warning(
                "circuit_breaker.redis_read_failed_fail_closed",
                scope_type=scope_type,
                scope_id=scope_id,
                error=str(exc),
            )
            return "open"

        state = await self._fetch_state_from_db(scope_type=scope_type, scope_id=scope_id)
        if state is None:
            return None

        try:
            await self._redis.setex(key, self._cache_ttl_seconds, state)
            self._cache_fallback[key] = (state, now_ts + self._cache_ttl_seconds)
            return state
        except Exception as exc:
            logger.warning(
                "circuit_breaker.redis_write_failed_fail_closed",
                scope_type=scope_type,
                scope_id=scope_id,
                error=str(exc),
            )
            return "open"

    async def _fetch_state_from_db(self, *, scope_type: str, scope_id: str) -> str | None:
        try:
            async with UnitOfWork(self._session_factory) as uow:
                repo = CircuitBreakerRepository(uow.require_session())
                state = await repo.get_state(scope_type=scope_type, scope_id=scope_id)
                if state is None:
                    return None
                return state.state
        except Exception as exc:
            logger.warning(
                "circuit_breaker.db_read_failed_fail_closed",
                scope_type=scope_type,
                scope_id=scope_id,
                error=str(exc),
            )
            return "open"

    async def _invalidate_cache(self, *, scope_type: str, scope_id: str) -> None:
        key = self._cache_key(scope_type=scope_type, scope_id=scope_id)
        self._cache_fallback.pop(key, None)
        if self._redis is None:
            return
        try:
            await self._redis.delete(key)
        except Exception:
            logger.warning(
                "circuit_breaker.cache_invalidate_failed",
                scope_type=scope_type,
                scope_id=scope_id,
            )

    async def _trip_with_repositories(
        self,
        *,
        repo: CircuitBreakerRepository,
        auth_repo: AuthRepository,
        params: CircuitBreakerTripParams,
    ) -> CircuitBreakerState:
        now = datetime.now(UTC)
        before = await repo.get_state(scope_type=params.scope_type, scope_id=params.scope_id)
        state = await repo.upsert_state(
            scope_type=params.scope_type,
            scope_id=params.scope_id,
            state="open",
            bounce_rate_24h=params.bounce_rate_24h,
            complaint_rate_24h=params.complaint_rate_24h,
            tripped_reason=params.reason_code,
            tripped_at=now,
            auto_reset_at=now + self._auto_reset_after,
            manually_reset_by=None,
        )

        threshold_bounce, threshold_complaint = _THRESHOLDS[params.scope_type]
        breach_metric = (
            "bounce_rate_24h"
            if (params.bounce_rate_24h or Decimal("0")) >= threshold_bounce
            else "complaint_rate_24h"
        )
        observed_value = (
            params.bounce_rate_24h
            if breach_metric == "bounce_rate_24h"
            else params.complaint_rate_24h
        )
        expected_value = (
            threshold_bounce
            if breach_metric == "bounce_rate_24h"
            else threshold_complaint
        )
        severity = "critical" if params.scope_type == "account" else "warning"

        await repo.create_anomaly_alert(
            scope_type=params.scope_type,
            scope_id=params.scope_id,
            metric=breach_metric,
            severity=severity,
            message=(
                f"circuit breaker tripped for {params.scope_type}:{params.scope_id} "
                f"reason={params.reason_code}"
            ),
            observed_value=observed_value,
            expected_value=expected_value,
        )
        await auth_repo.write_audit_log(
            actor_type="system",
            actor_id=None,
            action="circuit_breaker.trip",
            resource_type="circuit_breaker_state",
            resource_id=state.id,
            before_state=self._serialize_state(before),
            after_state=self._serialize_state(state),
        )

        logger.warning(
            "circuit_breaker.tripped",
            scope_type=params.scope_type,
            scope_id=params.scope_id,
            reason_code=params.reason_code,
            bounce_rate_24h=params.bounce_rate_24h,
            complaint_rate_24h=params.complaint_rate_24h,
        )
        if params.scope_type == "account":
            logger.error(
                "circuit_breaker.account_trip_pager",
                scope_id=params.scope_id,
                reason_code=params.reason_code,
            )
        return state

    @staticmethod
    def _serialize_state(state: CircuitBreakerState | None) -> dict[str, object] | None:
        if state is None:
            return None
        return {
            "id": state.id,
            "scope_type": state.scope_type,
            "scope_id": state.scope_id,
            "state": state.state,
            "bounce_rate_24h": (
                str(state.bounce_rate_24h) if state.bounce_rate_24h is not None else None
            ),
            "complaint_rate_24h": (
                str(state.complaint_rate_24h) if state.complaint_rate_24h is not None else None
            ),
            "tripped_at": state.tripped_at.isoformat() if state.tripped_at is not None else None,
            "tripped_reason": state.tripped_reason,
            "auto_reset_at": (
                state.auto_reset_at.isoformat() if state.auto_reset_at is not None else None
            ),
            "manually_reset_by": state.manually_reset_by,
        }

    @staticmethod
    def _is_threshold_breached(
        *,
        scope_type: str,
        bounce_rate_24h: Decimal | None,
        complaint_rate_24h: Decimal | None,
    ) -> tuple[bool, str | None]:
        threshold_bounce, threshold_complaint = _THRESHOLDS[scope_type]
        if bounce_rate_24h is not None and bounce_rate_24h >= threshold_bounce:
            return True, "bounce_threshold"
        if complaint_rate_24h is not None and complaint_rate_24h >= threshold_complaint:
            return True, "complaint_threshold"
        return False, None

    @staticmethod
    def account_scope_id() -> str:
        return _ACCOUNT_SCOPE_ID

    @staticmethod
    def _cache_key(*, scope_type: str, scope_id: str) -> str:
        return f"cb:state:{scope_type}:{scope_id}"

    @staticmethod
    def _scope_key(*, scope_type: str, scope_id: str) -> str:
        return f"{scope_type}:{scope_id}"

    @staticmethod
    def _coerce_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


@lru_cache(maxsize=1)
def get_circuit_breaker_service() -> CircuitBreakerService:
    return CircuitBreakerService(get_settings())


def reset_circuit_breaker_service_cache() -> None:
    get_circuit_breaker_service.cache_clear()
