from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

from libs.core.config import Settings, get_settings
from libs.ses_client.errors import (
    SesConfigurationError,
    SesError,
    SesTerminalError,
    map_ses_error,
)
from libs.ses_client.metrics import NoopSesMetricsRecorder, SesMetricsRecorder
from libs.ses_client.retries import run_with_retry


@dataclass(slots=True)
class SesSendEmailRequest:
    from_email: str
    to_email: str
    subject: str
    body_text: str
    body_html: str | None = None
    configuration_set_name: str | None = None
    tags: list[tuple[str, str]] = field(default_factory=list)
    headers: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class SesSendRawEmailRequest:
    source: str
    to_addresses: list[str]
    raw_data: bytes
    configuration_set_name: str | None = None
    tags: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class SesSendEmailResponse:
    message_id: str
    request_id: str | None = None


@dataclass(slots=True)
class SesSuppressedDestination:
    email: str
    reason: str


class SesTransport(Protocol):
    async def send_email(self, request: SesSendEmailRequest) -> SesSendEmailResponse: ...

    async def send_raw_email(self, request: SesSendRawEmailRequest) -> SesSendEmailResponse: ...

    async def get_suppressed_destination(
        self,
        *,
        email: str,
    ) -> SesSuppressedDestination | None: ...


class Boto3SesTransport:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_email(self, request: SesSendEmailRequest) -> SesSendEmailResponse:
        return await asyncio.to_thread(self._send_email_sync, request)

    async def send_raw_email(self, request: SesSendRawEmailRequest) -> SesSendEmailResponse:
        return await asyncio.to_thread(self._send_raw_email_sync, request)

    async def get_suppressed_destination(self, *, email: str) -> SesSuppressedDestination | None:
        return await asyncio.to_thread(self._get_suppressed_destination_sync, email)

    def _send_email_sync(self, request: SesSendEmailRequest) -> SesSendEmailResponse:
        client = self._build_client()
        payload: dict[str, object] = {
            "FromEmailAddress": request.from_email,
            "Destination": {"ToAddresses": [request.to_email]},
            "Content": {
                "Simple": {
                    "Subject": {"Data": request.subject},
                    "Body": {
                        "Text": {"Data": request.body_text},
                        **(
                            {"Html": {"Data": request.body_html}}
                            if request.body_html is not None
                            else {}
                        ),
                    },
                }
            },
        }
        if request.configuration_set_name is not None:
            payload["ConfigurationSetName"] = request.configuration_set_name
        if request.tags:
            payload["EmailTags"] = [
                {"Name": key, "Value": value}
                for key, value in request.tags
            ]
        if request.headers:
            simple = payload["Content"]["Simple"]  # type: ignore[index]
            simple["Headers"] = [  # type: ignore[index]
                {"Name": key, "Value": value}
                for key, value in request.headers
            ]

        try:
            response = client.send_email(**payload)
        except Exception as exc:  # pragma: no cover - exercised by contract tests
            raise self._map_exception(exc) from exc

        message_id = str(response.get("MessageId") or "").strip()
        if not message_id:
            raise SesTerminalError("SES response did not include MessageId")

        response_metadata = response.get("ResponseMetadata") or {}
        request_id = response_metadata.get("RequestId")
        return SesSendEmailResponse(
            message_id=message_id,
            request_id=str(request_id) if request_id else None,
        )

    def _send_raw_email_sync(self, request: SesSendRawEmailRequest) -> SesSendEmailResponse:
        client = self._build_client()
        payload: dict[str, object] = {
            "FromEmailAddress": request.source,
            "Destination": {"ToAddresses": request.to_addresses},
            "Content": {
                "Raw": {
                    "Data": request.raw_data,
                }
            },
        }
        if request.configuration_set_name is not None:
            payload["ConfigurationSetName"] = request.configuration_set_name
        if request.tags:
            payload["EmailTags"] = [
                {"Name": key, "Value": value}
                for key, value in request.tags
            ]

        try:
            response = client.send_email(**payload)
        except Exception as exc:  # pragma: no cover - exercised by contract tests
            raise self._map_exception(exc) from exc

        message_id = str(response.get("MessageId") or "").strip()
        if not message_id:
            raise SesTerminalError("SES response did not include MessageId")

        response_metadata = response.get("ResponseMetadata") or {}
        request_id = response_metadata.get("RequestId")
        return SesSendEmailResponse(
            message_id=message_id,
            request_id=str(request_id) if request_id else None,
        )

    def _get_suppressed_destination_sync(self, email: str) -> SesSuppressedDestination | None:
        client = self._build_client()
        try:
            response = client.get_suppressed_destination(EmailAddress=email)
        except Exception as exc:  # pragma: no cover - exercised by contract tests
            details = self._extract_error(exc)
            if details is not None and details[0] == "NotFoundException":
                return None
            raise self._map_exception(exc) from exc

        destination = response.get("SuppressedDestination")
        if not isinstance(destination, dict):
            return None

        destination_email = str(destination.get("EmailAddress") or "").strip().lower()
        if not destination_email:
            return None
        reason = str(destination.get("Reason") or "unknown")
        return SesSuppressedDestination(email=destination_email, reason=reason)

    def _build_client(self) -> Any:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover - runtime guard
            raise SesConfigurationError(
                "boto3 is required for the default SES transport"
            ) from exc

        kwargs: dict[str, object] = {
            "region_name": self._settings.ses_region,
        }

        if self._settings.aws_access_key_id and self._settings.aws_secret_access_key:
            kwargs["aws_access_key_id"] = self._settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = self._settings.aws_secret_access_key
            if self._settings.aws_session_token:
                kwargs["aws_session_token"] = self._settings.aws_session_token

        if self._settings.app_env in {"local", "test"}:
            kwargs["endpoint_url"] = self._settings.localstack_endpoint_url

        return boto3.client("sesv2", **kwargs)

    @staticmethod
    def _extract_error(exc: Exception) -> tuple[str, str] | None:
        response = getattr(exc, "response", None)
        if not isinstance(response, dict):
            return None
        error_payload = response.get("Error")
        if not isinstance(error_payload, dict):
            return None
        code = str(error_payload.get("Code") or "").strip()
        message = str(error_payload.get("Message") or "SES request failed").strip()
        if not code:
            return None
        return code, message

    def _map_exception(self, exc: Exception) -> SesError:
        details = self._extract_error(exc)
        if details is not None:
            return map_ses_error(code=details[0], message=details[1])
        return SesTerminalError(str(exc) or "SES request failed")


