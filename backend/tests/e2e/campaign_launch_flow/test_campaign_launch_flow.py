from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from apps.api.deps import (
    get_auth_service_dep,
    get_campaign_service_dep,
    get_settings_dep,
    get_user_service_dep,
)
from apps.api.main import app
from libs.core.auth.schemas import CurrentActor
from libs.core.campaigns.models import Campaign, Message
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


@pytest.fixture
async def auth_client(auth_test_context: AuthTestContext) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_settings_dep] = lambda: auth_test_context.settings
    app.dependency_overrides[get_auth_service_dep] = lambda: auth_test_context.auth_service
    app.dependency_overrides[get_user_service_dep] = lambda: auth_test_context.user_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_campaign_launch_flow_sends_without_duplicates(
    auth_client: AsyncClient,
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin = await auth_user_factory(
        email="e2e-campaign-admin@dispatch.test",
        password="correct-password-value",
        role="admin",
    )
    actor = CurrentActor(actor_type="user", user=admin)

    fake_transport = FakeSesTransport()
    campaign_service = CampaignService(
        auth_test_context.settings,
        ses_client=build_fake_ses_client(fake_transport),
        segment_service=auth_test_context.segment_service,
    )
    app.dependency_overrides[get_campaign_service_dep] = lambda: campaign_service

    login_response = await auth_client.post(
        "/auth/login",
        json={
            "email": "e2e-campaign-admin@dispatch.test",
            "password": "correct-password-value",
        },
    )
    assert login_response.status_code == 200

    domain_name = f"e2e-launch-{uuid4().hex[:8]}.dispatch.test"
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
            display_name="E2E Sender",
            from_name="E2E",
            from_email=f"sender@{domain_name}",
            reply_to=None,
            domain_id=domain_detail.domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=2000,
        ),
        ip_address=None,
        user_agent=None,
    )

    template = await auth_test_context.template_service.create_template(
        actor=actor,
        payload=TemplateCreateRequest(
            name="E2E Template",
            description=None,
            category="outreach",
            subject="Hello {{contact.first_name}}",
            body_text="Body for {{contact.email}}",
            body_html="<p>Body for {{contact.first_name}}</p>",
            spintax_enabled=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    total_contacts = 1000
    for idx in range(total_contacts):
        await auth_test_context.contact_service.create_contact(
            actor=actor,
            payload=ContactCreateRequest(
                email=f"e2e-launch-{idx}@dispatch.test",
                first_name=f"Contact{idx}",
                source_type="manual",
            ),
            ip_address=None,
            user_agent=None,
        )

    segment = await auth_test_context.segment_service.create_segment(
        actor=actor,
        payload=SegmentCreateRequest(
            name="E2E Segment",
            description=None,
            dsl_json={"op": "contains", "field": "contact.email", "value": "e2e-launch-"},
        ),
        ip_address=None,
        user_agent=None,
    )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        campaign = Campaign(
            name="E2E Campaign",
            campaign_type="outreach",
            sender_profile_id=sender_profile.id,
            template_version_id=template.versions[0].id,
            segment_id=segment.segment.id,
            list_id=None,
            schedule_type="immediate",
            timezone="UTC",
            send_rate_per_hour=2000,
            status="draft",
            tracking_opens=False,
            tracking_clicks=False,
            created_by=admin.id,
        )
        uow.require_session().add(campaign)
        await uow.require_session().flush()
        campaign_id = campaign.id

    queued_ids: list[str] = []

    def _capture_send_task(task_name: str, kwargs: dict[str, str]) -> None:
        assert task_name == "send.send_message"
        queued_ids.append(kwargs["message_id"])

    from apps.workers import celery_app as celery_module

    monkeypatch.setattr(celery_module.celery_app, "send_task", _capture_send_task)

    launch_response = await auth_client.post(f"/campaigns/{campaign_id}/launch")
    assert launch_response.status_code == 200
    payload = launch_response.json()
    assert payload["created_messages"] == total_contacts
    assert payload["enqueued_messages"] == total_contacts

    for message_id in queued_ids:
        result = await campaign_service.send_queued_message(message_id=message_id)
        assert result.status == "sent"

    async with auth_test_context.session_factory() as session:
        sent_count_stmt = (
            select(func.count())
            .select_from(Message)
            .where(Message.campaign_id == campaign_id)
            .where(Message.status == "sent")
        )
        sent_count = int((await session.execute(sent_count_stmt)).scalar_one())

        ids_stmt = (
            select(Message.ses_message_id)
            .where(Message.campaign_id == campaign_id)
            .where(Message.ses_message_id.is_not(None))
        )
        ses_ids = [str(row[0]) for row in (await session.execute(ids_stmt)).all()]

    assert sent_count == total_contacts
    assert len(ses_ids) == total_contacts
    assert len(set(ses_ids)) == total_contacts
    assert len(fake_transport.send_calls) == total_contacts
