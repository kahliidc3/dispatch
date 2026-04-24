from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from libs.core.auth.schemas import CurrentActor
from libs.core.campaigns.models import Campaign
from libs.core.campaigns.repository import CampaignRepository
from libs.core.campaigns.service import CampaignService
from libs.core.contacts.schemas import ContactCreateRequest
from libs.core.db.uow import UnitOfWork
from libs.core.domains.schemas import DnsRecordType
from libs.core.segments.schemas import SegmentCreateRequest
from libs.core.sender_profiles.schemas import SenderProfileCreateRequest
from libs.core.suppression.models import SuppressionEntry
from libs.core.templates.schemas import TemplateCreateRequest
from tests.fixtures.ses_fake import FakeSesTransport, build_fake_ses_client

AuthTestContext = Any
UserFactory = Any


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email=f"campaign-admin-{uuid4().hex[:8]}@dispatch.test",
        password="campaign-password-value",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


async def _create_campaign_fixture(
    *,
    auth_test_context: AuthTestContext,
    actor: CurrentActor,
    contact_count: int,
) -> str:
    domain_name = f"campaign-{uuid4().hex[:8]}.dispatch.test"
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
            display_name="Campaign Sender",
            from_name="Dispatch",
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
            name="Campaign Template",
            description=None,
            category="outreach",
            subject="Hello {{contact.first_name}}",
            body_text="Body for {{contact.email}}",
            body_html="<p>Hello {{contact.first_name}}</p>",
            spintax_enabled=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    for idx in range(contact_count):
        await auth_test_context.contact_service.create_contact(
            actor=actor,
            payload=ContactCreateRequest(
                email=f"launch-flow-{idx}@dispatch.test",
                first_name=f"User{idx}",
                source_type="manual",
            ),
            ip_address=None,
            user_agent=None,
        )

    segment = await auth_test_context.segment_service.create_segment(
        actor=actor,
        payload=SegmentCreateRequest(
            name="Campaign Segment",
            description=None,
            dsl_json={"op": "contains", "field": "contact.email", "value": "launch-flow-"},
        ),
        ip_address=None,
        user_agent=None,
    )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        campaign = Campaign(
            name="Launch Campaign",
            campaign_type="outreach",
            sender_profile_id=sender_profile.id,
            template_version_id=template.versions[0].id,
            segment_id=segment.segment.id,
            list_id=None,
            schedule_type="immediate",
            timezone="UTC",
            send_rate_per_hour=500,
            status="draft",
            tracking_opens=False,
            tracking_clicks=False,
            created_by=actor.user.id,
        )
        uow.require_session().add(campaign)
        await uow.require_session().flush()
        return campaign.id


@pytest.mark.asyncio
async def test_launch_campaign_creates_messages_and_enqueues(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    campaign_id = await _create_campaign_fixture(
        auth_test_context=auth_test_context,
        actor=actor,
        contact_count=3,
    )

    fake_transport = FakeSesTransport()
    service = CampaignService(
        auth_test_context.settings,
        ses_client=build_fake_ses_client(fake_transport),
        segment_service=auth_test_context.segment_service,
    )

    queued: list[str] = []

    def _fake_send_task(task_name: str, kwargs: dict[str, str]) -> None:
        assert task_name == "send.send_message"
        queued.append(kwargs["message_id"])

    from apps.workers import celery_app as celery_module

    monkeypatch.setattr(celery_module.celery_app, "send_task", _fake_send_task)

    launch = await service.launch_campaign(
        actor=actor,
        campaign_id=campaign_id,
        ip_address=None,
        user_agent=None,
    )

    assert launch.snapshot_rows == 3
    assert launch.created_messages == 3
    assert launch.enqueued_messages == 3
    assert launch.campaign.status == "running"
    assert len(queued) == 3


@pytest.mark.asyncio
async def test_send_queued_message_is_idempotent(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    campaign_id = await _create_campaign_fixture(
        auth_test_context=auth_test_context,
        actor=actor,
        contact_count=1,
    )

    fake_transport = FakeSesTransport()
    service = CampaignService(
        auth_test_context.settings,
        ses_client=build_fake_ses_client(fake_transport),
        segment_service=auth_test_context.segment_service,
    )

    from apps.workers import celery_app as celery_module

    monkeypatch.setattr(celery_module.celery_app, "send_task", lambda *args, **kwargs: None)

    launch = await service.launch_campaign(
        actor=actor,
        campaign_id=campaign_id,
        ip_address=None,
        user_agent=None,
    )

    async with auth_test_context.session_factory() as session:
        repo = CampaignRepository(session)
        message_ids = await repo.list_queued_message_ids_for_run(launch.campaign_run.id)
    message_id = message_ids[0]

    first = await service.send_queued_message(message_id=message_id)
    second = await service.send_queued_message(message_id=message_id)

    assert first.status == "sent"
    assert second.status == "sent"
    assert first.ses_message_id is not None
    assert second.ses_message_id == first.ses_message_id
    assert len(fake_transport.send_calls) == 1


@pytest.mark.asyncio
async def test_send_queued_message_blocks_local_suppression(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    campaign_id = await _create_campaign_fixture(
        auth_test_context=auth_test_context,
        actor=actor,
        contact_count=1,
    )

    fake_transport = FakeSesTransport()
    service = CampaignService(
        auth_test_context.settings,
        ses_client=build_fake_ses_client(fake_transport),
        segment_service=auth_test_context.segment_service,
    )

    from apps.workers import celery_app as celery_module

    monkeypatch.setattr(celery_module.celery_app, "send_task", lambda *args, **kwargs: None)

    launch = await service.launch_campaign(
        actor=actor,
        campaign_id=campaign_id,
        ip_address=None,
        user_agent=None,
    )

    async with auth_test_context.session_factory() as session:
        repo = CampaignRepository(session)
        message_ids = await repo.list_queued_message_ids_for_run(launch.campaign_run.id)
        message = await repo.get_message_by_id(message_ids[0])
        assert message is not None

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        uow.require_session().add(
            SuppressionEntry(email=message.to_email, reason="manual"),
        )
        await uow.require_session().flush()

    result = await service.send_queued_message(message_id=message.id)
    assert result.status == "failed"
    assert result.error_code == "suppressed_local"
    assert len(fake_transport.send_calls) == 0
