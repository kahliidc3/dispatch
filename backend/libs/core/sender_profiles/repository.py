from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.sender_profiles.models import SenderProfile


class SenderProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, sender_profile_id: str) -> SenderProfile | None:
        stmt = select(SenderProfile).where(SenderProfile.id == sender_profile_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_from_email(self, from_email: str) -> SenderProfile | None:
        stmt = select(SenderProfile).where(
            func.lower(SenderProfile.from_email) == from_email.lower()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_profiles(self) -> list[SenderProfile]:
        stmt = select(SenderProfile).order_by(SenderProfile.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_profile(
        self,
        *,
        display_name: str,
        from_name: str,
        from_email: str,
        reply_to: str | None,
        domain_id: str,
        configuration_set_id: str | None,
        ip_pool_id: str | None,
        allowed_campaign_types: list[str],
        daily_send_limit: int,
    ) -> SenderProfile:
        profile = SenderProfile(
            display_name=display_name,
            from_name=from_name,
            from_email=from_email,
            reply_to=reply_to,
            domain_id=domain_id,
            configuration_set_id=configuration_set_id,
            ip_pool_id=ip_pool_id,
            allowed_campaign_types=allowed_campaign_types,
            daily_send_limit=daily_send_limit,
        )
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def update_profile(
        self,
        *,
        sender_profile_id: str,
        values: dict[str, object],
    ) -> bool:
        stmt = (
            update(SenderProfile)
            .where(SenderProfile.id == sender_profile_id)
            .values(**values)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def soft_delete(self, *, sender_profile_id: str, reason: str) -> bool:
        stmt = (
            update(SenderProfile)
            .where(SenderProfile.id == sender_profile_id)
            .values(
                is_active=False,
                paused_at=datetime.now(UTC),
                paused_reason=reason,
            )
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))
