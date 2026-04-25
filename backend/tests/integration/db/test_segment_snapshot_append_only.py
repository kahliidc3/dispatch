from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError

from libs.core.auth.schemas import CurrentActor
from libs.core.campaigns.models import Campaign, CampaignRun
from libs.core.contacts.schemas import ContactCreateRequest
from libs.core.db.uow import UnitOfWork
from libs.core.domains.schemas import DnsRecordType
from libs.core.segments.models import SegmentSnapshot
from libs.core.segments.schemas import SegmentCreateRequest
from libs.core.sender_profiles.schemas import SenderProfileCreateRequest
from libs.core.templates.schemas import TemplateCreateRequest

AuthTestContext = Any
UserFactory = Any


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email="admin-segment-append-only@dispatch.test",
        password="segment-append-only-password",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


async def _create_campaign_run(
    *,
    auth_test_context: AuthTestContext,
    actor: CurrentActor,
) -> str:
    domain_name = f"append-only-{uuid4().hex[:8]}.dispatch.test"
    detail = await auth_test_context.domain_service.create_domain(
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
    for record in detail.dns_records:
        auth_test_context.dns_adapter.set_record(
            record_type=DnsRecordType(record.record_type),
            name=record.name,
            values=[record.value],
        )
    await auth_test_context.domain_service.verify_domain(
        actor=actor,
        domain_id=detail.domain.id,
        ip_address=None,
        user_agent=None,
    )

    sender_profile = await auth_test_context.sender_profile_service.create_sender_profile(
        actor=actor,
        payload=SenderProfileCreateRequest(
            display_name="Append Sender",
            from_name="Append",
            from_email=f"sender@{domain_name}",
            reply_to=None,
            domain_id=detail.domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=500,
        ),
        ip_address=None,
        user_agent=None,
    )
    template = await auth_test_context.template_service.create_template(
        actor=actor,
        payload=TemplateCreateRequest(
            name="Append Template",
            description=None,
            category="append-only",
            subject="Hello {{contact.first_name}}",
            body_text="Body {{contact.first_name}}",
            body_html=None,
            spintax_enabled=False,
        ),
        ip_address=None,
        user_agent=None,
    )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        campaign = Campaign(
            name="Append Campaign",
            campaign_type="outreach",
            sender_profile_id=sender_profile.id,
            template_version_id=template.versions[0].id,
            segment_id=None,
            list_id=None,
            schedule_type="immediate",
            scheduled_at=None,
            timezone="UTC",
            send_rate_per_hour=100,
            status="draft",
            tracking_opens=False,
            tracking_clicks=False,
            created_by=actor.user.id,
        )
        uow.require_session().add(campaign)
        await uow.require_session().flush()

        run = CampaignRun(campaign_id=campaign.id, run_number=1, status="running")
        uow.require_session().add(run)
        await uow.require_session().flush()
        return run.id


@pytest.mark.asyncio
async def test_segment_snapshot_rows_are_append_only_at_db_level(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    campaign_run_id = await _create_campaign_run(auth_test_context=auth_test_context, actor=actor)

    await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="segment-append-only@dispatch.test",
            first_name="Append",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )
    segment = await auth_test_context.segment_service.create_segment(
        actor=actor,
        payload=SegmentCreateRequest(
            name="Append Segment",
            description=None,
            dsl_json={"op": "contains", "field": "contact.email", "value": "segment-append"},
        ),
        ip_address=None,
        user_agent=None,
    )
    await auth_test_context.segment_service.freeze_segment(
        segment_id=segment.segment.id,
        campaign_run_id=campaign_run_id,
        chunk_size=100,
    )

    async with auth_test_context.session_factory() as session:
        snapshot = (
            await session.execute(
                select(SegmentSnapshot).where(SegmentSnapshot.campaign_run_id == campaign_run_id)
            )
        ).scalar_one()
        snapshot_id = snapshot.id

    with pytest.raises(DBAPIError):
        async with UnitOfWork(auth_test_context.session_factory) as uow:
            await uow.require_session().execute(
                update(SegmentSnapshot)
                .where(SegmentSnapshot.id == snapshot_id)
                .values(exclusion_reason="mutated")
            )

    with pytest.raises(DBAPIError):
        async with UnitOfWork(auth_test_context.session_factory) as uow:
            await uow.require_session().execute(
                delete(SegmentSnapshot).where(SegmentSnapshot.id == snapshot_id)
            )
