from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import func, select

from libs.core.auth.models import AuditLog
from libs.core.auth.schemas import CurrentActor
from libs.core.domains.schemas import (
    DnsRecordType,
    IPPoolCreateRequest,
    SESConfigurationSetCreateRequest,
)
from libs.core.errors import ConflictError, PermissionDeniedError

AuthTestContext = Any
UserFactory = Any


async def _create_actor(
    auth_user_factory: UserFactory,
    *,
    email: str,
    role: str,
) -> CurrentActor:
    user = await auth_user_factory(email=email, password="password-value-123", role=role)
    return CurrentActor(actor_type="user", user=user)


@pytest.mark.asyncio
async def test_create_domain_generates_expected_dns_records_and_audit(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin@dispatch.test", role="admin")
    detail = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name="mail.dispatch.test",
        dns_provider="manual",
        parent_domain="dispatch.test",
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn="arn:aws:sns:us-east-1:123456789012:test",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert detail.domain.default_configuration_set_id is not None
    assert detail.domain.verification_status == "pending"
    assert len(detail.dns_records) == 7
    assert {item.purpose for item in detail.dns_records} >= {"spf", "dkim", "dmarc", "mail_from"}

    async with auth_test_context.session_factory() as session:
        stmt = select(func.count()).select_from(AuditLog).where(AuditLog.action == "domain.create")
        result = await session.execute(stmt)
        assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_verify_domain_marks_records_and_domain_verified(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin2@dispatch.test", role="admin")
    created = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name="verify.dispatch.test",
        dns_provider="manual",
        parent_domain="dispatch.test",
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )

    for record in created.dns_records:
        auth_test_context.dns_adapter.set_record(
            record_type=DnsRecordType(record.record_type),
            name=record.name,
            values=[record.value],
        )

    verification = await auth_test_context.domain_service.verify_domain(
        actor=actor,
        domain_id=created.domain.id,
        ip_address=None,
        user_agent=None,
    )

    assert verification.fully_verified is True
    assert verification.domain.verification_status == "verified"
    assert verification.domain.spf_status == "verified"
    assert verification.domain.dkim_status == "verified"
    assert verification.domain.dmarc_status == "verified"
    assert verification.verified_records == verification.total_records


@pytest.mark.asyncio
async def test_retire_domain_blocks_future_verification(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin3@dispatch.test", role="admin")
    created = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name="retire.dispatch.test",
        dns_provider="manual",
        parent_domain="dispatch.test",
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )

    retired = await auth_test_context.domain_service.retire_domain(
        actor=actor,
        domain_id=created.domain.id,
        reason="reputation protection",
        ip_address=None,
        user_agent=None,
    )
    assert retired.domain.reputation_status == "retired"
    assert retired.domain.retired_at is not None

    with pytest.raises(ConflictError):
        await auth_test_context.domain_service.verify_domain(
            actor=actor,
            domain_id=created.domain.id,
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_domains(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="user@dispatch.test", role="user")
    with pytest.raises(PermissionDeniedError):
        await auth_test_context.domain_service.create_domain(
            actor=actor,
            name="blocked.dispatch.test",
            dns_provider="manual",
            parent_domain=None,
            ses_region="us-east-1",
            default_configuration_set_name=None,
            event_destination_sns_topic_arn=None,
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_configuration_set_and_ip_pool_management(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin4@dispatch.test", role="admin")
    created_set = await auth_test_context.domain_service.create_configuration_set(
        actor=actor,
        payload=SESConfigurationSetCreateRequest(
            name="outreach-default",
            ses_region="us-east-1",
            event_destination_sns_topic_arn="arn:aws:sns:us-east-1:123:test",
        ),
    )
    assert created_set.name == "outreach-default"

    pools_before = await auth_test_context.domain_service.list_ip_pools()
    created_pool = await auth_test_context.domain_service.create_ip_pool(
        actor=actor,
        payload=IPPoolCreateRequest(
            name="pool-a",
            ses_pool_name="ses-pool-a",
            dedicated_ips=["192.0.2.10", "192.0.2.11"],
            traffic_weight=100,
        ),
    )
    pools_after = await auth_test_context.domain_service.list_ip_pools()
    assert created_pool.name == "pool-a"
    assert len(pools_after) == len(pools_before) + 1


@pytest.mark.asyncio
async def test_verify_domain_system_path(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin5@dispatch.test", role="admin")
    created = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name="worker.dispatch.test",
        dns_provider="manual",
        parent_domain=None,
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )
    for record in created.dns_records:
        auth_test_context.dns_adapter.set_record(
            record_type=DnsRecordType(record.record_type),
            name=record.name,
            values=[record.value],
        )

    result = await auth_test_context.domain_service.verify_domain_system(created.domain.id)
    assert result.fully_verified is True

    async with auth_test_context.session_factory() as session:
        stmt = select(func.count()).select_from(AuditLog).where(AuditLog.action == "domain.verify")
        count = (await session.execute(stmt)).scalar_one()
        assert count >= 1


def test_expected_dns_record_builder_shapes_values(auth_test_context: AuthTestContext) -> None:
    records = auth_test_context.domain_service.build_expected_dns_records(
        domain_name="example.dispatch.test",
        parent_domain="dispatch.test",
        ses_region="us-east-1",
        mail_from_domain="mail.example.dispatch.test",
    )
    assert any(
        record.purpose == "dkim" and record.record_type is DnsRecordType.CNAME
        for record in records
    )
    assert any(
        record.purpose == "dmarc" and "v=dmarc1" in record.value.lower() for record in records
    )
    assert any(
        record.purpose == "mail_from" and record.record_type is DnsRecordType.MX
        for record in records
    )
    assert datetime.now(UTC)
