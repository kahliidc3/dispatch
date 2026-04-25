from __future__ import annotations

from typing import Any

import pytest

from libs.core.auth.schemas import CurrentActor
from libs.core.domains.schemas import DnsRecordType, IPPoolCreateRequest
from libs.core.errors import ConflictError, PermissionDeniedError
from libs.core.sender_profiles.schemas import (
    SenderProfileCreateRequest,
    SenderProfileDeleteRequest,
    SenderProfileUpdateRequest,
)

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
async def test_cannot_create_sender_profile_for_unverified_domain(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin@dispatch.test", role="admin")
    created_domain = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name="identity.dispatch.test",
        dns_provider="manual",
        parent_domain=None,
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(ConflictError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=actor,
            payload=SenderProfileCreateRequest(
                display_name="Dispatch Sales",
                from_name="Dispatch",
                from_email="sales@identity.dispatch.test",
                reply_to="reply@identity.dispatch.test",
                domain_id=created_domain.domain.id,
            ),
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_create_update_delete_sender_profile_happy_path(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin2@dispatch.test", role="admin")
    created_domain = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name="verified.dispatch.test",
        dns_provider="manual",
        parent_domain=None,
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )
    for record in created_domain.dns_records:
        auth_test_context.dns_adapter.set_record(
            record_type=DnsRecordType(record.record_type),
            name=record.name,
            values=[record.value],
        )
    await auth_test_context.domain_service.verify_domain(
        actor=actor,
        domain_id=created_domain.domain.id,
        ip_address=None,
        user_agent=None,
    )

    pool = await auth_test_context.domain_service.create_ip_pool(
        actor=actor,
        payload=IPPoolCreateRequest(
            name="pool-test",
            ses_pool_name="ses-pool-test",
            dedicated_ips=["192.0.2.50"],
            traffic_weight=80,
        ),
    )
    profile = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="Dispatch Team",
            from_name="Dispatch",
            from_email="team@verified.dispatch.test",
            reply_to="reply@verified.dispatch.test",
            domain_id=created_domain.domain.id,
            ip_pool_id=pool.id,
            allowed_campaign_types=["outreach"],
        ),
        ip_address=None,
        user_agent=None,
    )
    assert profile.from_email == "team@verified.dispatch.test"
    assert profile.ip_pool_id == pool.id

    updated = await auth_test_context.sender_profile_service.update_sender_profile(
        actor=actor,
        sender_profile_id=profile.id,
        payload=SenderProfileUpdateRequest(
            display_name="Dispatch Team Updated",
            daily_send_limit=250,
            is_active=False,
            paused_reason="maintenance",
        ),
        ip_address=None,
        user_agent=None,
    )
    assert updated.display_name == "Dispatch Team Updated"
    assert updated.daily_send_limit == 250
    assert updated.is_active is False
    assert updated.paused_reason == "maintenance"

    await auth_test_context.sender_profile_service.delete_sender_profile(
        actor=actor,
        sender_profile_id=profile.id,
        payload=SenderProfileDeleteRequest(reason="retired profile"),
        ip_address=None,
        user_agent=None,
    )

    listed = await auth_test_context.sender_profile_service.list_sender_profiles(actor=actor)
    deleted = next(item for item in listed if item.id == profile.id)
    assert deleted.is_active is False
    assert deleted.paused_reason == "retired profile"


@pytest.mark.asyncio
async def test_sender_profile_uniqueness_and_admin_guard(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(auth_user_factory, email="admin3@dispatch.test", role="admin")
    user_actor = await _create_actor(auth_user_factory, email="user@dispatch.test", role="user")
    created_domain = await auth_test_context.domain_service.create_domain(
        actor=admin_actor,
        name="guard.dispatch.test",
        dns_provider="manual",
        parent_domain=None,
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )
    for record in created_domain.dns_records:
        auth_test_context.dns_adapter.set_record(
            record_type=DnsRecordType(record.record_type),
            name=record.name,
            values=[record.value],
        )
    await auth_test_context.domain_service.verify_domain(
        actor=admin_actor,
        domain_id=created_domain.domain.id,
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=user_actor,
            payload=SenderProfileCreateRequest(
                display_name="Unauthorized",
                from_name="Unauthorized",
                from_email="unauth@guard.dispatch.test",
                domain_id=created_domain.domain.id,
            ),
            ip_address=None,
            user_agent=None,
        )

    await auth_test_context.sender_profile_service.create_sender_profile(
        actor=admin_actor,
        payload=SenderProfileCreateRequest(
            display_name="Primary",
            from_name="Primary",
            from_email="primary@guard.dispatch.test",
            domain_id=created_domain.domain.id,
        ),
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(ConflictError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=admin_actor,
            payload=SenderProfileCreateRequest(
                display_name="Duplicate",
                from_name="Duplicate",
                from_email="primary@guard.dispatch.test",
                domain_id=created_domain.domain.id,
            ),
            ip_address=None,
            user_agent=None,
        )
