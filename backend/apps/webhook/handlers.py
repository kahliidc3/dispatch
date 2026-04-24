from __future__ import annotations

from dataclasses import dataclass

from apps.webhook.schemas import SnsEnvelope
from apps.webhook.sns_verify import (
    SnsVerificationError,
    confirm_sns_subscription,
    verify_sns_signature,
)
from apps.workers.celery_app import celery_app
from libs.core.config import Settings, get_settings
from libs.core.errors import ValidationError
from libs.core.logging import get_logger

logger = get_logger("webhook.handlers")


@dataclass(slots=True)
class SnsHandleResult:
    status: str
    subscription_confirmed: bool = False


def handle_sns_envelope(
    *,
    envelope: SnsEnvelope,
    settings: Settings | None = None,
) -> SnsHandleResult:
    verification = verify_sns_signature(envelope.to_sns_dict(), settings=settings)
    if not verification.verified:
        raise SnsVerificationError("SNS signature verification failed")

    if envelope.is_subscription_confirmation:
        if envelope.subscribe_url is None:
            raise ValidationError("SubscriptionConfirmation missing SubscribeURL")
        confirmed = confirm_sns_subscription(subscribe_url=envelope.subscribe_url)
        logger.info(
            "webhook.subscription_confirmation",
            message_id=envelope.message_id,
            confirmed=confirmed,
        )
        return SnsHandleResult(status="subscription_confirmed", subscription_confirmed=confirmed)

    if envelope.type == "UnsubscribeConfirmation":
        logger.info("webhook.unsubscribe_confirmation", message_id=envelope.message_id)
        return SnsHandleResult(status="unsubscribe_confirmation")

    if envelope.is_notification:
        try:
            message_payload = envelope.parse_message_json()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        celery_app.send_task(
            "events.process_event",
            kwargs={"payload": message_payload},
            queue="events.ses.incoming",
        )
        return SnsHandleResult(status="enqueued")

    logger.warning("webhook.unsupported_sns_type", sns_type=envelope.type)
    return SnsHandleResult(status="ignored")


def get_webhook_settings() -> Settings:
    return get_settings()
