from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from libs.core.auth.schemas import CurrentActor
from libs.core.contacts.schemas import ContactCreateRequest
from libs.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from libs.core.lists.schemas import BulkListMembershipRequest, ListCreateRequest

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
async def test_create_list_add_and_remove_contact(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(auth_user_factory, email="admin-lists@dispatch.test", role="admin")
    contact = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(email="list-member@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )

    created_list = await auth_test_context.list_service.create_list(
        actor=actor,
        payload=ListCreateRequest(name="List A", description="Primary list"),
    )
    assert created_list.name == "List A"

    membership = await auth_test_context.list_service.add_contact_to_list(
        actor=actor,
        list_id=created_list.id,
        contact_id=contact.id,
    )
    assert membership.list_id == created_list.id
    assert membership.contact_id == contact.id

    listed = await auth_test_context.list_service.list_contacts_for_list(
        actor=actor,
        list_id=created_list.id,
        sendable_only=True,
    )
    assert len(listed) == 1
    assert listed[0].id == contact.id

    await auth_test_context.list_service.remove_contact_from_list(
        actor=actor,
        list_id=created_list.id,
        contact_id=contact.id,
    )
    listed_after = await auth_test_context.list_service.list_contacts_for_list(
        actor=actor,
        list_id=created_list.id,
        sendable_only=True,
    )
    assert listed_after == []


@pytest.mark.asyncio
async def test_bulk_membership_and_sendable_filtering(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_actor(
        auth_user_factory,
        email="admin-bulk-lists@dispatch.test",
        role="admin",
    )
    contact_one = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(email="bulk-one@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )
    contact_two = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(email="bulk-two@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )

    list_entity = await auth_test_context.list_service.create_list(
        actor=actor,
        payload=ListCreateRequest(name="Bulk List"),
    )
    add_result = await auth_test_context.list_service.bulk_add_contacts(
        actor=actor,
        list_id=list_entity.id,
        payload=BulkListMembershipRequest(
            contact_ids=[contact_one.id, contact_two.id, str(uuid4())]
        ),
    )
    assert add_result.processed == 3
    assert add_result.added == 2

    await auth_test_context.contact_service.unsubscribe_contact(
        actor=actor,
        contact_id=contact_two.id,
        reason="user_request",
        ip_address=None,
        user_agent=None,
    )

    all_members = await auth_test_context.list_service.list_contacts_for_list(
        actor=actor,
        list_id=list_entity.id,
        sendable_only=False,
    )
    sendable_members = await auth_test_context.list_service.list_contacts_for_list(
        actor=actor,
        list_id=list_entity.id,
        sendable_only=True,
    )
    assert len(all_members) == 2
    assert len(sendable_members) == 1
    assert sendable_members[0].id == contact_one.id

    remove_result = await auth_test_context.list_service.bulk_remove_contacts(
        actor=actor,
        list_id=list_entity.id,
        payload=BulkListMembershipRequest(contact_ids=[contact_one.id, contact_two.id]),
    )
    assert remove_result.processed == 2
    assert remove_result.removed == 2


@pytest.mark.asyncio
async def test_list_guards_not_found_and_ineligible_contact_checks(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin_actor = await _create_actor(
        auth_user_factory,
        email="admin-guards@dispatch.test",
        role="admin",
    )
    user_actor = await _create_actor(
        auth_user_factory,
        email="user-guards@dispatch.test",
        role="user",
    )
    list_entity = await auth_test_context.list_service.create_list(
        actor=admin_actor,
        payload=ListCreateRequest(name="Guarded"),
    )
    contact = await auth_test_context.contact_service.create_contact(
        actor=admin_actor,
        payload=ContactCreateRequest(email="ineligible@dispatch.test"),
        ip_address=None,
        user_agent=None,
    )
    await auth_test_context.contact_service.unsubscribe_contact(
        actor=admin_actor,
        contact_id=contact.id,
        reason="requested",
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.list_service.list_lists(actor=user_actor)

    with pytest.raises(NotFoundError):
        await auth_test_context.list_service.add_contact_to_list(
            actor=admin_actor,
            list_id=str(uuid4()),
            contact_id=contact.id,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.list_service.remove_contact_from_list(
            actor=admin_actor,
            list_id=list_entity.id,
            contact_id=str(uuid4()),
        )

    with pytest.raises(ConflictError):
        await auth_test_context.list_service.add_contact_to_list(
            actor=admin_actor,
            list_id=list_entity.id,
            contact_id=contact.id,
        )
