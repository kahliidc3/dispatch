from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from apps.api.deps import get_current_actor, get_list_service_dep, require_admin
from libs.core.auth.models import User
from libs.core.auth.schemas import CurrentActor, MessageResponse
from libs.core.contacts.schemas import ContactResponse
from libs.core.lists.schemas import (
    BulkListMembershipRequest,
    ListCollectionResponse,
    ListContactListResponse,
    ListCreateRequest,
    ListMembershipBulkResponse,
    ListMembershipCreateRequest,
    ListMembershipResponse,
    ListResponse,
)
from libs.core.lists.service import ListService

router = APIRouter(prefix="/lists", tags=["lists"])


@router.post("", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    payload: ListCreateRequest,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ListService, Depends(get_list_service_dep)],
) -> ListResponse:
    list_entity = await service.create_list(actor=actor, payload=payload)
    return ListResponse.from_model(list_entity)


@router.get("", response_model=ListCollectionResponse)
async def list_lists(
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ListService, Depends(get_list_service_dep)],
) -> ListCollectionResponse:
    items = await service.list_lists(actor=actor)
    return ListCollectionResponse(items=[ListResponse.from_model(item) for item in items])


@router.post("/{list_id}/contacts", response_model=ListMembershipResponse)
async def add_contact_to_list(
    list_id: str,
    payload: ListMembershipCreateRequest,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ListService, Depends(get_list_service_dep)],
) -> ListMembershipResponse:
    membership = await service.add_contact_to_list(
        actor=actor,
        list_id=list_id,
        contact_id=payload.contact_id,
    )
    return ListMembershipResponse.from_model(membership)


@router.delete("/{list_id}/contacts/{contact_id}", response_model=MessageResponse)
async def remove_contact_from_list(
    list_id: str,
    contact_id: str,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ListService, Depends(get_list_service_dep)],
) -> MessageResponse:
    await service.remove_contact_from_list(actor=actor, list_id=list_id, contact_id=contact_id)
    return MessageResponse(message="Contact removed from list")


@router.post("/{list_id}/contacts/bulk-add", response_model=ListMembershipBulkResponse)
async def bulk_add_contacts_to_list(
    list_id: str,
    payload: BulkListMembershipRequest,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ListService, Depends(get_list_service_dep)],
) -> ListMembershipBulkResponse:
    result = await service.bulk_add_contacts(actor=actor, list_id=list_id, payload=payload)
    return ListMembershipBulkResponse(
        processed=result.processed,
        added=result.added,
        removed=result.removed,
    )


@router.post("/{list_id}/contacts/bulk-remove", response_model=ListMembershipBulkResponse)
async def bulk_remove_contacts_from_list(
    list_id: str,
    payload: BulkListMembershipRequest,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ListService, Depends(get_list_service_dep)],
) -> ListMembershipBulkResponse:
    result = await service.bulk_remove_contacts(actor=actor, list_id=list_id, payload=payload)
    return ListMembershipBulkResponse(
        processed=result.processed,
        added=result.added,
        removed=result.removed,
    )


@router.get("/{list_id}/contacts", response_model=ListContactListResponse)
async def list_contacts_for_list(
    list_id: str,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ListService, Depends(get_list_service_dep)],
    sendable_only: Annotated[bool, Query()] = True,
) -> ListContactListResponse:
    contacts = await service.list_contacts_for_list(
        actor=actor,
        list_id=list_id,
        sendable_only=sendable_only,
    )
    return ListContactListResponse(items=[ContactResponse.from_model(item) for item in contacts])
