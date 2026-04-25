from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from libs.core.auth.schemas import CurrentActor
from libs.core.contacts.schemas import ContactCreateRequest, ContactUpdateRequest
from libs.core.contacts.service import (
    ContactService,
    get_contact_service,
    reset_contact_service_cache,
)
from libs.core.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
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
async def test_create_contact_invalid_email_and_not_found_paths(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-invalid@dispatch.test",
        role="admin",
    )

    with pytest.raises(ValidationError):
        await auth_test_context.contact_service.create_contact(
            actor=admin_actor,
            payload=ContactCreateRequest(email="not-an-email"),
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.contact_service.get_contact(
            actor=admin_actor,
            contact_id=str(uuid4()),
        )
    with pytest.raises(NotFoundError):
        await auth_test_context.contact_service.update_contact(
            actor=admin_actor,
            contact_id=str(uuid4()),
            payload=ContactUpdateRequest(first_name="none"),
            ip_address=None,
            user_agent=None,
        )
    with pytest.raises(NotFoundError):
        await auth_test_context.contact_service.unsubscribe_contact(
            actor=admin_actor,
            contact_id=str(uuid4()),
            reason="missing",
            ip_address=None,
            user_agent=None,
        )
    with pytest.raises(NotFoundError):
        await auth_test_context.contact_service.delete_contact(
            actor=admin_actor,
            contact_id=str(uuid4()),
            reason="cleanup",
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_update_noop_and_delete_reason_validation(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-noop@dispatch.test",
        role="admin",
    )
    created = await auth_test_context.contact_service.create_contact(
        actor=admin_actor,
        payload=ContactCreateRequest(email="noop@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )

    untouched = await auth_test_context.contact_service.update_contact(
        actor=admin_actor,
        contact_id=created.id,
        payload=ContactUpdateRequest(),
        ip_address=None,
        user_agent=None,
    )
    assert untouched.id == created.id
    assert untouched.email == "noop@dispatch.test"

    with pytest.raises(ValidationError):
        await auth_test_context.contact_service.delete_contact(
            actor=admin_actor,
            contact_id=created.id,
            reason=" ",
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_unsubscribe_branches_and_guard_checks(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-unsub@dispatch.test",
        role="admin",
    )
    user_actor = await _create_actor(
        auth_user_factory,
        email="user-unsub@dispatch.test",
        role="user",
    )
    created = await auth_test_context.contact_service.create_contact(
        actor=admin_actor,
        payload=ContactCreateRequest(email="branch-unsub@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.contact_service.create_unsubscribe_token(
            actor=user_actor,
            contact_id=created.id,
        )

    token = await auth_test_context.contact_service.create_unsubscribe_token(
        actor=admin_actor,
        contact_id=created.id,
    )

    first = await auth_test_context.contact_service.unsubscribe_public(
        token=token,
        ip_address=None,
        user_agent=None,
    )
    assert first.lifecycle_status == "unsubscribed"

    second = await auth_test_context.contact_service.unsubscribe_public(
        token=token,
        ip_address=None,
        user_agent=None,
    )
    assert second.lifecycle_status == "unsubscribed"

    bad_payload_token = auth_test_context.contact_service._unsubscribe_serializer.dumps(
        {"bad": "value"}
    )
    with pytest.raises(AuthenticationError):
        await auth_test_context.contact_service.unsubscribe_public(
            token=bad_payload_token,
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.contact_service.create_unsubscribe_token(
            actor=admin_actor,
            contact_id=str(uuid4()),
        )


@pytest.mark.asyncio
async def test_lifecycle_transition_helper_and_cache_paths(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-transition@dispatch.test",
        role="admin",
    )
    created = await auth_test_context.contact_service.create_contact(
        actor=admin_actor,
        payload=ContactCreateRequest(email="transition@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )

    transitioned = await auth_test_context.contact_service.update_contact(
        actor=admin_actor,
        contact_id=created.id,
        payload=ContactUpdateRequest(lifecycle_status="bounced"),
        ip_address=None,
        user_agent=None,
    )
    assert transitioned.lifecycle_status == "bounced"

    with pytest.raises(ConflictError):
        ContactService._assert_valid_lifecycle_transition(
            current_status="bounced",
            target_status="suppressed",
        )

    with pytest.raises(ValidationError):
        ContactService._assert_valid_lifecycle_transition(
            current_status="active",
            target_status="archived",
        )

    reset_contact_service_cache()
    cached = get_contact_service()
    assert get_contact_service() is cached
    reset_contact_service_cache()
    assert get_contact_service() is not cached
    reset_contact_service_cache()
