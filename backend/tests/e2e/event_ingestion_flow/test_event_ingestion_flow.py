from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select

from apps.workers import event_tasks
from libs.core.campaigns.models import Message
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain
from libs.core.events.models import (
    BounceEvent,
    ClickEvent,
    ComplaintEvent,
    DeliveryEvent,
    OpenEvent,
)
from libs.core.events.service import reset_event_service_cache
from libs.core.sender_profiles.models import SenderProfile
from libs.core.suppression.repository import SuppressionRepository
from libs.core.suppression.service import reset_suppression_service_cache

AuthTestContext = Any


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _make_terminal_payload(
    *,
    event_type: str,
    ses_message_id: str,
    to_email: str,
    occurred_at: datetime,
) -> dict[str, object]:
    base = {
        "eventType": event_type,
        "mail": {
            "messageId": ses_message_id,
            "timestamp": _iso(occurred_at),
            "destination": [to_email],
        },
    }
    if event_type == "Delivery":
        base["delivery"] = {
            "timestamp": _iso(occurred_at),
            "smtpResponse": "250 2.6.0 Message accepted",
            "processingTimeMillis": 256,
        }
    elif event_type == "Bounce":
        base["bounce"] = {
            "timestamp": _iso(occurred_at),
            "bounceType": "Permanent",
            "bounceSubType": "General",
            "bouncedRecipients": [
                {
                    "emailAddress": to_email,
                    "diagnosticCode": "smtp; 550 User unknown",
                }
            ],
        }
    elif event_type == "Complaint":
        base["complaint"] = {
            "timestamp": _iso(occurred_at),
            "complaintSubType": "abuse",
            "complainedRecipients": [{"emailAddress": to_email}],
            "userAgent": "Mozilla/5.0",
        }
    return base


def _make_open_payload(
    *,
    ses_message_id: str,
    to_email: str,
    occurred_at: datetime,
) -> dict[str, object]:
    return {
        "eventType": "Open",
        "mail": {
            "messageId": ses_message_id,
            "timestamp": _iso(occurred_at),
            "destination": [to_email],
        },
        "open": {
            "timestamp": _iso(occurred_at),
            "userAgent": "Mozilla/5.0",
            "ipAddress": "127.0.0.1",
        },
    }


def _make_click_payload(
    *,
    ses_message_id: str,
    to_email: str,
    occurred_at: datetime,
) -> dict[str, object]:
    return {
        "eventType": "Click",
        "mail": {
            "messageId": ses_message_id,
            "timestamp": _iso(occurred_at),
            "destination": [to_email],
        },
        "click": {
            "timestamp": _iso(occurred_at),
            "link": "https://dispatch.test/offers",
            "userAgent": "Mozilla/5.0",
            "ipAddress": "127.0.0.1",
        },
    }


def _make_delay_payload(
    *,
    ses_message_id: str,
    to_email: str,
    occurred_at: datetime,
) -> dict[str, object]:
    return {
        "eventType": "DeliveryDelay",
        "mail": {
            "messageId": ses_message_id,
            "timestamp": _iso(occurred_at),
            "destination": [to_email],
        },
        "deliveryDelay": {
            "timestamp": _iso(occurred_at),
            "reason": "MailboxBusy",
        },
    }


async def _seed_messages(auth_test_context: AuthTestContext) -> list[tuple[str, str]]:
    unique = uuid4().hex[:8]
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        domain = Domain(
            name=f"event-e2e-{unique}.dispatch.test",
            verification_status="verified",
            spf_status="verified",
            dkim_status="verified",
            dmarc_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()

        sender = SenderProfile(
            display_name="E2E Sender",
            from_name="Dispatch",
            from_email=f"sender-{unique}@{domain.name}",
            domain_id=domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=20000,
        )
        uow.require_session().add(sender)
        await uow.require_session().flush()

        seeded: list[tuple[str, str]] = []
        for index in range(250):
            ses_message_id = f"e2e-ses-{unique}-{index}"
            to_email = f"recipient-{index}@dispatch.test"
            message = Message(
                campaign_id=None,
                send_batch_id=None,
                contact_id=None,
                sender_profile_id=sender.id,
                domain_id=domain.id,
                to_email=to_email,
                from_email=sender.from_email,
                subject="E2E event ingestion",
                ses_message_id=ses_message_id,
                status="sent",
                sent_at=datetime.now(UTC),
            )
            uow.require_session().add(message)
            seeded.append((ses_message_id, to_email))

        await uow.require_session().flush()
        return seeded


def test_event_ingestion_flow_processes_1000_mixed_events(
    auth_test_context: AuthTestContext,
) -> None:
    reset_suppression_service_cache()
    reset_event_service_cache()
    seeded = asyncio.run(_seed_messages(auth_test_context))
    base_time = datetime.now(UTC)
    payloads: list[dict[str, object]] = []

    for idx, (ses_message_id, to_email) in enumerate(seeded):
        occurred_at = base_time + timedelta(seconds=idx * 10)
        if idx < 100:
            terminal_type = "Delivery"
        elif idx < 175:
            terminal_type = "Bounce"
        else:
            terminal_type = "Complaint"

        payloads.append(
            _make_terminal_payload(
                event_type=terminal_type,
                ses_message_id=ses_message_id,
                to_email=to_email,
                occurred_at=occurred_at,
            )
        )
        payloads.append(
            _make_open_payload(
                ses_message_id=ses_message_id,
                to_email=to_email,
                occurred_at=occurred_at + timedelta(seconds=1),
            )
        )
        payloads.append(
            _make_click_payload(
                ses_message_id=ses_message_id,
                to_email=to_email,
                occurred_at=occurred_at + timedelta(seconds=2),
            )
        )
        payloads.append(
            _make_delay_payload(
                ses_message_id=ses_message_id,
                to_email=to_email,
                occurred_at=occurred_at + timedelta(seconds=3),
            )
        )

    assert len(payloads) == 1000

    for payload in payloads:
        event_tasks.process_event(payload)

    dedup_hits = 0
    for payload in payloads[:25]:
        result = event_tasks.process_event(payload)
        if result["deduplicated"] is True:
            dedup_hits += 1
    assert dedup_hits == 25

    async def _assertions() -> None:
        async with auth_test_context.session_factory() as session:
            delivered_count = await session.scalar(
                select(func.count(Message.id)).where(Message.status == "delivered")
            )
            bounced_count = await session.scalar(
                select(func.count(Message.id)).where(Message.status == "bounced")
            )
            complained_count = await session.scalar(
                select(func.count(Message.id)).where(Message.status == "complained")
            )
            assert delivered_count == 100
            assert bounced_count == 75
            assert complained_count == 75

            delivery_events = await session.scalar(select(func.count(DeliveryEvent.id)))
            bounce_events = await session.scalar(select(func.count(BounceEvent.id)))
            complaint_events = await session.scalar(select(func.count(ComplaintEvent.id)))
            open_events = await session.scalar(select(func.count(OpenEvent.id)))
            click_events = await session.scalar(select(func.count(ClickEvent.id)))
            assert delivery_events == 100
            assert bounce_events == 325
            assert complaint_events == 75
            assert open_events == 250
            assert click_events == 250

            suppression_repo = SuppressionRepository(session)
            suppressed = 0
            for idx in range(250):
                email = f"recipient-{idx}@dispatch.test"
                entry = await suppression_repo.get_by_email(email)
                if entry is not None:
                    suppressed += 1
            assert suppressed == 150

    asyncio.run(_assertions())
