from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.contacts.models import Contact
from libs.core.lists.models import List, ListMembership


class ListRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_list_by_id(self, list_id: str) -> List | None:
        stmt = select(List).where(List.id == list_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_lists(self) -> list[List]:
        stmt = select(List).order_by(List.created_at.desc(), List.id.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_list(self, *, name: str, description: str | None) -> List:
        list_entity = List(name=name, description=description)
        self.session.add(list_entity)
        await self.session.flush()
        return list_entity

    async def get_membership(self, *, list_id: str, contact_id: str) -> ListMembership | None:
        stmt = (
            select(ListMembership)
            .where(ListMembership.list_id == list_id)
            .where(ListMembership.contact_id == contact_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_membership(self, *, list_id: str, contact_id: str) -> ListMembership:
        existing = await self.get_membership(list_id=list_id, contact_id=contact_id)
        if existing is not None:
            return existing

        membership = ListMembership(list_id=list_id, contact_id=contact_id)
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def remove_membership(self, *, list_id: str, contact_id: str) -> bool:
        membership = await self.get_membership(list_id=list_id, contact_id=contact_id)
        if membership is None:
            return False
        await self.session.delete(membership)
        await self.session.flush()
        return True

    async def list_contacts_for_list(
        self,
        *,
        list_id: str,
        sendable_only: bool,
    ) -> list[Contact]:
        stmt = (
            select(Contact)
            .join(ListMembership, ListMembership.contact_id == Contact.id)
            .where(ListMembership.list_id == list_id)
            .where(Contact.deleted_at.is_(None))
            .order_by(Contact.created_at.desc(), Contact.id.desc())
        )
        if sendable_only:
            stmt = stmt.where(Contact.lifecycle_status == "active")
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def refresh_member_count(self, *, list_id: str) -> int:
        count_stmt = (
            select(func.count())
            .select_from(ListMembership)
            .where(ListMembership.list_id == list_id)
        )
        count_result = await self.session.execute(count_stmt)
        member_count = int(count_result.scalar_one())
        stmt = (
            update(List)
            .where(List.id == list_id)
            .values(member_count=member_count)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        return member_count
