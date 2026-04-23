from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import update

from libs.core.auth.schemas import CurrentActor
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import DomainDnsRecord
from libs.core.domains.schemas import IPPoolCreateRequest, SESConfigurationSetCreateRequest
from libs.core.domains.service import DomainService, get_domain_service, reset_domain_service_cache
from libs.core.errors import ConflictError, NotFoundError, ValidationError

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
async def test_create_domain_validation_and_duplicate_paths(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-branches@dispatch.test",
        role="admin",
    )

    with pytest.raises(ValidationError):
        await auth_test_context.domain_service.create_domain(
            actor=actor,
            name="same.dispatch.test",
            dns_provider="manual",
            parent_domain="same.dispatch.test",
            ses_region="us-east-1",
            default_configuration_set_name=None,
            event_destination_sns_topic_arn=None,
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(ValidationError):
        await auth_test_context.domain_service.create_domain(
            actor=actor,
            name="provider.dispatch.test",
            dns_provider="dnsimple",
            parent_domain=None,
            ses_region="us-east-1",
            default_configuration_set_name=None,
            event_destination_sns_topic_arn=None,
            ip_address=None,
            user_agent=None,
        )

    await auth_test_context.domain_service.create_domain(
        actor=actor,
        name="dupe.dispatch.test",
        dns_provider="manual",
        parent_domain=None,
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )
    with pytest.raises(ConflictError):
        await auth_test_context.domain_service.create_domain(
            actor=actor,
            name="dupe.dispatch.test",
            dns_provider="manual",
            parent_domain=None,
            ses_region="us-east-1",
            default_configuration_set_name=None,
            event_destination_sns_topic_arn=None,
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_domain_not_found_and_retire_validation_paths(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-notfound@dispatch.test",
        role="admin",
    )

    with pytest.raises(NotFoundError):
        await auth_test_context.domain_service.get_domain(str(uuid4()))

    with pytest.raises(ValidationError):
        await auth_test_context.domain_service.retire_domain(
            actor=actor,
            domain_id=str(uuid4()),
            reason="   ",
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.domain_service.retire_domain(
            actor=actor,
            domain_id=str(uuid4()),
            reason="cleanup",
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.domain_service.verify_domain(
            actor=actor,
            domain_id=str(uuid4()),
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_configuration_set_and_ip_pool_duplicate_and_list_paths(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin-config@dispatch.test", role="admin")

    created_set = await auth_test_context.domain_service.create_configuration_set(
        actor=actor,
        payload=SESConfigurationSetCreateRequest(
            name="duplicate-check",
            ses_region="us-east-1",
            event_destination_sns_topic_arn=None,
        ),
    )
    assert created_set.name == "duplicate-check"

    with pytest.raises(ConflictError):
        await auth_test_context.domain_service.create_configuration_set(
            actor=actor,
            payload=SESConfigurationSetCreateRequest(
                name="duplicate-check",
                ses_region="us-east-1",
                event_destination_sns_topic_arn=None,
            ),
        )

    configuration_sets = await auth_test_context.domain_service.list_configuration_sets()
    assert any(item.id == created_set.id for item in configuration_sets)

    created_pool = await auth_test_context.domain_service.create_ip_pool(
        actor=actor,
        payload=IPPoolCreateRequest(
            name="duplicate-pool",
            ses_pool_name="duplicate-pool",
            dedicated_ips=["192.0.2.90"],
            traffic_weight=100,
        ),
    )
    assert created_pool.name == "duplicate-pool"

    with pytest.raises(ConflictError):
        await auth_test_context.domain_service.create_ip_pool(
            actor=actor,
            payload=IPPoolCreateRequest(
                name="duplicate-pool",
                ses_pool_name="duplicate-pool",
                dedicated_ips=["192.0.2.91"],
                traffic_weight=90,
            ),
        )


@pytest.mark.asyncio
async def test_verify_domain_without_active_dns_records_raises_validation(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin-dns@dispatch.test", role="admin")
    created = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name="no-records.dispatch.test",
        dns_provider="manual",
        parent_domain=None,
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        await uow.require_session().execute(
            update(DomainDnsRecord)
            .where(DomainDnsRecord.domain_id == created.domain.id)
            .values(is_active=False)
        )

    with pytest.raises(ValidationError):
        await auth_test_context.domain_service.verify_domain(
            actor=actor,
            domain_id=created.domain.id,
            ip_address=None,
            user_agent=None,
        )


def test_domain_service_static_helpers_and_cache_paths() -> None:
    with pytest.raises(ValidationError):
        DomainService._normalize_domain_name(None)
    with pytest.raises(ValidationError):
        DomainService._normalize_domain_name("invalid")

    failed_record = DomainDnsRecord(
        domain_id=str(uuid4()),
        record_type="TXT",
        name="spf.dispatch.test",
        value="v=spf1 include:amazonses.com -all",
        purpose="spf",
        is_active=True,
        verification_status="failed",
    )
    assert DomainService._purpose_status([], purpose="spf") == "pending"
    assert DomainService._purpose_status([failed_record], purpose="spf") == "pending"

    reset_domain_service_cache()
    cached = get_domain_service()
    assert get_domain_service() is cached
    reset_domain_service_cache()
    assert get_domain_service() is not cached
    reset_domain_service_cache()
