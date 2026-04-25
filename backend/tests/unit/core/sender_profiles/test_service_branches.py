from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import update

from libs.core.auth.schemas import CurrentActor
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain, IPPool
from libs.core.domains.repository import DomainRepository
from libs.core.domains.schemas import (
    DnsRecordType,
    IPPoolCreateRequest,
    SESConfigurationSetCreateRequest,
)
from libs.core.errors import ConflictError, NotFoundError
from libs.core.sender_profiles.repository import SenderProfileRepository
from libs.core.sender_profiles.schemas import (
    SenderProfileCreateRequest,
    SenderProfileDeleteRequest,
    SenderProfileUpdateRequest,
)
from libs.core.sender_profiles.service import (
    get_sender_profile_service,
    reset_sender_profile_service_cache,
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


async def _create_verified_domain(
    auth_test_context: AuthTestContext,
    *,
    actor: CurrentActor,
    name: str,
) -> str:
    created_domain = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name=name,
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
    return str(created_domain.domain.id)


@pytest.mark.asyncio
async def test_create_sender_profile_error_paths(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-create-paths@dispatch.test",
        role="admin",
    )

    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=actor,
            payload=SenderProfileCreateRequest(
                display_name="Missing Domain",
                from_name="Missing Domain",
                from_email="missing-domain@dispatch.test",
                domain_id=str(uuid4()),
            ),
            ip_address=None,
            user_agent=None,
        )

    domain_id = await _create_verified_domain(
        auth_test_context,
        actor=actor,
        name="sender-errors.dispatch.test",
    )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        await uow.require_session().execute(
            update(Domain).where(Domain.id == domain_id).values(reputation_status="burnt")
        )
    with pytest.raises(ConflictError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=actor,
            payload=SenderProfileCreateRequest(
                display_name="Burnt",
                from_name="Burnt",
                from_email="burnt@sender-errors.dispatch.test",
                domain_id=domain_id,
            ),
            ip_address=None,
            user_agent=None,
        )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        await uow.require_session().execute(
            update(Domain)
            .where(Domain.id == domain_id)
            .values(reputation_status="healthy", default_configuration_set_id=None)
        )
    with pytest.raises(ConflictError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=actor,
            payload=SenderProfileCreateRequest(
                display_name="No Default Config",
                from_name="No Default Config",
                from_email="missing-default@sender-errors.dispatch.test",
                domain_id=domain_id,
            ),
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=actor,
            payload=SenderProfileCreateRequest(
                display_name="Bad Config",
                from_name="Bad Config",
                from_email="bad-config@sender-errors.dispatch.test",
                domain_id=domain_id,
                configuration_set_id=str(uuid4()),
            ),
            ip_address=None,
            user_agent=None,
        )

    valid_config = await auth_test_context.domain_service.create_configuration_set(
        actor=actor,
        payload=SESConfigurationSetCreateRequest(
            name="sender-errors-config",
            ses_region="us-east-1",
            event_destination_sns_topic_arn=None,
        ),
    )
    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=actor,
            payload=SenderProfileCreateRequest(
                display_name="Bad Pool",
                from_name="Bad Pool",
                from_email="bad-pool@sender-errors.dispatch.test",
                domain_id=domain_id,
                configuration_set_id=valid_config.id,
                ip_pool_id=str(uuid4()),
            ),
            ip_address=None,
            user_agent=None,
        )

    inactive_pool = await auth_test_context.domain_service.create_ip_pool(
        actor=actor,
        payload=IPPoolCreateRequest(
            name="inactive-create-pool",
            ses_pool_name="inactive-create-pool",
            dedicated_ips=["192.0.2.120"],
            traffic_weight=100,
        ),
    )
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        await uow.require_session().execute(
            update(IPPool).where(IPPool.id == inactive_pool.id).values(is_active=False)
        )
    with pytest.raises(ConflictError):
        await auth_test_context.sender_profile_service.create_sender_profile(
            actor=actor,
            payload=SenderProfileCreateRequest(
                display_name="Inactive Pool",
                from_name="Inactive Pool",
                from_email="inactive-pool@sender-errors.dispatch.test",
                domain_id=domain_id,
                configuration_set_id=valid_config.id,
                ip_pool_id=inactive_pool.id,
            ),
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_update_sender_profile_branch_paths(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-update-paths@dispatch.test",
        role="admin",
    )
    domain_id = await _create_verified_domain(
        auth_test_context,
        actor=actor,
        name="sender-update.dispatch.test",
    )

    profile = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="Base",
            from_name="Base Name",
            from_email="base@sender-update.dispatch.test",
            domain_id=domain_id,
        ),
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.update_sender_profile(
            actor=actor,
            sender_profile_id=str(uuid4()),
            payload=SenderProfileUpdateRequest(display_name="missing"),
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.update_sender_profile(
            actor=actor,
            sender_profile_id=profile.id,
            payload=SenderProfileUpdateRequest(configuration_set_id=str(uuid4())),
            ip_address=None,
            user_agent=None,
        )

    valid_config = await auth_test_context.domain_service.create_configuration_set(
        actor=actor,
        payload=SESConfigurationSetCreateRequest(
            name="sender-update-config",
            ses_region="us-east-1",
            event_destination_sns_topic_arn=None,
        ),
    )
    updated_with_config = await auth_test_context.sender_profile_service.update_sender_profile(
        actor=actor,
        sender_profile_id=profile.id,
        payload=SenderProfileUpdateRequest(
            from_name="Updated Name",
            reply_to="updated-reply@sender-update.dispatch.test",
            allowed_campaign_types=["transactional", "followup"],
            configuration_set_id=valid_config.id,
            paused_reason="manual hold",
        ),
        ip_address=None,
        user_agent=None,
    )
    assert updated_with_config.from_name == "Updated Name"
    assert updated_with_config.reply_to == "updated-reply@sender-update.dispatch.test"
    assert updated_with_config.allowed_campaign_types == ["transactional", "followup"]
    assert updated_with_config.configuration_set_id == valid_config.id
    assert updated_with_config.paused_reason == "manual hold"

    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.update_sender_profile(
            actor=actor,
            sender_profile_id=profile.id,
            payload=SenderProfileUpdateRequest(ip_pool_id=str(uuid4())),
            ip_address=None,
            user_agent=None,
        )

    inactive_pool = await auth_test_context.domain_service.create_ip_pool(
        actor=actor,
        payload=IPPoolCreateRequest(
            name="inactive-update-pool",
            ses_pool_name="inactive-update-pool",
            dedicated_ips=["192.0.2.130"],
            traffic_weight=100,
        ),
    )
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        await uow.require_session().execute(
            update(IPPool).where(IPPool.id == inactive_pool.id).values(is_active=False)
        )
    with pytest.raises(ConflictError):
        await auth_test_context.sender_profile_service.update_sender_profile(
            actor=actor,
            sender_profile_id=profile.id,
            payload=SenderProfileUpdateRequest(ip_pool_id=inactive_pool.id),
            ip_address=None,
            user_agent=None,
        )

    active_pool = await auth_test_context.domain_service.create_ip_pool(
        actor=actor,
        payload=IPPoolCreateRequest(
            name="active-update-pool",
            ses_pool_name="active-update-pool",
            dedicated_ips=["192.0.2.131"],
            traffic_weight=100,
        ),
    )
    final_update = await auth_test_context.sender_profile_service.update_sender_profile(
        actor=actor,
        sender_profile_id=profile.id,
        payload=SenderProfileUpdateRequest(ip_pool_id=active_pool.id, is_active=True),
        ip_address=None,
        user_agent=None,
    )
    assert final_update.ip_pool_id == active_pool.id
    assert final_update.is_active is True
    assert final_update.paused_reason is None


@pytest.mark.asyncio
async def test_update_sender_profile_refreshed_not_found_path(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-update-refresh@dispatch.test",
        role="admin",
    )
    domain_id = await _create_verified_domain(
        auth_test_context,
        actor=actor,
        name="sender-refresh.dispatch.test",
    )
    profile = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="Refresh",
            from_name="Refresh",
            from_email="refresh@sender-refresh.dispatch.test",
            domain_id=domain_id,
        ),
        ip_address=None,
        user_agent=None,
    )

    original_get_by_id = SenderProfileRepository.get_by_id
    call_count = {"count": 0}

    async def _patched_get_by_id(
        self: SenderProfileRepository,
        sender_profile_id: str,
    ) -> Any:
        call_count["count"] += 1
        if call_count["count"] == 2:
            return None
        return await original_get_by_id(self, sender_profile_id)

    monkeypatch.setattr(SenderProfileRepository, "get_by_id", _patched_get_by_id)

    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.update_sender_profile(
            actor=actor,
            sender_profile_id=profile.id,
            payload=SenderProfileUpdateRequest(display_name="should-fail"),
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_delete_sender_profile_error_paths_and_cache(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-delete-paths@dispatch.test",
        role="admin",
    )
    domain_id = await _create_verified_domain(
        auth_test_context,
        actor=actor,
        name="sender-delete.dispatch.test",
    )

    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.delete_sender_profile(
            actor=actor,
            sender_profile_id=str(uuid4()),
            payload=SenderProfileDeleteRequest(reason="missing"),
            ip_address=None,
            user_agent=None,
        )

    profile = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="Delete Target",
            from_name="Delete Target",
            from_email="delete@sender-delete.dispatch.test",
            domain_id=domain_id,
        ),
        ip_address=None,
        user_agent=None,
    )

    original_soft_delete = SenderProfileRepository.soft_delete

    async def _patched_soft_delete(
        self: SenderProfileRepository,
        *,
        sender_profile_id: str,
        reason: str,
    ) -> bool:
        return False

    monkeypatch.setattr(SenderProfileRepository, "soft_delete", _patched_soft_delete)
    with pytest.raises(NotFoundError):
        await auth_test_context.sender_profile_service.delete_sender_profile(
            actor=actor,
            sender_profile_id=profile.id,
            payload=SenderProfileDeleteRequest(reason="simulate-failure"),
            ip_address=None,
            user_agent=None,
        )
    monkeypatch.setattr(SenderProfileRepository, "soft_delete", original_soft_delete)

    reset_sender_profile_service_cache()
    cached = get_sender_profile_service()
    assert get_sender_profile_service() is cached
    reset_sender_profile_service_cache()
    assert get_sender_profile_service() is not cached
    reset_sender_profile_service_cache()


