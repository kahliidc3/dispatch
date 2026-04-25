from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(slots=True, frozen=True)
class PostmasterDomainData:
    """Value type returned by the Postmaster adapter for a single domain+day."""

    domain_reputation: str | None
    spam_rate: Decimal | None
    dkim_success_ratio: Decimal | None
    spf_success_ratio: Decimal | None
    dmarc_success_ratio: Decimal | None
    inbound_encryption_ratio: Decimal | None
    raw_json: dict[str, object]


class PostmasterAdapter(Protocol):
    """Interface for fetching data from Google Postmaster Tools."""

    async def fetch_domain_reputation(
        self,
        *,
        domain_name: str,
        report_date: date,
    ) -> PostmasterDomainData: ...


class NoopPostmasterAdapter:
    """Default no-op adapter when Postmaster is not configured."""

    async def fetch_domain_reputation(
        self,
        *,
        domain_name: str,
        report_date: date,
    ) -> PostmasterDomainData:
        _ = (domain_name, report_date)
        return PostmasterDomainData(
            domain_reputation=None,
            spam_rate=None,
            dkim_success_ratio=None,
            spf_success_ratio=None,
            dmarc_success_ratio=None,
            inbound_encryption_ratio=None,
            raw_json={},
        )
