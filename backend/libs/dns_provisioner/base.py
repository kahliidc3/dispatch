from __future__ import annotations

import asyncio
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, cast

import dns.asyncresolver
import dns.exception
import dns.resolver

from libs.core.config import Settings
from libs.core.domains.schemas import DnsRecordType
from libs.core.errors import ExternalServiceError, ValidationError
from libs.core.logging import get_logger

logger = get_logger("dns_provisioner.base")


@dataclass(frozen=True, slots=True)
class DNSZone:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class DNSRecordInput:
    record_type: str
    name: str
    value: str
    ttl: int = 300
    priority: int | None = None


class AuthenticationError(ExternalServiceError):
    code = "dns_authentication_error"
    default_message = "DNS provider authentication failed"


class RateLimitedError(ExternalServiceError):
    code = "dns_rate_limited"
    default_message = "DNS provider rate-limited the request"


class ZoneNotFoundError(ExternalServiceError):
    code = "dns_zone_not_found"
    default_message = "DNS zone was not found"


class RecordExistsError(ExternalServiceError):
    code = "dns_record_exists"
    default_message = "DNS record already exists with conflicting values"


class DNSProvisioner(Protocol):
    async def create_record(self, *, zone_id: str, record: DNSRecordInput) -> str: ...

    async def update_record(
        self,
        *,
        zone_id: str,
        record_id: str,
        record: DNSRecordInput,
    ) -> str: ...

    async def delete_record(self, *, zone_id: str, record_id: str) -> None: ...

    async def verify_record(self, *, zone_id: str, record: DNSRecordInput) -> bool: ...

    async def list_zones(self) -> list[DNSZone]: ...


def normalize_dns_value(value: str) -> str:
    return value.strip().strip('"').rstrip(".").lower()


class SecretProvider(Protocol):
    async def get_secret(self, *, secret_name: str) -> str: ...


class _AwsSecretsManagerClient(Protocol):
    def get_secret_value(self, **kwargs: object) -> dict[str, object]: ...


class AwsSecretsManagerSecretProvider:
    def __init__(
        self,
        settings: Settings,
        *,
        client: _AwsSecretsManagerClient | None = None,
    ) -> None:
        self._settings = settings
        self._client = client
        self._cache: dict[str, str] = {}

    async def get_secret(self, *, secret_name: str) -> str:
        normalized_name = secret_name.strip()
        if not normalized_name:
            raise ValidationError("secret_name is required")
        cached = self._cache.get(normalized_name)
        if cached is not None:
            return cached

        value = await asyncio.to_thread(self._get_secret_sync, normalized_name)
        self._cache[normalized_name] = value
        return value

    def _get_secret_sync(self, secret_name: str) -> str:
        client = self._client or self._build_client()
        try:
            payload = client.get_secret_value(SecretId=secret_name)
        except Exception as exc:
            raise ExternalServiceError("Failed to read secret from Secrets Manager") from exc

        secret_string = payload.get("SecretString")
        if isinstance(secret_string, str) and secret_string.strip():
            return secret_string.strip()

        secret_binary = payload.get("SecretBinary")
        if isinstance(secret_binary, (bytes, bytearray)):
            decoded = bytes(secret_binary).decode("utf-8").strip()
            if decoded:
                return decoded
        if isinstance(secret_binary, str) and secret_binary.strip():
            decoded = base64.b64decode(secret_binary.encode("utf-8")).decode("utf-8").strip()
            if decoded:
                return decoded

        raise ValidationError("Secret exists but does not contain a readable value")

    def _build_client(self) -> _AwsSecretsManagerClient:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover
            raise ValidationError("boto3 is required for Secrets Manager access") from exc

        kwargs: dict[str, object] = {"region_name": self._settings.aws_region}
        if self._settings.aws_access_key_id and self._settings.aws_secret_access_key:
            kwargs["aws_access_key_id"] = self._settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = self._settings.aws_secret_access_key
            if self._settings.aws_session_token:
                kwargs["aws_session_token"] = self._settings.aws_session_token

        if self._settings.app_env in {"local", "test"}:
            kwargs["endpoint_url"] = self._settings.localstack_endpoint_url

        return cast(_AwsSecretsManagerClient, boto3.client("secretsmanager", **kwargs))


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
