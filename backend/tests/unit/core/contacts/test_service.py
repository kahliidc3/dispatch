from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from libs.core.auth.models import AuditLog
from libs.core.auth.schemas import CurrentActor
from libs.core.contacts.schemas import (
    ContactCreateRequest,
    ContactPreferenceUpdateRequest,
    ContactQueryParams,
    ContactUpdateRequest,
)
from libs.core.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
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
async def test_create_list_get_update_delete_contact_lifecycle(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-contacts@dispatch.test",
        role="admin",
    )

    created = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="Lead@Example.COM",
            first_name="Lead",
            last_name="One",
            source_type="manual",
            source_detail="seed",
        ),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    assert created.email == "lead@example.com"
    assert created.email_domain == "example.com"
    assert created.lifecycle_status == "active"

    listed = await auth_test_context.contact_service.list_contacts(
        actor=actor,
        query=ContactQueryParams(limit=10, offset=0, search="lead@", email_domain="example.com"),
    )
    assert listed.total == 1
    assert listed.items[0].id == created.id

    fetched = await auth_test_context.contact_service.get_contact(
        actor=actor,
        contact_id=created.id,
    )
    assert fetched.id == created.id

    updated = await auth_test_context.contact_service.update_contact(
        actor=actor,
        contact_id=created.id,
        payload=ContactUpdateRequest(
            first_name="Leady",
            company="Dispatch",
            custom_attributes={"tier": "a"},
        ),
        ip_address=None,
        user_agent=None,
    )
    assert updated.first_name == "Leady"
    assert updated.company == "Dispatch"
    assert updated.custom_attributes == {"tier": "a"}

    unsubscribed = await auth_test_context.contact_service.unsubscribe_contact(
        actor=actor,
        contact_id=created.id,
        reason="requested",
        ip_address=None,
        user_agent=None,
    )
    assert unsubscribed.lifecycle_status == "unsubscribed"

    with pytest.raises(ConflictError):
        await auth_test_context.contact_service.update_contact(
            actor=actor,
            contact_id=created.id,
            payload=ContactUpdateRequest(lifecycle_status="active"),
            ip_address=None,
            user_agent=None,
        )

    await auth_test_context.contact_service.delete_contact(
        actor=actor,
        contact_id=created.id,
        reason="gdpr",
        ip_address=None,
        user_agent=None,
    )
    with pytest.raises(NotFoundError):
        await auth_test_context.contact_service.get_contact(actor=actor, contact_id=created.id)

    async with auth_test_context.session_factory() as session:
        unsubscribe_count_stmt = select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "contact.unsubscribe"
        )
        unsubscribe_count = (await session.execute(unsubscribe_count_stmt)).scalar_one()
        delete_count_stmt = select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "contact.hard_delete"
        )
        delete_count = (await session.execute(delete_count_stmt)).scalar_one()
        assert unsubscribe_count >= 1
        assert delete_count >= 1


@pytest.mark.asyncio
async def test_case_insensitive_uniqueness_and_permission_guards(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-uniq@dispatch.test",
        role="admin",
    )
    user_actor = await _create_actor(
        auth_user_factory,
        email="user-uniq@dispatch.test",
        role="user",
    )

    await auth_test_context.contact_service.create_contact(
        actor=admin_actor,
        payload=ContactCreateRequest(email="dupe@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )
    with pytest.raises(ConflictError):
        await auth_test_context.contact_service.create_contact(
            actor=admin_actor,
            payload=ContactCreateRequest(email="DUPE@dispatch.test"),
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.contact_service.list_contacts(
            actor=user_actor,
            query=ContactQueryParams(limit=5, offset=0),
        )


@pytest.mark.asyncio
async def test_public_unsubscribe_token_and_forged_signature(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin-public@dispatch.test", role="admin")
    contact = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(email="public-unsub@dispatch.test", source_type="api"),
        ip_address=None,
        user_agent=None,
    )
    token = await auth_test_context.contact_service.create_unsubscribe_token(
        actor=actor,
        contact_id=contact.id,
    )

    unsubscribed = await auth_test_context.contact_service.unsubscribe_public(
        token=token,
        ip_address=None,
        user_agent=None,
    )
    assert unsubscribed.lifecycle_status == "unsubscribed"

    with pytest.raises(AuthenticationError):
        await auth_test_context.contact_service.unsubscribe_public(
            token=f"{token}forged",
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_preferences_read_write(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-preferences@dispatch.test",
        role="admin",
    )
    contact = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(email="prefs@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )

    initial = await auth_test_context.contact_service.get_preferences(
        actor=actor,
        contact_id=contact.id,
    )
    assert initial.language == "en"
    assert initial.campaign_types == []

    updated = await auth_test_context.contact_service.set_preferences(
        actor=actor,
        contact_id=contact.id,
        payload=ContactPreferenceUpdateRequest(
            campaign_types=["newsletter", "outreach"],
            max_frequency_per_week=3,
            language="FR",
        ),
        ip_address=None,
        user_agent=None,
    )
    assert updated.campaign_types == ["newsletter", "outreach"]
    assert updated.max_frequency_per_week == 3
    assert updated.language == "fr"

    with pytest.raises(NotFoundError):
        await auth_test_context.contact_service.get_preferences(
            actor=actor,
            contact_id=str(uuid4()),
        )
