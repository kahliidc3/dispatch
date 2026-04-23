from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from libs.core.auth.schemas import CurrentActor
from libs.core.config import get_settings
from libs.core.contacts.models import Contact
from libs.core.contacts.repository import ContactRepository
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from libs.core.lists.models import List, ListMembership
from libs.core.lists.repository import ListRepository
from libs.core.lists.schemas import BulkListMembershipRequest, ListCreateRequest


@dataclass(slots=True)
class BulkMembershipResult:
    processed: int
    added: int
    removed: int


class ListService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._session_factory = get_session_factory()

    async def create_list(self, *, actor: CurrentActor, payload: ListCreateRequest) -> List:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            repo = ListRepository(uow.require_session())
            return await repo.create_list(
                name=payload.name.strip(),
                description=payload.description.strip() if payload.description else None,
            )

    async def list_lists(self, *, actor: CurrentActor) -> list[List]:
        self._require_admin(actor)
        async with self._session_factory() as session:
            repo = ListRepository(session)
            return await repo.list_lists()

    async def add_contact_to_list(
        self,
        *,
        actor: CurrentActor,
        list_id: str,
        contact_id: str,
    ) -> ListMembership:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            list_repo = ListRepository(uow.require_session())
            contact_repo = ContactRepository(uow.require_session())
            list_entity = await list_repo.get_list_by_id(list_id)
            if list_entity is None:
                raise NotFoundError("List not found")

            contact = await contact_repo.get_contact_by_id(contact_id)
            if contact is None:
                raise NotFoundError("Contact not found")
            if contact.lifecycle_status in {"suppressed", "unsubscribed", "deleted"}:
                raise ConflictError("Contact is not eligible for list delivery")

            membership = await list_repo.add_membership(list_id=list_id, contact_id=contact_id)
            await list_repo.refresh_member_count(list_id=list_id)
            return membership

    async def remove_contact_from_list(
        self,
        *,
        actor: CurrentActor,
        list_id: str,
        contact_id: str,
    ) -> None:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            repo = ListRepository(uow.require_session())
            list_entity = await repo.get_list_by_id(list_id)
            if list_entity is None:
                raise NotFoundError("List not found")

            removed = await repo.remove_membership(list_id=list_id, contact_id=contact_id)
            if not removed:
                raise NotFoundError("List membership not found")
            await repo.refresh_member_count(list_id=list_id)

    async def bulk_add_contacts(
        self,
        *,
        actor: CurrentActor,
        list_id: str,
        payload: BulkListMembershipRequest,
    ) -> BulkMembershipResult:
        self._require_admin(actor)
        added = 0
        async with UnitOfWork(self._session_factory) as uow:
            list_repo = ListRepository(uow.require_session())
            contact_repo = ContactRepository(uow.require_session())
            list_entity = await list_repo.get_list_by_id(list_id)
            if list_entity is None:
                raise NotFoundError("List not found")

            for contact_id in payload.contact_ids:
                contact = await contact_repo.get_contact_by_id(contact_id)
                if contact is None:
                    continue
                if contact.lifecycle_status in {"suppressed", "unsubscribed", "deleted"}:
                    continue

                existing = await list_repo.get_membership(list_id=list_id, contact_id=contact_id)
                if existing is None:
                    await list_repo.add_membership(list_id=list_id, contact_id=contact_id)
                    added += 1

            await list_repo.refresh_member_count(list_id=list_id)
            return BulkMembershipResult(processed=len(payload.contact_ids), added=added, removed=0)

    async def bulk_remove_contacts(
        self,
        *,
        actor: CurrentActor,
        list_id: str,
        payload: BulkListMembershipRequest,
    ) -> BulkMembershipResult:
        self._require_admin(actor)
        removed = 0
        async with UnitOfWork(self._session_factory) as uow:
            repo = ListRepository(uow.require_session())
            list_entity = await repo.get_list_by_id(list_id)
            if list_entity is None:
                raise NotFoundError("List not found")

            for contact_id in payload.contact_ids:
                if await repo.remove_membership(list_id=list_id, contact_id=contact_id):
                    removed += 1

            await repo.refresh_member_count(list_id=list_id)
            return BulkMembershipResult(
                processed=len(payload.contact_ids),
                added=0,
                removed=removed,
            )

    async def list_contacts_for_list(
        self,
        *,
        actor: CurrentActor,
        list_id: str,
        sendable_only: bool,
    ) -> list[Contact]:
        self._require_admin(actor)
        async with self._session_factory() as session:
            repo = ListRepository(session)
            list_entity = await repo.get_list_by_id(list_id)
            if list_entity is None:
                raise NotFoundError("List not found")
            return await repo.list_contacts_for_list(list_id=list_id, sendable_only=sendable_only)

    @staticmethod
    def _require_admin(actor: CurrentActor) -> None:
        if actor.user.role != "admin":
            raise PermissionDeniedError("Admin role required")


@lru_cache(maxsize=1)
def get_list_service() -> ListService:
    return ListService()


def reset_list_service_cache() -> None:
    get_list_service.cache_clear()
