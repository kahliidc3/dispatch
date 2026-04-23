from __future__ import annotations

from abc import ABC, abstractmethod

import dns.asyncresolver
import dns.exception
import dns.resolver

from libs.core.domains.schemas import DnsRecordType


def normalize_dns_value(value: str) -> str:
    return value.strip().strip('"').rstrip(".").lower()


class DNSVerificationAdapter(ABC):
    @abstractmethod
    async def lookup(self, *, record_type: DnsRecordType, name: str) -> list[str]:
        """Returns normalized values for the requested DNS record."""


class DnsPythonVerificationAdapter(DNSVerificationAdapter):
    """Read-only DNS verification helper for MVP manual DNS checks."""

    def __init__(self) -> None:
        self._resolver = dns.asyncresolver.Resolver(configure=True)

    async def lookup(self, *, record_type: DnsRecordType, name: str) -> list[str]:
        try:
            answers = await self._resolver.resolve(name, record_type.value)
        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
            dns.resolver.LifetimeTimeout,
        ):
            return []

        if record_type is DnsRecordType.MX:
            return [normalize_dns_value(str(answer.exchange)) for answer in answers]
        if record_type is DnsRecordType.TXT:
            normalized: list[str] = []
            for answer in answers:
                text_value = "".join(part.decode("utf-8") for part in answer.strings)
                normalized.append(normalize_dns_value(text_value))
            return normalized

        return [normalize_dns_value(str(answer)) for answer in answers]
