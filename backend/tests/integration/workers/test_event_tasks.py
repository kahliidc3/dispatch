from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select

from apps.workers import event_tasks
from libs.core.campaigns.models import Message
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain
from libs.core.events.models import BounceEvent, DeliveryEvent, RollingMetric
from libs.core.events.service import reset_event_service_cache
from libs.core.sender_profiles.models import SenderProfile
from libs.core.suppression.repository import SuppressionRepository
from libs.core.suppression.service import reset_suppression_service_cache

AuthTestContext = Any


def _reset_event_pipeline_caches() -> None:
    reset_suppression_service_cache()
    reset_event_service_cache()


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


async def _create_sent_message(
    auth_test_context: AuthTestContext,
    *,
    to_email: str,
) -> tuple[str, str]:
    unique = uuid4().hex[:8]
    ses_message_id = f"ses-{unique}"
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        domain = Domain(
            name=f"events-{unique}.dispatch.test",
            verification_status="verified",
            spf_status="verified",
            dkim_status="verified",
            dmarc_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()

        sender = SenderProfile(
            display_name="Events Sender",
            from_name="Dispatch",
            from_email=f"sender-{unique}@{domain.name}",
            domain_id=domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=1000,
        )
        uow.require_session().add(sender)
        await uow.require_session().flush()

        message = Message(
            campaign_id=None,
            send_batch_id=None,
            contact_id=None,
            sender_profile_id=sender.id,
            domain_id=domain.id,
            to_email=to_email,
            from_email=sender.from_email,
            subject="Event task test message",
            ses_message_id=ses_message_id,
            status="sent",
            sent_at=datetime.now(UTC),
        )
        uow.require_session().add(message)
        await uow.require_session().flush()
        return message.id, ses_message_id


def _delivery_payload(
    *,
    ses_message_id: str,
    to_email: str,
    occurred_at: datetime,
) -> dict[str, object]:
    return {
        "eventType": "Delivery",
        "mail": {
            "messageId": ses_message_id,
            "timestamp": _iso(occurred_at),
            "destination": [to_email],
        },
        "delivery": {
            "timestamp": _iso(occurred_at),
            "smtpResponse": "250 2.6.0 Message accepted",
            "processingTimeMillis": 1024,
        },
    }


def _bounce_payload(
    *,
    ses_message_id: str,
    to_email: str,
    occurred_at: datetime,
) -> dict[str, object]:
    return {
        "eventType": "Bounce",
        "mail": {
            "messageId": ses_message_id,
            "timestamp": _iso(occurred_at),
            "destination": [to_email],
        },
        "bounce": {
            "timestamp": _iso(occurred_at),
            "bounceType": "Permanent",
            "bounceSubType": "General",
            "bouncedRecipients": [
                {
                    "emailAddress": to_email,
                    "diagnosticCode": "smtp; 550 User unknown",
                }
            ],
        },
    }


def test_process_event_delivery_updates_message_and_metrics(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_event_pipeline_caches()
    to_email = f"delivery-{uuid4().hex[:8]}@dispatch.test"
    message_id, ses_message_id = asyncio.run(
        _create_sent_message(auth_test_context, to_email=to_email)
    )
    occurred_at = datetime.now(UTC)

    result = event_tasks.process_event(
        _delivery_payload(ses_message_id=ses_message_id, to_email=to_email, occurred_at=occurred_at)
    )

    assert result["event_type"] == "Delivery"
    assert result["message_found"] is True
    assert result["status_updated"] is True
    assert result["deduplicated"] is False
    assert result["metrics_updated"] is True

    async def _assertions() -> None:
        async with auth_test_context.session_factory() as session:
            message = await session.get(Message, message_id)
            assert message is not None
            assert message.status == "delivered"

            delivery_count = await session.scalar(select(func.count(DeliveryEvent.id)))
            assert delivery_count == 1

            metrics_count = await session.scalar(select(func.count(RollingMetric.id)))
            assert metrics_count is not None
            assert metrics_count > 0

    asyncio.run(_assertions())


def test_process_event_is_deduplicated(auth_test_context: AuthTestContext) -> None:
    _reset_event_pipeline_caches()
    to_email = f"dedup-{uuid4().hex[:8]}@dispatch.test"
    _, ses_message_id = asyncio.run(_create_sent_message(auth_test_context, to_email=to_email))
    occurred_at = datetime.now(UTC)
    payload = _delivery_payload(
        ses_message_id=ses_message_id,
        to_email=to_email,
        occurred_at=occurred_at,
    )

    first = event_tasks.process_event(payload)
    second = event_tasks.process_event(payload)

    assert first["deduplicated"] is False
    assert second["deduplicated"] is True

    async def _assertions() -> None:
        async with auth_test_context.session_factory() as session:
            delivery_count = await session.scalar(select(func.count(DeliveryEvent.id)))
            assert delivery_count == 1

    asyncio.run(_assertions())


def test_process_event_bounce_writes_suppression(auth_test_context: AuthTestContext) -> None:
    _reset_event_pipeline_caches()
    to_email = f"bounce-{uuid4().hex[:8]}@dispatch.test"
    message_id, ses_message_id = asyncio.run(
        _create_sent_message(auth_test_context, to_email=to_email)
    )
    occurred_at = datetime.now(UTC)

    result = event_tasks.process_event(
        _bounce_payload(ses_message_id=ses_message_id, to_email=to_email, occurred_at=occurred_at)
    )

    assert result["event_type"] == "Bounce"
    assert result["status_updated"] is True
    assert result["suppression_written"] is True

    async def _assertions() -> None:
        async with auth_test_context.session_factory() as session:
            message = await session.get(Message, message_id)
            assert message is not None
            assert message.status == "bounced"

            bounce_count = await session.scalar(select(func.count(BounceEvent.id)))
            assert bounce_count == 1

            suppression_repo = SuppressionRepository(session)
            suppression = await suppression_repo.get_by_email(to_email)
            assert suppression is not None
            assert suppression.reason == "hard_bounce"

    asyncio.run(_assertions())
