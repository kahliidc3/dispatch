from __future__ import annotations

import pytest

from libs.ses_client.client import SesClient, SesSendEmailRequest
from libs.ses_client.errors import SesMessageRejectedError
from libs.ses_client.metrics import InMemorySesMetricsRecorder
from tests.fixtures.ses_fake import FakeSesTransport, build_fake_ses_client


@pytest.mark.asyncio
async def test_send_email_retries_transient_then_succeeds() -> None:
    transport = FakeSesTransport(transient_failures_remaining=2)
    metrics = InMemorySesMetricsRecorder()
    client = SesClient(transport=transport, metrics=metrics)

    result = await client.send_email(
        SesSendEmailRequest(
            from_email="from@dispatch.test",
            to_email="to@dispatch.test",
            subject="Hello",
            body_text="Body",
        )
    )

    assert result.message_id == "fake-ses-1"
    assert len(transport.send_calls) == 1
    assert len(metrics.events) == 1
    assert metrics.events[0].success is True


@pytest.mark.asyncio
async def test_send_email_does_not_retry_message_rejected() -> None:
    transport = FakeSesTransport(rejected_emails={"blocked@dispatch.test"})
    client = build_fake_ses_client(transport)

    with pytest.raises(SesMessageRejectedError):
        await client.send_email(
            SesSendEmailRequest(
                from_email="from@dispatch.test",
                to_email="blocked@dispatch.test",
                subject="Nope",
                body_text="Body",
            )
        )

    assert len(transport.send_calls) == 0


@pytest.mark.asyncio
async def test_get_suppressed_destination_returns_entry() -> None:
    transport = FakeSesTransport(suppressed={"supp@dispatch.test": "COMPLAINT"})
    client = build_fake_ses_client(transport)

    suppressed = await client.get_suppressed_destination(email="supp@dispatch.test")
    assert suppressed is not None
    assert suppressed.email == "supp@dispatch.test"
    assert suppressed.reason == "COMPLAINT"
