from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from libs.core.auth.schemas import CurrentActor
from libs.core.campaigns.models import Campaign
from libs.core.campaigns.repository import CampaignRepository
from libs.core.campaigns.service import CampaignService
from libs.core.contacts.schemas import ContactCreateRequest
from libs.core.db.uow import UnitOfWork
from libs.core.domains.schemas import DnsRecordType
from libs.core.segments.schemas import SegmentCreateRequest
from libs.core.sender_profiles.schemas import SenderProfileCreateRequest
from libs.core.templates.schemas import TemplateCreateRequest
from tests.fixtures.ses_fake import FakeSesTransport, build_fake_ses_client

AuthTestContext = Any
UserFactory = Any


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email=f"worker-send-{uuid4().hex[:8]}@dispatch.test",
        password="worker-send-password",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


async def _prepare_campaign(
    *,
    auth_test_context: AuthTestContext,
    actor: CurrentActor,
) -> tuple[str, CampaignService, FakeSesTransport]:
    domain_name = f"worker-send-{uuid4().hex[:8]}.dispatch.test"
    domain_detail = await auth_test_context.domain_service.create_domain(
        actor=actor,
        name=domain_name,
        dns_provider="manual",
        parent_domain="dispatch.test",
        ses_region="us-east-1",
        default_configuration_set_name=None,
        event_destination_sns_topic_arn=None,
        ip_address=None,
        user_agent=None,
    )
    for record in domain_detail.dns_records:
        auth_test_context.dns_adapter.set_record(
            record_type=DnsRecordType(record.record_type),
            name=record.name,
            values=[record.value],
        )
    await auth_test_context.domain_service.verify_domain(
        actor=actor,
        domain_id=domain_detail.domain.id,
        ip_address=None,
        user_agent=None,
    )

    sender_profile = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="Worker Sender",
            from_name="Worker",
            from_email=f"sender@{domain_name}",
            reply_to=None,
            domain_id=domain_detail.domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=1000,
        ),
        ip_address=None,
        user_agent=None,
    )

    template = await auth_test_context.template_service.create_template(
        actor=actor,
        payload=TemplateCreateRequest(
            name="Worker Template",
            description=None,
            category="outreach",
            subject="Hello {{contact.first_name}}",
            body_text="Body {{contact.email}}",
            body_html="<p>Body {{contact.first_name}}</p>",
            spintax_enabled=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    contact = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="worker-send-contact@dispatch.test",
            first_name="Worker",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )

    segment = await auth_test_context.segment_service.create_segment(
        actor=actor,
        payload=SegmentCreateRequest(
            name="Worker Segment",
            description=None,
            dsl_json={
                "op": "eq",
                "field": "contact.email",
                "value": contact.email,
            },
        ),
        ip_address=None,
        user_agent=None,
    )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        campaign = Campaign(
            name="Worker Campaign",
            campaign_type="outreach",
            sender_profile_id=sender_profile.id,
            template_version_id=template.versions[0].id,
            segment_id=segment.segment.id,
            list_id=None,
            schedule_type="immediate",
            timezone="UTC",
            send_rate_per_hour=100,
            status="draft",
            tracking_opens=False,
            tracking_clicks=False,
            created_by=actor.user.id,
        )
        uow.require_session().add(campaign)
        await uow.require_session().flush()

    fake_transport = FakeSesTransport()
    service = CampaignService(
        auth_test_context.settings,
        ses_client=build_fake_ses_client(fake_transport),
        segment_service=auth_test_context.segment_service,
    )

    return campaign.id, service, fake_transport


def test_send_task_sends_message_once(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: Any,
) -> None:
    from apps.workers import celery_app as celery_module
    from apps.workers import send_tasks

    actor = asyncio.run(_create_admin_actor(auth_user_factory))
    campaign_id, service, fake_transport = asyncio.run(
        _prepare_campaign(auth_test_context=auth_test_context, actor=actor)
    )

    monkeypatch.setattr(celery_module.celery_app, "send_task", lambda *args, **kwargs: None)
    launch = asyncio.run(
        service.launch_campaign(
            actor=actor,
            campaign_id=campaign_id,
            ip_address=None,
            user_agent=None,
        )
    )

    async def _get_message_id() -> str:
        async with auth_test_context.session_factory() as session:
            repo = CampaignRepository(session)
            ids = await repo.list_queued_message_ids_for_run(launch.campaign_run.id)
            return ids[0]

    message_id = asyncio.run(_get_message_id())

    monkeypatch.setattr(send_tasks, "get_campaign_service", lambda: service)
    result = send_tasks.send_message(message_id)

    assert result["status"] == "sent"
    assert result["message_id"] == message_id
    assert len(fake_transport.send_calls) == 1
