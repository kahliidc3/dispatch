from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.contacts.models import Contact, ContactSource, Preference, SubscriptionStatus


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_contact_by_id(self, contact_id: str) -> Contact | None:
        stmt = select(Contact).where(Contact.id == contact_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_contact_by_email(self, email: str) -> Contact | None:
        stmt = select(Contact).where(func.lower(Contact.email) == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_contacts(
        self,
        *,
        limit: int,
        offset: int,
        lifecycle_status: str | None,
        search: str | None,
        email_domain: str | None,
    ) -> list[Contact]:
        stmt = select(Contact).order_by(Contact.created_at.desc(), Contact.id.desc())
        if lifecycle_status is not None:
            stmt = stmt.where(Contact.lifecycle_status == lifecycle_status)
        if search is not None:
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(func.lower(Contact.email).like(term))
        if email_domain is not None:
            stmt = stmt.where(func.lower(Contact.email_domain) == email_domain.strip().lower())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_contacts(
        self,
        *,
        lifecycle_status: str | None,
        search: str | None,
        email_domain: str | None,
    ) -> int:
        stmt = select(func.count()).select_from(Contact)
        if lifecycle_status is not None:
            stmt = stmt.where(Contact.lifecycle_status == lifecycle_status)
        if search is not None:
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(func.lower(Contact.email).like(term))
        if email_domain is not None:
            stmt = stmt.where(func.lower(Contact.email_domain) == email_domain.strip().lower())
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create_contact(
        self,
        *,
        email: str,
        email_domain: str,
        first_name: str | None,
        last_name: str | None,
        company: str | None,
        title: str | None,
        phone: str | None,
        country_code: str | None,
        timezone: str | None,
        custom_attributes: dict[str, object],
    ) -> Contact:
        contact = Contact(
            email=email,
            email_domain=email_domain,
            first_name=first_name,
            last_name=last_name,
            company=company,
            title=title,
            phone=phone,
            country_code=country_code,
            timezone=timezone,
            custom_attributes=custom_attributes,
        )
        self.session.add(contact)
        await self.session.flush()
        return contact

    async def update_contact(self, *, contact_id: str, values: dict[str, object]) -> bool:
        stmt = (
            update(Contact)
            .where(Contact.id == contact_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def delete_contact(self, *, contact_id: str) -> bool:
        stmt = delete(Contact).where(Contact.id == contact_id)
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def create_contact_source(
        self,
        *,
        contact_id: str,
        source_type: str,
        source_detail: str | None,
        source_list: str | None,
    ) -> ContactSource:
        source = ContactSource(
            contact_id=contact_id,
            source_type=source_type,
            source_detail=source_detail,
            source_list=source_list,
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def get_subscription_status(
        self,
        *,
        contact_id: str,
        channel: str = "email",
    ) -> SubscriptionStatus | None:
        stmt = (
            select(SubscriptionStatus)
            .where(SubscriptionStatus.contact_id == contact_id)
            .where(SubscriptionStatus.channel == channel)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_subscription_status(
        self,
        *,
        contact_id: str,
        channel: str,
        status: str,
        reason: str | None,
    ) -> SubscriptionStatus:
        existing = await self.get_subscription_status(contact_id=contact_id, channel=channel)
        if existing is None:
            existing = SubscriptionStatus(
                contact_id=contact_id,
                channel=channel,
                status=status,
                reason=reason,
            )
            self.session.add(existing)
            await self.session.flush()
            return existing

        stmt = (
            update(SubscriptionStatus)
            .where(SubscriptionStatus.id == existing.id)
            .values(
                status=status,
                reason=reason,
                effective_at=datetime.now(UTC),
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        refreshed = await self.get_subscription_status(contact_id=contact_id, channel=channel)
        if refreshed is None:
            return existing
        return refreshed

    async def get_preferences(self, *, contact_id: str) -> Preference | None:
        stmt = select(Preference).where(Preference.contact_id == contact_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_preferences(
        self,
        *,
        contact_id: str,
        campaign_types: list[str],
        max_frequency_per_week: int | None,
        language: str,
    ) -> Preference:
        existing = await self.get_preferences(contact_id=contact_id)
        if existing is None:
            preference = Preference(
                contact_id=contact_id,
                campaign_types=campaign_types,
                max_frequency_per_week=max_frequency_per_week,
                language=language,
            )
            self.session.add(preference)
            await self.session.flush()
            return preference

        stmt = (
            update(Preference)
            .where(Preference.id == existing.id)
            .values(
                campaign_types=campaign_types,
                max_frequency_per_week=max_frequency_per_week,
                language=language,
                updated_at=datetime.now(UTC),
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        refreshed = await self.get_preferences(contact_id=contact_id)
        if refreshed is None:
            return existing
        return refreshed
