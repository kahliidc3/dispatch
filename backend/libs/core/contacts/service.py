from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from libs.core.auth.repository import AuthRepository
from libs.core.auth.schemas import CurrentActor
from libs.core.config import Settings, get_settings
from libs.core.contacts.models import Contact, Preference
from libs.core.contacts.repository import ContactRepository
from libs.core.contacts.schemas import (
    ContactCreateRequest,
    ContactPreferenceUpdateRequest,
    ContactQueryParams,
    ContactUpdateRequest,
)
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from libs.core.suppression.service import get_suppression_service

_TERMINAL_CONTACT_STATUSES = {"bounced", "complained", "unsubscribed", "suppressed", "deleted"}


@dataclass(slots=True)
class ContactListResult:
    items: list[Contact]
    total: int
    limit: int
    offset: int


class ContactService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._session_factory = get_session_factory()
        self._unsubscribe_serializer = URLSafeTimedSerializer(
            settings.secret_key,
            salt="dispatch-public-unsubscribe",
        )

    async def create_contact(
        self,
        *,
        actor: CurrentActor,
        payload: ContactCreateRequest,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Contact:
        self._require_admin(actor)
        email = self._normalize_email(payload.email)
        email_domain = self._extract_domain(email)

        async with UnitOfWork(self._session_factory) as uow:
            repo = ContactRepository(uow.require_session())
            existing = await repo.get_contact_by_email(email)
            if existing is not None:
                raise ConflictError("A contact with this email already exists")

            contact = await repo.create_contact(
                email=email,
                email_domain=email_domain,
                first_name=self._clean_optional_text(payload.first_name),
                last_name=self._clean_optional_text(payload.last_name),
                company=self._clean_optional_text(payload.company),
                title=self._clean_optional_text(payload.title),
                phone=self._clean_optional_text(payload.phone),
                country_code=self._clean_optional_text(payload.country_code),
                timezone=self._clean_optional_text(payload.timezone),
                custom_attributes=dict(payload.custom_attributes),
            )
            await repo.create_contact_source(
                contact_id=contact.id,
                source_type=payload.source_type,
                source_detail=self._clean_optional_text(payload.source_detail),
                source_list=self._clean_optional_text(payload.source_list),
            )
            await repo.upsert_subscription_status(
                contact_id=contact.id,
                channel="email",
                status="subscribed",
                reason="initial_create",
            )
            await repo.upsert_preferences(
                contact_id=contact.id,
                campaign_types=[],
                max_frequency_per_week=None,
                language="en",
            )
            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor.actor_type,
                actor_id=actor.user.id,
                action="contact.create",
                resource_type="contact",
                resource_id=contact.id,
                after_state={
                    "email_sha256": self._email_hash(contact.email),
                    "source_type": payload.source_type,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return contact

    async def list_contacts(
        self,
        *,
        actor: CurrentActor,
        query: ContactQueryParams,
    ) -> ContactListResult:
        self._require_admin(actor)
        async with self._session_factory() as session:
            repo = ContactRepository(session)
            items = await repo.list_contacts(
                limit=query.limit,
                offset=query.offset,
                lifecycle_status=query.lifecycle_status,
                search=query.search,
                email_domain=query.email_domain,
            )
            total = await repo.count_contacts(
                lifecycle_status=query.lifecycle_status,
                search=query.search,
                email_domain=query.email_domain,
            )
            return ContactListResult(
                items=items,
                total=total,
                limit=query.limit,
                offset=query.offset,
            )

    async def get_contact(self, *, actor: CurrentActor, contact_id: str) -> Contact:
        self._require_admin(actor)
        async with self._session_factory() as session:
            repo = ContactRepository(session)
            contact = await repo.get_contact_by_id(contact_id)
            if contact is None:
                raise NotFoundError("Contact not found")
            return contact

    async def update_contact(
        self,
        *,
        actor: CurrentActor,
        contact_id: str,
        payload: ContactUpdateRequest,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Contact:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            repo = ContactRepository(uow.require_session())
            contact = await repo.get_contact_by_id(contact_id)
            if contact is None:
                raise NotFoundError("Contact not found")

            values: dict[str, object] = {}
            field_set = payload.model_fields_set
            for field_name in (
                "first_name",
                "last_name",
                "company",
                "title",
                "phone",
                "country_code",
                "timezone",
            ):
                if field_name in field_set:
                    values[field_name] = self._clean_optional_text(getattr(payload, field_name))

            if "custom_attributes" in field_set and payload.custom_attributes is not None:
                values["custom_attributes"] = dict(payload.custom_attributes)

            if "lifecycle_status" in field_set and payload.lifecycle_status is not None:
                self._assert_valid_lifecycle_transition(
                    current_status=contact.lifecycle_status,
                    target_status=payload.lifecycle_status,
                )
                values["lifecycle_status"] = payload.lifecycle_status

            if values:
                await repo.update_contact(contact_id=contact_id, values=values)

            refreshed = await repo.get_contact_by_id(contact_id)
            if refreshed is None:
                raise NotFoundError("Contact not found")

            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor.actor_type,
                actor_id=actor.user.id,
                action="contact.update",
                resource_type="contact",
                resource_id=refreshed.id,
                after_state={
                    "changed_fields": sorted(values.keys()),
                    "lifecycle_status": values.get("lifecycle_status", refreshed.lifecycle_status),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return refreshed

    async def delete_contact(
        self,
        *,
        actor: CurrentActor,
        contact_id: str,
        reason: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        self._require_admin(actor)
        if not reason.strip():
            raise ValidationError("Deletion reason is required")

        async with UnitOfWork(self._session_factory) as uow:
            repo = ContactRepository(uow.require_session())
            contact = await repo.get_contact_by_id(contact_id)
            if contact is None:
                raise NotFoundError("Contact not found")

            deleted = await repo.delete_contact(contact_id=contact.id)
            if not deleted:
                raise NotFoundError("Contact not found")

            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor.actor_type,
                actor_id=actor.user.id,
                action="contact.hard_delete",
                resource_type="contact",
                resource_id=contact.id,
                before_state={
                    "lifecycle_status": contact.lifecycle_status,
                    "email_sha256": self._email_hash(contact.email),
                },
                after_state={"deleted": True, "reason": reason.strip()},
                ip_address=ip_address,
                user_agent=user_agent,
            )

    async def unsubscribe_contact(
        self,
        *,
        actor: CurrentActor,
        contact_id: str,
        reason: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Contact:
        self._require_admin(actor)
        contact = await self._unsubscribe_internal(
            contact_id=contact_id,
            reason=reason,
            actor_type=actor.actor_type,
            actor_id=actor.user.id,
            action="contact.unsubscribe",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await get_suppression_service().upsert_system_suppression(
            email=contact.email,
            reason_code="unsubscribe",
            source="contact_unsubscribe",
        )
        return contact

    async def unsubscribe_public(
        self,
        *,
        token: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Contact:
        payload = self._decode_unsubscribe_token(token)
        contact_id = payload.get("contact_id")
        if not isinstance(contact_id, str) or not contact_id:
            raise AuthenticationError("Invalid unsubscribe token")
        contact = await self._unsubscribe_internal(
            contact_id=contact_id,
            reason="public_unsubscribe",
            actor_type="system",
            actor_id=None,
            action="contact.unsubscribe.public",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await get_suppression_service().upsert_system_suppression(
            email=contact.email,
            reason_code="unsubscribe",
            source="public_unsubscribe",
        )
        return contact

    async def create_unsubscribe_token(self, *, actor: CurrentActor, contact_id: str) -> str:
        self._require_admin(actor)
        async with self._session_factory() as session:
            repo = ContactRepository(session)
            contact = await repo.get_contact_by_id(contact_id)
            if contact is None:
                raise NotFoundError("Contact not found")
            return self._unsubscribe_serializer.dumps({"contact_id": contact.id})

    async def get_preferences(self, *, actor: CurrentActor, contact_id: str) -> Preference:
        self._require_admin(actor)
        async with self._session_factory() as session:
            repo = ContactRepository(session)
            contact = await repo.get_contact_by_id(contact_id)
            if contact is None:
                raise NotFoundError("Contact not found")
            preference = await repo.get_preferences(contact_id=contact_id)
            if preference is None:
                raise NotFoundError("Contact preferences not found")
            return preference

    async def set_preferences(
        self,
        *,
        actor: CurrentActor,
        contact_id: str,
        payload: ContactPreferenceUpdateRequest,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Preference:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            repo = ContactRepository(uow.require_session())
            contact = await repo.get_contact_by_id(contact_id)
            if contact is None:
                raise NotFoundError("Contact not found")

            preferences = await repo.upsert_preferences(
                contact_id=contact_id,
                campaign_types=payload.campaign_types,
                max_frequency_per_week=payload.max_frequency_per_week,
                language=payload.language.strip().lower(),
            )
            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor.actor_type,
                actor_id=actor.user.id,
                action="contact.preferences.update",
                resource_type="contact",
                resource_id=contact_id,
                after_state={
                    "campaign_types_count": len(payload.campaign_types),
                    "language": preferences.language,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return preferences

    async def _unsubscribe_internal(
        self,
        *,
        contact_id: str,
        reason: str,
        actor_type: str,
        actor_id: str | None,
        action: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Contact:
        normalized_reason = reason.strip() or "unsubscribe"
        async with UnitOfWork(self._session_factory) as uow:
            repo = ContactRepository(uow.require_session())
            contact = await repo.get_contact_by_id(contact_id)
            if contact is None:
                raise NotFoundError("Contact not found")

            if contact.lifecycle_status != "unsubscribed":
                self._assert_valid_lifecycle_transition(
                    current_status=contact.lifecycle_status,
                    target_status="unsubscribed",
                )
                await repo.update_contact(
                    contact_id=contact.id,
                    values={"lifecycle_status": "unsubscribed"},
                )

            await repo.upsert_subscription_status(
                contact_id=contact.id,
                channel="email",
                status="unsubscribed",
                reason=normalized_reason,
            )
            refreshed = await repo.get_contact_by_id(contact.id)
            if refreshed is None:
                raise NotFoundError("Contact not found")

            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                resource_type="contact",
                resource_id=refreshed.id,
                after_state={
                    "lifecycle_status": refreshed.lifecycle_status,
                    "reason": normalized_reason,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return refreshed

    def _decode_unsubscribe_token(self, token: str) -> dict[str, Any]:
        try:
            payload = self._unsubscribe_serializer.loads(
                token,
                max_age=self._settings.unsubscribe_token_ttl_seconds,
            )
        except (BadSignature, SignatureExpired) as exc:
            raise AuthenticationError("Invalid unsubscribe token") from exc
        if not isinstance(payload, dict):
            raise AuthenticationError("Invalid unsubscribe token")
        return payload

    @staticmethod
    def _assert_valid_lifecycle_transition(*, current_status: str, target_status: str) -> None:
        if current_status == target_status:
            return
        if current_status != "active":
            raise ConflictError(
                f"Cannot transition contact lifecycle from {current_status} to {target_status}"
            )
        if target_status not in _TERMINAL_CONTACT_STATUSES:
            raise ValidationError("Unsupported lifecycle status transition")

    @staticmethod
    def _normalize_email(value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValidationError("Invalid email address")
        local, _, domain = normalized.partition("@")
        if not local or "." not in domain:
            raise ValidationError("Invalid email address")
        return normalized

    @staticmethod
    def _extract_domain(email: str) -> str:
        return email.partition("@")[2]

    @staticmethod
    def _email_hash(email: str) -> str:
        return hashlib.sha256(email.encode("utf-8")).hexdigest()

    @staticmethod
    def _clean_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None

    @staticmethod
    def _require_admin(actor: CurrentActor) -> None:
        if actor.user.role != "admin":
            raise PermissionDeniedError("Admin role required")


@lru_cache(maxsize=1)
def get_contact_service() -> ContactService:
    return ContactService(get_settings())


def reset_contact_service_cache() -> None:
    get_contact_service.cache_clear()