class SesClient:
    def __init__(
        self,
        *,
        transport: SesTransport,
        metrics: SesMetricsRecorder | None = None,
    ) -> None:
        self._transport = transport
        self._metrics = metrics or NoopSesMetricsRecorder()

    async def send_email(self, request: SesSendEmailRequest) -> SesSendEmailResponse:
        started = time.perf_counter()
        try:
            response = await run_with_retry(lambda: self._transport.send_email(request))
        except SesError as exc:
            self._metrics.record(
                operation="send_email",
                latency_ms=(time.perf_counter() - started) * 1000,
                success=False,
                error_class=exc.__class__.__name__,
            )
            raise

        self._metrics.record(
            operation="send_email",
            latency_ms=(time.perf_counter() - started) * 1000,
            success=True,
        )
        return response

    async def send_raw_email(self, request: SesSendRawEmailRequest) -> SesSendEmailResponse:
        started = time.perf_counter()
        try:
            response = await run_with_retry(lambda: self._transport.send_raw_email(request))
        except SesError as exc:
            self._metrics.record(
                operation="send_raw_email",
                latency_ms=(time.perf_counter() - started) * 1000,
                success=False,
                error_class=exc.__class__.__name__,
            )
            raise

        self._metrics.record(
            operation="send_raw_email",
            latency_ms=(time.perf_counter() - started) * 1000,
            success=True,
        )
        return response

    async def get_suppressed_destination(self, *, email: str) -> SesSuppressedDestination | None:
        started = time.perf_counter()
        try:
            response = await run_with_retry(
                lambda: self._transport.get_suppressed_destination(email=email)
            )
        except SesError as exc:
            self._metrics.record(
                operation="get_suppressed_destination",
                latency_ms=(time.perf_counter() - started) * 1000,
                success=False,
                error_class=exc.__class__.__name__,
            )
            raise

        self._metrics.record(
            operation="get_suppressed_destination",
            latency_ms=(time.perf_counter() - started) * 1000,
            success=True,
        )
        return response


@lru_cache(maxsize=1)
def get_ses_client() -> SesClient:
    settings = get_settings()
    return SesClient(transport=Boto3SesTransport(settings))


def reset_ses_client_cache() -> None:
    get_ses_client.cache_clear()
