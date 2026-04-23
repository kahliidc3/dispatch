from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from libs.core.auth.repository import AuthRepository
from libs.core.auth.schemas import CurrentActor
from libs.core.config import Settings, get_settings
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain, DomainDnsRecord, IPPool, SESConfigurationSet
from libs.core.domains.repository import DomainRepository
from libs.core.domains.schemas import (
    DnsRecordType,
    ExpectedDnsRecord,
    IPPoolCreateRequest,
    SESConfigurationSetCreateRequest,
)
from libs.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from libs.dns_provisioner.base import (
    DnsPythonVerificationAdapter,
    DNSVerificationAdapter,
    normalize_dns_value,
)


@dataclass(slots=True)
class DomainDetail:
    domain: Domain
    dns_records: list[DomainDnsRecord]


@dataclass(slots=True)
class DomainVerificationResult:
    domain: Domain
    dns_records: list[DomainDnsRecord]
    fully_verified: bool

    @property
    def verified_records(self) -> int:
        return sum(1 for record in self.dns_records if record.verification_status == "verified")

    @property
    def total_records(self) -> int:
        return len(self.dns_records)


class DomainService:
    def __init__(
        self,
        settings: Settings,
        *,
        dns_verifier: DNSVerificationAdapter | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = get_session_factory()
        self._dns_verifier = dns_verifier or DnsPythonVerificationAdapter()

    async def create_domain(
        self,
        *,
        actor: CurrentActor,
        name: str,
        dns_provider: str,
        parent_domain: str | None,
        ses_region: str,
        default_configuration_set_name: str | None,
        event_destination_sns_topic_arn: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> DomainDetail:
        self._require_admin(actor)

        normalized_name = self._normalize_domain_name(name)
        normalized_parent = self._normalize_domain_name(parent_domain) if parent_domain else None
        if normalized_parent and normalized_parent == normalized_name:
            raise ValidationError("parent_domain cannot be the same as name")

        if dns_provider not in {"cloudflare", "route53", "godaddy", "manual"}:
            raise ValidationError("Unsupported dns_provider")

        config_set_name = default_configuration_set_name or f"{normalized_name}-default"
        mail_from_domain = f"mail.{normalized_name}"
        expected_records = self.build_expected_dns_records(
            domain_name=normalized_name,
            parent_domain=normalized_parent,
            ses_region=ses_region,
            mail_from_domain=mail_from_domain,
        )

        async with UnitOfWork(self._session_factory) as uow:
            repo = DomainRepository(uow.require_session())
            existing = await repo.get_domain_by_name(normalized_name)
            if existing is not None:
                raise ConflictError("A domain with this name already exists")

            configuration_set = await repo.get_configuration_set_by_name(config_set_name)
            if configuration_set is None:
                configuration_set = await repo.create_configuration_set(
                    name=config_set_name,
                    ses_region=ses_region,
                    event_destination_sns_topic_arn=event_destination_sns_topic_arn,
                )

            domain = await repo.create_domain(
                name=normalized_name,
                parent_domain=normalized_parent,
                dns_provider=dns_provider,
                ses_region=ses_region,
                mail_from_domain=mail_from_domain,
                default_configuration_set_id=configuration_set.id,
            )
            records = await repo.create_dns_records(domain_id=domain.id, records=expected_records)
            await self._write_audit_log(
                repo=repo,
                actor=actor,
                action="domain.create",
                resource_type="domain",
                resource_id=domain.id,
                after_state={
                    "name": domain.name,
                    "dns_provider": domain.dns_provider,
                    "default_configuration_set_id": domain.default_configuration_set_id,
                    "dns_record_count": len(records),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return DomainDetail(domain=domain, dns_records=records)

    async def list_domains(self) -> list[DomainDetail]:
        async with self._session_factory() as session:
            repo = DomainRepository(session)
            domains = await repo.list_domains()
            details: list[DomainDetail] = []
            for domain in domains:
                records = await repo.list_dns_records_for_domain(domain.id)
                details.append(DomainDetail(domain=domain, dns_records=records))
            return details

    async def get_domain(self, domain_id: str) -> DomainDetail:
        async with self._session_factory() as session:
            repo = DomainRepository(session)
            domain = await repo.get_domain_by_id(domain_id)
            if domain is None:
                raise NotFoundError("Domain not found")
            records = await repo.list_dns_records_for_domain(domain.id)
            return DomainDetail(domain=domain, dns_records=records)

    async def verify_domain(
        self,
        *,
        actor: CurrentActor,
        domain_id: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> DomainVerificationResult:
        self._require_admin(actor)
        return await self._verify_domain_internal(
            domain_id=domain_id,
            actor_type=actor.actor_type,
            actor_id=actor.user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def verify_domain_system(self, domain_id: str) -> DomainVerificationResult:
        return await self._verify_domain_internal(
            domain_id=domain_id,
            actor_type="system",
            actor_id=None,
            ip_address=None,
            user_agent="celery:verify_domain_dns",
        )

    async def retire_domain(
        self,
        *,
        actor: CurrentActor,
        domain_id: str,
        reason: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> DomainDetail:
        self._require_admin(actor)
        if not reason.strip():
            raise ValidationError("Retirement reason is required")

        async with UnitOfWork(self._session_factory) as uow:
            repo = DomainRepository(uow.require_session())
            domain = await repo.get_domain_by_id(domain_id)
            if domain is None:
                raise NotFoundError("Domain not found")

            retired = await repo.retire_domain(domain_id=domain.id, reason=reason)
            if not retired:
                raise NotFoundError("Domain not found")

            refreshed = await repo.get_domain_by_id(domain.id)
            if refreshed is None:
                raise NotFoundError("Domain not found")

            records = await repo.list_dns_records_for_domain(refreshed.id)
            await self._write_audit_log(
                repo=repo,
                actor=actor,
                action="domain.retire",
                resource_type="domain",
                resource_id=refreshed.id,
                before_state={"reputation_status": domain.reputation_status},
                after_state={"reputation_status": "retired", "reason": reason},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return DomainDetail(domain=refreshed, dns_records=records)

    async def create_configuration_set(
        self,
        *,
        actor: CurrentActor,
        payload: SESConfigurationSetCreateRequest,
    ) -> SESConfigurationSet:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            repo = DomainRepository(uow.require_session())
            existing = await repo.get_configuration_set_by_name(payload.name)
            if existing is not None:
                raise ConflictError("Configuration set name already exists")
            return await repo.create_configuration_set(
                name=payload.name.strip(),
                ses_region=payload.ses_region.strip(),
                event_destination_sns_topic_arn=payload.event_destination_sns_topic_arn,
            )

    async def list_configuration_sets(self) -> list[SESConfigurationSet]:
        async with self._session_factory() as session:
            repo = DomainRepository(session)
            return await repo.list_configuration_sets()

    async def create_ip_pool(self, *, actor: CurrentActor, payload: IPPoolCreateRequest) -> IPPool:
        self._require_admin(actor)
        async with UnitOfWork(self._session_factory) as uow:
            repo = DomainRepository(uow.require_session())
            existing = await repo.get_ip_pool_by_name(payload.name)
            if existing is not None:
                raise ConflictError("IP pool name already exists")
            return await repo.create_ip_pool(
                name=payload.name.strip(),
                ses_pool_name=payload.ses_pool_name.strip(),
                dedicated_ips=[ip.strip() for ip in payload.dedicated_ips if ip.strip()],
                traffic_weight=payload.traffic_weight,
            )

    async def list_ip_pools(self) -> list[IPPool]:
        async with self._session_factory() as session:
            repo = DomainRepository(session)
            return await repo.list_ip_pools()

    def build_expected_dns_records(
        self,
        *,
        domain_name: str,
        parent_domain: str | None,
        ses_region: str,
        mail_from_domain: str,
    ) -> list[ExpectedDnsRecord]:
        normalized_domain = self._normalize_domain_name(domain_name)
        normalized_parent = (
            self._normalize_domain_name(parent_domain)
            if parent_domain
            else normalized_domain
        )
        normalized_mail_from = self._normalize_domain_name(mail_from_domain)

        return [
            ExpectedDnsRecord(
                record_type=DnsRecordType.TXT,
                name=normalized_domain,
                value="v=spf1 include:amazonses.com -all",
                purpose="spf",
            ),
            ExpectedDnsRecord(
                record_type=DnsRecordType.CNAME,
                name=f"selector1._domainkey.{normalized_domain}",
                value=f"selector1-{normalized_domain}.dkim.amazonses.com",
                purpose="dkim",
            ),
            ExpectedDnsRecord(
                record_type=DnsRecordType.CNAME,
                name=f"selector2._domainkey.{normalized_domain}",
                value=f"selector2-{normalized_domain}.dkim.amazonses.com",
                purpose="dkim",
            ),
            ExpectedDnsRecord(
                record_type=DnsRecordType.CNAME,
                name=f"selector3._domainkey.{normalized_domain}",
                value=f"selector3-{normalized_domain}.dkim.amazonses.com",
                purpose="dkim",
            ),
            ExpectedDnsRecord(
                record_type=DnsRecordType.TXT,
                name=f"_dmarc.{normalized_domain}",
                value=f"v=DMARC1; p=none; rua=mailto:dmarc@{normalized_parent}",
                purpose="dmarc",
            ),
            ExpectedDnsRecord(
                record_type=DnsRecordType.MX,
                name=normalized_mail_from,
                value=f"feedback-smtp.{ses_region}.amazonses.com",
                purpose="mail_from",
                priority=10,
            ),
            ExpectedDnsRecord(
                record_type=DnsRecordType.TXT,
                name=normalized_mail_from,
                value="v=spf1 include:amazonses.com -all",
                purpose="mail_from",
            ),
        ]

    async def _verify_domain_internal(
        self,
        *,
        domain_id: str,
        actor_type: str,
        actor_id: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> DomainVerificationResult:
        async with UnitOfWork(self._session_factory) as uow:
            repo = DomainRepository(uow.require_session())
            domain = await repo.get_domain_by_id(domain_id)
            if domain is None:
                raise NotFoundError("Domain not found")
            if domain.reputation_status in {"burnt", "retired"}:
                raise ConflictError(
                    f"Domain cannot be verified in state {domain.reputation_status}"
                )

            records = await repo.list_dns_records_for_domain(domain.id)
            if not records:
                raise ValidationError("Domain has no DNS records to verify")

            verification_results: dict[str, bool] = {}
            for record in records:
                verified = await self._verify_dns_record(record)
                await repo.update_dns_record_verification(record_id=record.id, is_verified=verified)
                verification_results[record.id] = verified

            refreshed_records = await repo.list_dns_records_for_domain(domain.id)
            spf_status = self._purpose_status(refreshed_records, purpose="spf")
            dkim_status = self._purpose_status(refreshed_records, purpose="dkim")
            dmarc_status = self._purpose_status(refreshed_records, purpose="dmarc")
            mail_from_status = self._purpose_status(refreshed_records, purpose="mail_from")
            fully_verified = (
                spf_status == "verified"
                and dkim_status == "verified"
                and dmarc_status == "verified"
                and mail_from_status == "verified"
            )
            verification_status = "verified" if fully_verified else "pending"
            await repo.update_domain_status(
                domain_id=domain.id,
                verification_status=verification_status,
                spf_status=spf_status,
                dkim_status=dkim_status,
                dmarc_status=dmarc_status,
            )

            refreshed_domain = await repo.get_domain_by_id(domain.id)
            if refreshed_domain is None:
                raise NotFoundError("Domain not found")

            await AuthRepository(uow.require_session()).write_audit_log(
                actor_type=actor_type,
                actor_id=actor_id,
                action="domain.verify",
                resource_type="domain",
                resource_id=refreshed_domain.id,
                after_state={
                    "verification_status": refreshed_domain.verification_status,
                    "spf_status": refreshed_domain.spf_status,
                    "dkim_status": refreshed_domain.dkim_status,
                    "dmarc_status": refreshed_domain.dmarc_status,
                    "fully_verified": fully_verified,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return DomainVerificationResult(
                domain=refreshed_domain,
                dns_records=refreshed_records,
                fully_verified=fully_verified,
            )

    async def _verify_dns_record(self, record: DomainDnsRecord) -> bool:
        record_type = DnsRecordType(record.record_type.upper())
        observed = await self._dns_verifier.lookup(record_type=record_type, name=record.name)
        expected = normalize_dns_value(record.value)
        if record_type is DnsRecordType.MX:
            return any(value.endswith(expected) for value in observed)
        return expected in observed

    @staticmethod
    def _purpose_status(records: list[DomainDnsRecord], *, purpose: str) -> str:
        scoped = [record for record in records if record.purpose == purpose and record.is_active]
        if not scoped:
            return "pending"
        if all(record.verification_status == "verified" for record in scoped):
            return "verified"
        return "pending"

    async def _write_audit_log(
        self,
        *,
        repo: DomainRepository,
        actor: CurrentActor,
        action: str,
        resource_type: str,
        resource_id: str | None,
        after_state: dict[str, object] | None = None,
        before_state: dict[str, object] | None = None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        await AuthRepository(repo.session).write_audit_log(
            actor_type=actor.actor_type,
            actor_id=actor.user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            after_state=after_state,
            before_state=before_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def _normalize_domain_name(value: str | None) -> str:
        if value is None:
            raise ValidationError("Domain name is required")
        normalized = value.strip().lower().rstrip(".")
        if not normalized or "." not in normalized:
            raise ValidationError("Invalid domain format")
        return normalized

    @staticmethod
    def _require_admin(actor: CurrentActor) -> None:
        if actor.user.role != "admin":
            raise PermissionDeniedError("Admin role required")


@lru_cache(maxsize=1)
def get_domain_service() -> DomainService:
    return DomainService(get_settings())


def reset_domain_service_cache() -> None:
    get_domain_service.cache_clear()
