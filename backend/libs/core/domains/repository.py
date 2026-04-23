from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.domains.models import Domain, DomainDnsRecord, IPPool, SESConfigurationSet
from libs.core.domains.schemas import ExpectedDnsRecord


class DomainRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_domain_by_name(self, name: str) -> Domain | None:
        stmt = select(Domain).where(func.lower(Domain.name) == name.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_domain_by_id(self, domain_id: str) -> Domain | None:
        stmt = select(Domain).where(Domain.id == domain_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_domains(self) -> list[Domain]:
        stmt = select(Domain).order_by(Domain.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_domain(
        self,
        *,
        name: str,
        parent_domain: str | None,
        dns_provider: str,
        ses_region: str,
        mail_from_domain: str,
        default_configuration_set_id: str | None,
    ) -> Domain:
        domain = Domain(
            name=name,
            parent_domain=parent_domain,
            dns_provider=dns_provider,
            ses_region=ses_region,
            mail_from_domain=mail_from_domain,
            default_configuration_set_id=default_configuration_set_id,
        )
        self.session.add(domain)
        await self.session.flush()
        return domain

    async def update_domain_status(
        self,
        *,
        domain_id: str,
        verification_status: str,
        spf_status: str,
        dkim_status: str,
        dmarc_status: str,
    ) -> None:
        stmt = (
            update(Domain)
            .where(Domain.id == domain_id)
            .values(
                verification_status=verification_status,
                spf_status=spf_status,
                dkim_status=dkim_status,
                dmarc_status=dmarc_status,
            )
        )
        await self.session.execute(stmt)

    async def retire_domain(self, *, domain_id: str, reason: str) -> bool:
        stmt = (
            update(Domain)
            .where(Domain.id == domain_id)
            .values(
                reputation_status="retired",
                verification_status="disabled",
                retired_at=datetime.now(UTC),
                retirement_reason=reason,
            )
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def create_dns_records(
        self,
        *,
        domain_id: str,
        records: list[ExpectedDnsRecord],
    ) -> list[DomainDnsRecord]:
        created: list[DomainDnsRecord] = []
        for record in records:
            item = DomainDnsRecord(
                domain_id=domain_id,
                record_type=record.record_type.value,
                name=record.name,
                value=record.value,
                purpose=record.purpose,
                priority=record.priority,
            )
            created.append(item)
            self.session.add(item)
        await self.session.flush()
        return created

    async def list_dns_records_for_domain(self, domain_id: str) -> list[DomainDnsRecord]:
        stmt = (
            select(DomainDnsRecord)
            .where(DomainDnsRecord.domain_id == domain_id)
            .where(DomainDnsRecord.is_active.is_(True))
            .order_by(DomainDnsRecord.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_dns_record_verification(
        self,
        *,
        record_id: str,
        is_verified: bool,
    ) -> None:
        values: dict[str, object] = {"verification_status": "verified" if is_verified else "failed"}
        if is_verified:
            values["last_verified_at"] = datetime.now(UTC)

        stmt = update(DomainDnsRecord).where(DomainDnsRecord.id == record_id).values(**values)
        await self.session.execute(stmt)

    async def get_configuration_set_by_id(
        self,
        configuration_set_id: str,
    ) -> SESConfigurationSet | None:
        stmt = select(SESConfigurationSet).where(SESConfigurationSet.id == configuration_set_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_configuration_set_by_name(self, name: str) -> SESConfigurationSet | None:
        stmt = select(SESConfigurationSet).where(
            func.lower(SESConfigurationSet.name) == name.lower()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_configuration_set(
        self,
        *,
        name: str,
        ses_region: str,
        event_destination_sns_topic_arn: str | None,
    ) -> SESConfigurationSet:
        configuration_set = SESConfigurationSet(
            name=name,
            ses_region=ses_region,
            event_destination_sns_topic_arn=event_destination_sns_topic_arn,
        )
        self.session.add(configuration_set)
        await self.session.flush()
        return configuration_set

    async def list_configuration_sets(self) -> list[SESConfigurationSet]:
        stmt = select(SESConfigurationSet).order_by(SESConfigurationSet.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_ip_pool_by_id(self, ip_pool_id: str) -> IPPool | None:
        stmt = select(IPPool).where(IPPool.id == ip_pool_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_ip_pool_by_name(self, name: str) -> IPPool | None:
        stmt = select(IPPool).where(func.lower(IPPool.name) == name.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_ip_pool(
        self,
        *,
        name: str,
        ses_pool_name: str,
        dedicated_ips: list[str],
        traffic_weight: int,
    ) -> IPPool:
        pool = IPPool(
            name=name,
            ses_pool_name=ses_pool_name,
            dedicated_ips=dedicated_ips,
            traffic_weight=traffic_weight,
        )
        self.session.add(pool)
        await self.session.flush()
        return pool

    async def list_ip_pools(self) -> list[IPPool]:
        stmt = select(IPPool).order_by(IPPool.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
