from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from libs.core.auth.schemas import CurrentActor
from libs.core.campaigns.models import Campaign, CampaignRun
from libs.core.contacts.schemas import ContactCreateRequest, ContactUpdateRequest
from libs.core.db.uow import UnitOfWork
from libs.core.domains.schemas import DnsRecordType
from libs.core.segments.models import SegmentSnapshot
from libs.core.segments.schemas import SegmentCreateRequest
from libs.core.sender_profiles.schemas import SenderProfileCreateRequest
from libs.core.suppression.models import SuppressionEntry
from libs.core.templates.schemas import TemplateCreateRequest

AuthTestContext = Any
UserFactory = Any


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email="admin-segment-freeze@dispatch.test",
        password="segment-freeze-password",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


async def _create_campaign_run(
    *,
    auth_test_context: AuthTestContext,
    actor: CurrentActor,
) -> str:
    domain_name = f"freeze-{uuid4().hex[:8]}.dispatch.test"
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
            display_name="Freeze Sender",
            from_name="Freeze",
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
            name="Freeze Template",
            description=None,
            category="freeze",
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
            name="Freeze Campaign",
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
async def test_freeze_segment_excludes_non_sendable_contacts(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    actor = await _create_admin_actor(auth_user_factory)
    campaign_run_id = await _create_campaign_run(auth_test_context=auth_test_context, actor=actor)

    active_one = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="segment-freeze-active-one@dispatch.test",
            first_name="Active",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )
    active_two = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="segment-freeze-active-two@dispatch.test",
            first_name="Active",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )
    suppressed_by_entry = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="segment-freeze-supp-entry@dispatch.test",
            first_name="Suppressed",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )
    unsubscribed = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="segment-freeze-unsub@dispatch.test",
            first_name="Unsub",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )
    suppressed = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="segment-freeze-suppressed@dispatch.test",
            first_name="Suppressed",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )
    bounced = await auth_test_context.contact_service.create_contact(
        actor=actor,
        payload=ContactCreateRequest(
            email="segment-freeze-bounced@dispatch.test",
            first_name="Bounced",
            source_type="manual",
        ),
        ip_address=None,
        user_agent=None,
    )

    await auth_test_context.contact_service.unsubscribe_contact(
        actor=actor,
        contact_id=unsubscribed.id,
        reason="test",
        ip_address=None,
        user_agent=None,
    )
    await auth_test_context.contact_service.update_contact(
        actor=actor,
        contact_id=suppressed.id,
        payload=ContactUpdateRequest(lifecycle_status="suppressed"),
        ip_address=None,
        user_agent=None,
    )
    await auth_test_context.contact_service.update_contact(
        actor=actor,
        contact_id=bounced.id,
        payload=ContactUpdateRequest(lifecycle_status="bounced"),
        ip_address=None,
        user_agent=None,
    )

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        uow.require_session().add(
            SuppressionEntry(email=suppressed_by_entry.email, reason="manual"),
        )
        await uow.require_session().flush()

    segment = await auth_test_context.segment_service.create_segment(
        actor=actor,
        payload=SegmentCreateRequest(
            name="Freeze Segment",
            description=None,
            dsl_json={"op": "contains", "field": "contact.email", "value": "segment-freeze"},
        ),
        ip_address=None,
        user_agent=None,
    )

    freeze = await auth_test_context.segment_service.freeze_segment(
        segment_id=segment.segment.id,
        campaign_run_id=campaign_run_id,
        chunk_size=2,
    )
    assert freeze.matched_count == 6
    assert freeze.eligible_count == 2
    assert freeze.snapshot_rows == 2
    assert freeze.excluded_counts["excluded_total"] == 4
    assert freeze.excluded_counts["suppressed"] >= 2
    assert freeze.excluded_counts["unsubscribed"] >= 1
    assert freeze.excluded_counts["hard_bounced"] >= 1

    async with auth_test_context.session_factory() as session:
        snapshot_count_stmt = (
            select(func.count())
            .select_from(SegmentSnapshot)
            .where(SegmentSnapshot.campaign_run_id == campaign_run_id)
            .where(SegmentSnapshot.included.is_(True))
        )
        snapshot_count = (await session.execute(snapshot_count_stmt)).scalar_one()
        assert snapshot_count == 2

        included_stmt = (
            select(SegmentSnapshot.contact_id)
            .where(SegmentSnapshot.campaign_run_id == campaign_run_id)
            .where(SegmentSnapshot.included.is_(True))
        )
        included_ids = {row[0] for row in (await session.execute(included_stmt)).all()}
        assert active_one.id in included_ids
        assert active_two.id in included_ids

        run = await session.get(CampaignRun, campaign_run_id)
        assert run is not None
        assert run.eligible_count == 2
