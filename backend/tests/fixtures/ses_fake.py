from __future__ import annotations

from dataclasses import dataclass, field

from libs.ses_client.client import (
    SesClient,
    SesSendEmailRequest,
    SesSendEmailResponse,
    SesSendRawEmailRequest,
    SesSuppressedDestination,
)
from libs.ses_client.errors import SesMessageRejectedError, SesTransientError


@dataclass(slots=True)
class FakeSesTransport:
    suppressed: dict[str, str] = field(default_factory=dict)
    send_calls: list[SesSendEmailRequest] = field(default_factory=list)
    raw_send_calls: list[SesSendRawEmailRequest] = field(default_factory=list)
    transient_failures_remaining: int = 0
    rejected_emails: set[str] = field(default_factory=set)

    async def send_email(self, request: SesSendEmailRequest) -> SesSendEmailResponse:
        to_email = request.to_email.strip().lower()
        if self.transient_failures_remaining > 0:
            self.transient_failures_remaining -= 1
            raise SesTransientError("temporary SES outage")
        if to_email in {item.strip().lower() for item in self.rejected_emails}:
            raise SesMessageRejectedError("message rejected")

        self.send_calls.append(request)
        return SesSendEmailResponse(message_id=f"fake-ses-{len(self.send_calls)}")

    async def send_raw_email(self, request: SesSendRawEmailRequest) -> SesSendEmailResponse:
        if self.transient_failures_remaining > 0:
            self.transient_failures_remaining -= 1
            raise SesTransientError("temporary SES outage")
        self.raw_send_calls.append(request)
        return SesSendEmailResponse(message_id=f"fake-ses-raw-{len(self.raw_send_calls)}")

    async def get_suppressed_destination(self, *, email: str) -> SesSuppressedDestination | None:
        normalized = email.strip().lower()
        reason = self.suppressed.get(normalized)
        if reason is None:
            return None
        return SesSuppressedDestination(email=normalized, reason=reason)


def build_fake_ses_client(transport: FakeSesTransport | None = None) -> SesClient:
    return SesClient(transport=transport or FakeSesTransport())
