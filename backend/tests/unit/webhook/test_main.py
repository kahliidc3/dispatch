from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from apps.webhook.main import app
from apps.webhook.sns_verify import SnsVerificationError


@pytest.fixture
async def webhook_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def _sns_payload() -> dict[str, object]:
    return {
        "Type": "Notification",
        "MessageId": "sns-msg-1",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:dispatch-events",
        "Message": "{\"eventType\":\"Delivery\",\"mail\":{\"messageId\":\"ses-1\"}}",
        "Timestamp": "2026-04-24T10:00:00Z",
        "SignatureVersion": "2",
        "Signature": "ZmFrZS1zaWduYXR1cmU=",
        "SigningCertURL": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-test.pem",
    }


@pytest.mark.asyncio
async def test_receive_sns_success(
    webhook_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from apps.webhook import main as webhook_main

    class _FakeResult:
        status = "enqueued"
        subscription_confirmed = False

    monkeypatch.setattr(
        webhook_main,
        "handle_sns_envelope",
        lambda **_kwargs: _FakeResult(),
    )

    response = await webhook_client.post("/sns", json=_sns_payload())

    assert response.status_code == 200
    assert response.json() == {"status": "enqueued", "subscription_confirmed": False}


@pytest.mark.asyncio
async def test_receive_sns_rejects_invalid_signature(
    webhook_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from apps.webhook import main as webhook_main

    def _raise_signature_error(**_kwargs: object) -> None:
        raise SnsVerificationError("SNS signature verification failed")

    monkeypatch.setattr(webhook_main, "handle_sns_envelope", _raise_signature_error)

    response = await webhook_client.post("/sns", json=_sns_payload())

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_receive_sns_requires_json_body(webhook_client: AsyncClient) -> None:
    response = await webhook_client.post(
        "/sns",
        content="not-json",
        headers={"content-type": "text/plain"},
    )
    assert response.status_code == 400
