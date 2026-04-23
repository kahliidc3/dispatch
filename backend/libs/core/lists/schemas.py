from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from libs.core.contacts.schemas import ContactResponse
from libs.core.lists.models import List, ListMembership


class ListCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class ListResponse(BaseModel):
    id: str
    name: str
    description: str | None
    member_count: int
    created_at: datetime

    @classmethod
    def from_model(cls, list_entity: List) -> ListResponse:
        return cls(
            id=list_entity.id,
            name=list_entity.name,
            description=list_entity.description,
            member_count=list_entity.member_count,
            created_at=list_entity.created_at,
        )


class ListCollectionResponse(BaseModel):
    items: list[ListResponse]


class ListMembershipCreateRequest(BaseModel):
    contact_id: str


class BulkListMembershipRequest(BaseModel):
    contact_ids: list[str] = Field(min_length=1, max_length=500)


class ListMembershipResponse(BaseModel):
    list_id: str
    contact_id: str
    added_at: datetime

    @classmethod
    def from_model(cls, membership: ListMembership) -> ListMembershipResponse:
        return cls(
            list_id=membership.list_id,
            contact_id=membership.contact_id,
            added_at=membership.added_at,
        )


class ListMembershipBulkResponse(BaseModel):
    processed: int
    added: int
    removed: int


class ListContactListResponse(BaseModel):
    items: list[ContactResponse]
