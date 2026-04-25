from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import func, select

from libs.core.auth.models import AuditLog
from libs.core.auth.schemas import CurrentActor
from libs.core.contacts.schemas import ContactCreateRequest, ContactQueryParams
from libs.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationError

AuthTestContext = Any
UserFactory = Any


def _csv_bytes(content: str) -> bytes:
    return content.encode("utf-8")


async def _create_actor(
    auth_user_factory: UserFactory,
    *,
    email: str,
    role: str,
) -> CurrentActor:
    user = await auth_user_factory(email=email, password="password-value-123", role=role)
    return CurrentActor(actor_type="user", user=user)


@pytest.mark.asyncio
async def test_create_import_job_guards_and_limits(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-imports@dispatch.test",
        role="admin",
    )
    user_actor = await _create_actor(
        auth_user_factory,
        email="user-imports@dispatch.test",
        role="user",
    )

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.import_service.create_import_job(
            actor=user_actor,
            file_name="contacts.csv",
            file_bytes=_csv_bytes("email\none@example.com\n"),
            source_label=None,
            target_list_id=None,
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(ValidationError):
        await auth_test_context.import_service.create_import_job(
            actor=admin_actor,
            file_name="contacts.csv",
            file_bytes=b"",
            source_label=None,
            target_list_id=None,
            ip_address=None,
            user_agent=None,
        )

    for _ in range(3):
        await auth_test_context.import_service.create_import_job(
            actor=admin_actor,
            file_name="contacts.csv",
            file_bytes=_csv_bytes("email\none@example.com\n"),
            source_label="seed",
            target_list_id=None,
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(ConflictError):
        await auth_test_context.import_service.create_import_job(
            actor=admin_actor,
            file_name="contacts.csv",
            file_bytes=_csv_bytes("email\none@example.com\n"),
            source_label=None,
            target_list_id=None,
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_run_import_applies_gates_and_is_idempotent(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-run-import@dispatch.test",
        role="admin",
    )

    existing_contact = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="existing@good.com",
            first_name="Before",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )
    auth_test_context.mx_lookup.set_result(domain="good.com", has_mx=True)
    auth_test_context.mx_lookup.set_result(domain="nomx.test", has_mx=False)

    csv_content = (
        "email,first_name,last_name\n"
        "valid@good.com,Valid,One\n"
        "invalid-email,Bad,Format\n"
        "nomx@nomx.test,No,Mx\n"
        "info@good.com,Role,Account\n"
        "valid@good.com,Dupe,Row\n"
        "existing@good.com,After,Upsert\n"
    )
    created_job = await auth_test_context.import_service.create_import_job(
        actor=actor,
        file_name="seed.csv",
        file_bytes=_csv_bytes(csv_content),
        source_label="csv_seed",
        target_list_id=None,
        ip_address=None,
        user_agent=None,
    )

    summary = await auth_test_context.import_service.run_import_job(job_id=created_job.id)
    assert summary.status == "complete"
    assert summary.total_rows == 6
    assert summary.valid_rows == 2
    assert summary.invalid_rows == 2
    assert summary.suppressed_rows == 1
    assert summary.duplicate_rows == 1
    assert summary.rows_per_second > 0

    rerun = await auth_test_context.import_service.run_import_job(job_id=created_job.id)
    assert rerun.status == "complete"
    assert rerun.rows_per_second == 0
    assert rerun.total_rows == 6

    all_contacts = await auth_test_context.contact_service.list_contacts(
        actor=actor,
        query=ContactQueryParams(limit=100, offset=0),
    )
    emails = {item.email for item in all_contacts.items}
    assert "valid@good.com" in emails
    assert "existing@good.com" in emails

    existing_after = await auth_test_context.contact_service.get_contact(
        actor=actor,
        contact_id=existing_contact.id,
    )
    assert existing_after.first_name == "After"
    assert existing_after.last_name == "Upsert"

    details = await auth_test_context.import_service.get_import_job(
        actor=actor,
        job_id=created_job.id,
    )
    assert details.rejected_rows == 4
    assert len(details.sample_error_rows) >= 3

    async with auth_test_context.session_factory() as session:
        complete_audits_stmt = select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "import.job.complete"
        )
        complete_audits = (await session.execute(complete_audits_stmt)).scalar_one()
        assert complete_audits >= 1


@pytest.mark.asyncio
async def test_import_missing_required_column_fails_job(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-missing-column@dispatch.test",
        role="admin",
    )
    created_job = await auth_test_context.import_service.create_import_job(
        actor=actor,
        file_name="missing-email.csv",
        file_bytes=_csv_bytes("first_name,last_name\nA,B\n"),
        source_label=None,
        target_list_id=None,
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(ValidationError):
        await auth_test_context.import_service.run_import_job(job_id=created_job.id)

    failed_details = await auth_test_context.import_service.get_import_job(
        actor=actor,
        job_id=created_job.id,
    )
    assert failed_details.status == "failed"
    assert failed_details.error_message is not None

    with pytest.raises(NotFoundError):
        await auth_test_context.import_service.get_import_job(actor=actor, job_id="missing-job-id")
