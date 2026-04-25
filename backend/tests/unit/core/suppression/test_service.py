from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import func, select

from libs.core.auth.models import AuditLog
from libs.core.auth.schemas import CurrentActor
from libs.core.errors import RateLimitedError
from libs.core.suppression.schemas import (
    SuppressionCreateRequest,
    SuppressionQueryParams,
    SuppressionReasonCode,
)
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
        self.put_calls: list[tuple[str, SuppressionReasonCode]] = []
        self.deleted_calls: list[str] = []

    async def put_suppressed_destination(
        self,
        *,
        email: str,
        reason_code: SuppressionReasonCode,
    ) -> None:
        normalized = email.strip().lower()
        self.remote[normalized] = reason_code
        self.put_calls.append((normalized, reason_code))

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
        new_next = str(start + page_size) if start + page_size < len(ordered) else None
        rows = [RemoteSuppressedDestination(email=item[0], reason_code=item[1]) for item in chunk]
        return rows, new_next

    async def delete_suppressed_destination(self, *, email: str) -> None:
        normalized = email.strip().lower()
        self.remote.pop(normalized, None)
        self.deleted_calls.append(normalized)


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email="suppression-admin@dispatch.test",
        password="suppression-password-value",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


@pytest.mark.asyncio
async def test_add_list_get_and_is_suppressed(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    service = auth_test_context.suppression_service

    added = await service.add_suppression(
        actor=actor,
        payload=SuppressionCreateRequest(
            email="supp-service-one@dispatch.test",
            reason_code="manual",
            source="admin_panel",
            notes="manual block for investigation",
            sync_to_ses=False,
        ),
        ip_address=None,
        user_agent=None,
    )
    assert service.to_reason_code(added) == "manual"
    assert service.to_source(added) == "admin_panel"

    assert await service.is_suppressed("supp-service-one@dispatch.test") is True

    fetched = await service.get_suppression(actor=actor, email="supp-service-one@dispatch.test")
    assert fetched.id == added.id

    result = await service.list_suppressions(
        actor=actor,
        query=SuppressionQueryParams(limit=10, offset=0),
    )
    assert result.total >= 1
    assert any(item.id == added.id for item in result.items)


@pytest.mark.asyncio
async def test_removal_rate_limit_and_audit(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    service = auth_test_context.suppression_service

    for email in (
        "supp-remove-one@dispatch.test",
        "supp-remove-two@dispatch.test",
        "supp-remove-three@dispatch.test",
    ):
        await service.add_suppression(
            actor=actor,
            payload=SuppressionCreateRequest(
                email=email,
                reason_code="manual",
                source="admin_panel",
                sync_to_ses=False,
            ),
            ip_address=None,
            user_agent=None,
        )

    await service.remove_suppression(
        actor=actor,
        email="supp-remove-one@dispatch.test",
        justification="False positive removal approved by admin",
        ip_address=None,
        user_agent=None,
        sync_to_ses=False,
    )
    await service.remove_suppression(
        actor=actor,
        email="supp-remove-two@dispatch.test",
        justification="Case reviewed and restored",
        ip_address=None,
        user_agent=None,
        sync_to_ses=False,
    )

    with pytest.raises(RateLimitedError):
        await service.remove_suppression(
            actor=actor,
            email="supp-remove-three@dispatch.test",
            justification="Third removal must be rate limited",
            ip_address=None,
            user_agent=None,
            sync_to_ses=False,
        )

    async with auth_test_context.session_factory() as session:
        stmt = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == "suppression.remove")
        )
        removals_audited = int((await session.execute(stmt)).scalar_one())
    assert removals_audited == 2


@pytest.mark.asyncio
async def test_bulk_import_handles_invalid_and_duplicate_rows(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    service = auth_test_context.suppression_service

    csv_bytes = (
        b"email\n"
        b"bulk-one@dispatch.test\n"
        b"invalid-email\n"
        b"bulk-two@dispatch.test\n"
        b"bulk-one@dispatch.test\n"
        b"\n"
    )
    summary = await service.bulk_import_csv(
        actor=actor,
        csv_bytes=csv_bytes,
        reason_code="role_account",
        source="csv_upload",
        ip_address=None,
        user_agent=None,
        sync_to_ses=False,
    )
    assert summary.total_rows == 4
    assert summary.imported_count == 2
    assert summary.skipped_count == 1
    assert summary.invalid_count == 1

    entry = await service.get_suppression(actor=actor, email="bulk-one@dispatch.test")
    assert service.to_reason_code(entry) == "role_account"
    assert service.to_source(entry) == "csv_upload"


@pytest.mark.asyncio
async def test_reconcile_with_ses_pushes_and_pulls(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    sync_adapter = FakeSuppressionSyncAdapter()
    sync_adapter.remote["remote-only@dispatch.test"] = "complaint"

    settings = auth_test_context.settings.model_copy(
        update={
            "suppression_ses_sync_enabled": True,
            "suppression_ses_sync_batch_size": 25,
            "suppression_ses_sync_pause_ms": 0,
            "suppression_ses_sync_max_records_per_run": 100,
        }
    )
    service = SuppressionService(settings, sync_adapter=sync_adapter)
    await service.add_suppression(
        actor=actor,
        payload=SuppressionCreateRequest(
            email="local-only@dispatch.test",
            reason_code="manual",
            source="admin_panel",
            sync_to_ses=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    summary = await service.reconcile_with_ses()
    assert summary.pushed_count >= 1
    assert summary.pulled_count >= 1
    assert summary.scanned_remote_count >= 1
    assert summary.error_count == 0
    assert await service.is_suppressed("remote-only@dispatch.test") is True
    assert any(item[0] == "local-only@dispatch.test" for item in sync_adapter.put_calls)
