from __future__ import annotations

from time import perf_counter
from typing import Any

import pytest

from libs.core.auth.schemas import CurrentActor
from libs.core.suppression.schemas import SuppressionCreateRequest, SuppressionReasonCode
from libs.core.suppression.service import (
    RemoteSuppressedDestination,
    SuppressionService,
    SuppressionSyncAdapter,
)

AuthTestContext = Any
UserFactory = Any


class FakeSuppressionSyncAdapter(SuppressionSyncAdapter):
    def __init__(self) -> None:
        self.remote: dict[str, SuppressionReasonCode] = {}

    async def put_suppressed_destination(
        self,
        *,
        email: str,
        reason_code: SuppressionReasonCode,
    ) -> None:
        self.remote[email.strip().lower()] = reason_code

    async def get_suppressed_destination(self, *, email: str) -> RemoteSuppressedDestination | None:
        normalized = email.strip().lower()
        reason = self.remote.get(normalized)
        if reason is None:
            return None
        return RemoteSuppressedDestination(email=normalized, reason_code=reason)

    async def list_suppressed_destinations(
        self,
        *,
        page_size: int,
        next_token: str | None = None,
    ) -> tuple[list[RemoteSuppressedDestination], str | None]:
        ordered = sorted(self.remote.items())
        start = int(next_token or "0")
        chunk = ordered[start : start + page_size]
        next_cursor = str(start + page_size) if start + page_size < len(ordered) else None
        rows = [
            RemoteSuppressedDestination(email=email, reason_code=reason)
            for email, reason in chunk
        ]
        return rows, next_cursor

    async def delete_suppressed_destination(self, *, email: str) -> None:
        self.remote.pop(email.strip().lower(), None)


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email="suppression-sync-admin@dispatch.test",
        password="suppression-sync-password",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


@pytest.mark.asyncio
async def test_is_suppressed_returns_true_within_100ms_after_write(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    service = auth_test_context.suppression_service
    email = "quick-suppress@dispatch.test"

    await service.add_suppression(
        actor=actor,
        payload=SuppressionCreateRequest(
            email=email,
            reason_code="unsubscribe",
            source="unsubscribe_event",
            sync_to_ses=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    started = perf_counter()
    suppressed = await service.is_suppressed(email)
    elapsed = perf_counter() - started
    assert suppressed is True
    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_reconcile_with_ses_pulls_remote_and_keeps_local_consistent(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    sync_adapter = FakeSuppressionSyncAdapter()
    sync_adapter.remote["remote-ses-only@dispatch.test"] = "complaint"

    settings = auth_test_context.settings.model_copy(
        update={
            "suppression_ses_sync_enabled": True,
            "suppression_ses_sync_batch_size": 20,
            "suppression_ses_sync_pause_ms": 0,
            "suppression_ses_sync_max_records_per_run": 50,
        }
    )
    service = SuppressionService(settings, sync_adapter=sync_adapter)
    await service.add_suppression(
        actor=actor,
        payload=SuppressionCreateRequest(
            email="local-ses-only@dispatch.test",
            reason_code="manual",
            source="admin_api",
            sync_to_ses=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    summary = await service.reconcile_with_ses()
    assert summary.pushed_count >= 1
    assert summary.pulled_count >= 1
    assert summary.error_count == 0
    assert await service.is_suppressed("remote-ses-only@dispatch.test") is True