@pytest.mark.asyncio
async def test_update_sender_profile_with_ip_pool_none_keeps_flow(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-ip-none@dispatch.test",
        role="admin",
    )
    domain_id = await _create_verified_domain(
        auth_test_context,
        actor=actor,
        name="sender-none.dispatch.test",
    )

    profile = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="None Pool",
            from_name="None Pool",
            from_email="none-pool@sender-none.dispatch.test",
            domain_id=domain_id,
        ),
        ip_address=None,
        user_agent=None,
    )

    updated = await auth_test_context.sender_profile_service.update_sender_profile(
        actor=actor,
        sender_profile_id=profile.id,
        payload=SenderProfileUpdateRequest(ip_pool_id="", is_active=True),
        ip_address=None,
        user_agent=None,
    )
    assert updated.ip_pool_id is None


@pytest.mark.asyncio
async def test_create_sender_profile_with_explicit_configuration_set_success(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-explicit-config@dispatch.test",
        role="admin",
    )
    domain_id = await _create_verified_domain(
        auth_test_context,
        actor=actor,
        name="sender-explicit-config.dispatch.test",
    )

    configuration_set = await auth_test_context.domain_service.create_configuration_set(
        actor=actor,
        payload=SESConfigurationSetCreateRequest(
            name="sender-explicit-config",
            ses_region="us-east-1",
            event_destination_sns_topic_arn=None,
        ),
    )

    created = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="Explicit Config",
            from_name="Explicit Config",
            from_email="explicit@sender-explicit-config.dispatch.test",
            domain_id=domain_id,
            configuration_set_id=configuration_set.id,
        ),
        ip_address=None,
        user_agent=None,
    )
    assert created.configuration_set_id == configuration_set.id


@pytest.mark.asyncio
async def test_update_sender_profile_with_existing_configuration_set_id(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-config-update@dispatch.test",
        role="admin",
    )
    domain_id = await _create_verified_domain(
        auth_test_context,
        actor=actor,
        name="sender-config-update.dispatch.test",
    )

    baseline = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="Config Update",
            from_name="Config Update",
            from_email="config-update@sender-config-update.dispatch.test",
            domain_id=domain_id,
        ),
        ip_address=None,
        user_agent=None,
    )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        domain_repo = DomainRepository(uow.require_session())
        existing_configuration_set = await domain_repo.get_configuration_set_by_name(
            "sender-config-update.dispatch.test-default"
        )
        assert existing_configuration_set is not None
        refreshed = await auth_test_context.sender_profile_service.update_sender_profile(
            actor=actor,
            sender_profile_id=baseline.id,
            payload=SenderProfileUpdateRequest(
                configuration_set_id=existing_configuration_set.id,
            ),
            ip_address=None,
            user_agent=None,
        )
    assert refreshed.configuration_set_id == existing_configuration_set.id
