from __future__ import annotations

import json

import pytest

from apps.webhook import handlers
from apps.webhook.schemas import SnsEnvelope
from apps.webhook.sns_verify import SnsVerificationError, SnsVerificationResult
from libs.core.errors import ValidationError


def _sns_envelope(
    *,
    sns_type: str = "Notification",
    message: str | None = None,
    subscribe_url: str | None = None,
) -> SnsEnvelope:
    return SnsEnvelope.model_validate(
        {
            "Type": sns_type,
            "MessageId": "sns-msg-1",
            "TopicArn": "arn:aws:sns:us-east-1:123456789012:dispatch-events",
            "Message": message if message is not None else json.dumps({"eventType": "Delivery"}),
            "Timestamp": "2026-04-24T10:00:00Z",
            "SignatureVersion": "2",
            "Signature": "ZmFrZS1zaWduYXR1cmU=",
            "SigningCertURL": (
                "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-test.pem"
            ),
            "SubscribeURL": subscribe_url,
        }
    )


def test_handle_notification_enqueues_event(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object], str | None]] = []

    monkeypatch.setattr(
        handlers,
        "verify_sns_signature",
        lambda *_args, **_kwargs: SnsVerificationResult(verified=True),
    )

    def _fake_send_task(name: str, kwargs: dict[str, object], queue: str | None = None) -> None:
        calls.append((name, kwargs, queue))

    monkeypatch.setattr(handlers.celery_app, "send_task", _fake_send_task)

    envelope = _sns_envelope(
        message=json.dumps({"eventType": "Delivery", "mail": {"messageId": "ses-1"}}),
    )
    result = handlers.handle_sns_envelope(envelope=envelope)

    assert result.status == "enqueued"
    assert calls == [
        (
            "events.process_event",
            {"payload": {"eventType": "Delivery", "mail": {"messageId": "ses-1"}}},
            "events.ses.incoming",
        )
    ]


def test_handle_subscription_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        handlers,
        "verify_sns_signature",
        lambda *_args, **_kwargs: SnsVerificationResult(verified=True),
    )
    monkeypatch.setattr(handlers, "confirm_sns_subscription", lambda **_kwargs: True)

    result = handlers.handle_sns_envelope(
        envelope=_sns_envelope(
            sns_type="SubscriptionConfirmation",
            subscribe_url="https://sns.us-east-1.amazonaws.com/?Action=ConfirmSubscription",
        )
    )
    assert result.status == "subscription_confirmed"
    assert result.subscription_confirmed is True


def test_handle_notification_rejects_invalid_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        handlers,
        "verify_sns_signature",
        lambda *_args, **_kwargs: SnsVerificationResult(verified=True),
    )
    envelope = _sns_envelope(message="not-json")

    with pytest.raises(ValidationError, match="valid JSON"):
        handlers.handle_sns_envelope(envelope=envelope)


def test_handle_rejects_invalid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        handlers,
        "verify_sns_signature",
        lambda *_args, **_kwargs: SnsVerificationResult(verified=False),
    )

    with pytest.raises(SnsVerificationError):
        handlers.handle_sns_envelope(envelope=_sns_envelope())
