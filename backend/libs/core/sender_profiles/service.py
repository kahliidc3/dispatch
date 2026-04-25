from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache

from libs.core.auth.repository import AuthRepository
from libs.core.auth.schemas import CurrentActor
from libs.core.config import get_settings
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.domains.repository import DomainRepository
from libs.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from libs.core.sender_profiles.models import SenderProfile
from libs.core.sender_profiles.repository import SenderProfileRepository
from libs.core.sender_profiles.schemas import (
    SenderProfileCreateRequest,
    SenderProfileDeleteRequest,
    SenderProfileUpdateRequest,
)


class SenderProfileService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._session_factory = get_session_factory()

    async def create_sender_profile(
        self,
        *,
        actor: CurrentActor,
        payload: SenderProfileCreateRequest,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SenderProfile:
        self._require_admin(actor)
        normalized_from_email = payload.from_email.strip().lower()
        reply_to = payload.reply_to.strip().lower() if payload.reply_to else None
        normalized_ip_pool_id: str | None = None
        if payload.ip_pool_id is not None:
            candidate_ip_pool_id = payload.ip_pool_id.strip()
            normalized_ip_pool_id = candidate_ip_pool_id or None

        async with UnitOfWork(self._session_factory) as uow:
            sender_repo = SenderProfileRepository(uow.require_session())
            domain_repo = DomainRepository(uow.require_session())

            existing = await sender_repo.get_by_from_email(normalized_from_email)
            if existing is not None:
                raise ConflictError("Sender profile from_email already exists")

            domain = await domain_repo.get_domain_by_id(payload.domain_id)
            if domain is None:
                raise NotFoundError("Domain not found")
            if domain.verification_status != "verified":
                raise ConflictError("Sender profile domain must be verified")
            if domain.reputation_status in {"burnt", "retired"}:
                raise ConflictError("Sender profile domain is not sendable")

            configuration_set_id = (
                payload.configuration_set_id or domain.default_configuration_set_id
            )
            if configuration_set_id is None:
                raise ConflictError("Domain is missing a default SES configuration set")

            configuration_set = await domain_repo.get_configuration_set_by_id(configuration_set_id)
            if configuration_set is None:
                raise NotFoundError("SES configuration set not found")

            if normalized_ip_pool_id:
                ip_pool = await domain_repo.get_ip_pool_by_id(normalized_ip_pool_id)
                if ip_pool is None:
                    raise NotFoundError("IP pool not found")
                if not ip_pool.is_active:
                    raise ConflictError("IP pool is not active")

            profile = await sender_repo.create_profile(
                display_name=payload.display_name.strip(),
                from_name=payload.from_name.strip(),
                from_email=normalized_from_email,
                reply_to=reply_to,
                domain_id=payload.domain_id,
                configuration_set_id=configuration_set_id,
                ip_pool_id=normalized_ip_pool_id,
                allowed_campaign_types=payload.allowed_campaign_types,
                daily_send_limit=payload.daily_send_limit,
            )

            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor.actor_type,
                actor_id=actor.user.id,
                action="sender_profile.create",
                resource_type="sender_profile",
                resource_id=profile.id,
                after_state={"from_email": profile.from_email, "domain_id": profile.domain_id},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return profile

    async def list_sender_profiles(self, *, actor: CurrentActor) -> list[SenderProfile]:
        self._require_admin(actor)
        async with self._session_factory() as session:
            repo = SenderProfileRepository(session)
            return await repo.list_profiles()

    async def update_sender_profile(
        self,
        *,
        actor: CurrentActor,
        sender_profile_id: str,
        payload: SenderProfileUpdateRequest,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SenderProfile:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            sender_repo = SenderProfileRepository(uow.require_session())
            domain_repo = DomainRepository(uow.require_session())
            profile = await sender_repo.get_by_id(sender_profile_id)
            if profile is None:
                raise NotFoundError("Sender profile not found")

            values: dict[str, object] = {}
            if payload.display_name is not None:
                values["display_name"] = payload.display_name.strip()
            if payload.from_name is not None:
                values["from_name"] = payload.from_name.strip()
            if payload.reply_to is not None:
                values["reply_to"] = payload.reply_to.strip().lower() if payload.reply_to else None
            if payload.allowed_campaign_types is not None:
                values["allowed_campaign_types"] = payload.allowed_campaign_types
            if payload.daily_send_limit is not None:
                values["daily_send_limit"] = payload.daily_send_limit
            if payload.configuration_set_id is not None:
                configuration_set = await domain_repo.get_configuration_set_by_id(
                    payload.configuration_set_id
                )
                if configuration_set is None:
                    raise NotFoundError("SES configuration set not found")
                values["configuration_set_id"] = payload.configuration_set_id
            if payload.ip_pool_id is not None:
                normalized_ip_pool_id = payload.ip_pool_id.strip()
                if normalized_ip_pool_id:
                    ip_pool = await domain_repo.get_ip_pool_by_id(normalized_ip_pool_id)
                    if ip_pool is None:
                        raise NotFoundError("IP pool not found")
                    if not ip_pool.is_active:
                        raise ConflictError("IP pool is not active")
                values["ip_pool_id"] = normalized_ip_pool_id or None
            if payload.is_active is not None:
                values["is_active"] = payload.is_active
                if payload.is_active:
                    values["paused_at"] = None
                    values["paused_reason"] = None
                else:
                    values["paused_at"] = datetime.now(UTC)
                    values["paused_reason"] = payload.paused_reason or "paused"
            if payload.paused_reason is not None and payload.is_active is None:
                values["paused_reason"] = payload.paused_reason

            if values:
                await sender_repo.update_profile(sender_profile_id=sender_profile_id, values=values)

            refreshed = await sender_repo.get_by_id(sender_profile_id)
            if refreshed is None:
                raise NotFoundError("Sender profile not found")

            audit_after_state: dict[str, object] | None = None
            if values:
                audit_after_state = {
                    key: value.isoformat() if isinstance(value, datetime) else value
                    for key, value in values.items()
                }

            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor.actor_type,
                actor_id=actor.user.id,
                action="sender_profile.update",
                resource_type="sender_profile",
                resource_id=refreshed.id,
                after_state=audit_after_state,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return refreshed

    async def delete_sender_profile(
        self,
        *,
        actor: CurrentActor,
        sender_profile_id: str,
        payload: SenderProfileDeleteRequest,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            repo = SenderProfileRepository(uow.require_session())
            profile = await repo.get_by_id(sender_profile_id)
            if profile is None:
                raise NotFoundError("Sender profile not found")

            deleted = await repo.soft_delete(
                sender_profile_id=sender_profile_id,
                reason=payload.reason,
            )
            if not deleted:
                raise NotFoundError("Sender profile not found")

            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor.actor_type,
                actor_id=actor.user.id,
                action="sender_profile.delete",
                resource_type="sender_profile",
                resource_id=sender_profile_id,
                after_state={"is_active": False, "paused_reason": payload.reason},
                ip_address=ip_address,
                user_agent=user_agent,
            )

    @staticmethod
    def _require_admin(actor: CurrentActor) -> None:
        if actor.user.role != "admin":
            raise PermissionDeniedError("Admin role required")


@lru_cache(maxsize=1)
def get_sender_profile_service() -> SenderProfileService:
    return SenderProfileService()


def reset_sender_profile_service_cache() -> None:
    get_sender_profile_service.cache_clear()
