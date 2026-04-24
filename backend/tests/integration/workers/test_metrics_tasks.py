from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from libs.core.analytics.repository import AnalyticsRepository
from libs.core.analytics.service import AnalyticsService, reset_analytics_service_cache
from libs.core.campaigns.models import Campaign, Message
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain
from libs.core.sender_profiles.models import SenderProfile

AuthTestContext = Any


def _reset_caches() -> None:
    reset_analytics_service_cache()


async def _seed_sent_message(
    auth_test_context: AuthTestContext,
    *,
    campaign_id: str | None = None,
    sent_at: datetime | None = None,
    bounce_type: str | None = None,
    status: str = "sent",
) -> tuple[str, str]:
    unique = uuid4().hex[:8]
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        domain = Domain(
            name=f"metrics-{unique}.dispatch.test",
            verification_status="verified",
            spf_status="verified",
            dkim_status="verified",
            dmarc_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()

        sender = SenderProfile(
            display_name="Metrics Sender",
            from_name="Dispatch",
            from_email=f"metrics-{unique}@{domain.name}",
            domain_id=domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=1000,
        )
        uow.require_session().add(sender)
        await uow.require_session().flush()

        message = Message(
            campaign_id=campaign_id,
            send_batch_id=None,
            contact_id=None,
            sender_profile_id=sender.id,
            domain_id=domain.id,
            to_email=f"recv-{unique}@example.com",
            from_email=sender.from_email,
            subject="Metrics test",
            ses_message_id=f"ses-metrics-{unique}",
            status=status,
            sent_at=sent_at or datetime.now(UTC),
            bounce_type=bounce_type,
        )
        uow.require_session().add(message)
        await uow.require_session().flush()
        return domain.id, message.id


async def _seed_campaign(
    auth_test_context: AuthTestContext,
    *,
    status: str = "running",
) -> str:
    from libs.core.auth.repository import AuthRepository
    from libs.core.campaigns.models import Campaign
    from libs.core.templates.models import Template, TemplateVersion

    unique = uuid4().hex[:8]
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        repo = AuthRepository(uow.require_session())
        user = await repo.create_user(
            email=f"metrics-admin-{unique}@dispatch.test",
            password_hash="x",
            role="admin",
        )
        await uow.require_session().flush()

        domain = Domain(
            name=f"cmp-domain-{unique}.dispatch.test",
            verification_status="verified",
            spf_status="verified",
            dkim_status="verified",
            dmarc_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()

        sender = SenderProfile(
            display_name="Cmp Sender",
            from_name="Dispatch",
            from_email=f"cmp-{unique}@{domain.name}",
            domain_id=domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=1000,
        )
        uow.require_session().add(sender)
        await uow.require_session().flush()

        template = Template(name=f"t-{unique}")
        uow.require_session().add(template)
        await uow.require_session().flush()

        version = TemplateVersion(
            template_id=template.id,
            version_number=1,
            subject="Hello",
            body_html="<p>Hi</p>",
            body_text="Hi",
            created_by=user.id,
        )
        uow.require_session().add(version)
        await uow.require_session().flush()

        campaign = Campaign(
            name=f"Campaign-{unique}",
            campaign_type="outreach",
            sender_profile_id=sender.id,
            template_version_id=version.id,
            created_by=user.id,
            status=status,
        )
        uow.require_session().add(campaign)
        await uow.require_session().flush()
        return campaign.id


async def test_rollup_campaign_metrics_produces_correct_counts(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    campaign_id = await _seed_campaign(auth_test_context)
    now = datetime.now(UTC)

    # Seed 3 sent messages for this campaign
    for _ in range(3):
        await _seed_sent_message(auth_test_context, campaign_id=campaign_id, sent_at=now)

    # 1 bounced message
    await _seed_sent_message(
        auth_test_context,
        campaign_id=campaign_id,
        sent_at=now,
        bounce_type="Permanent",
        status="bounced",
    )

    service = auth_test_context.analytics_service
    result = await service.rollup_campaign_metrics()

    assert result["campaigns"] >= 1

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        repo = AnalyticsRepository(uow.require_session())
        metrics = await repo.get_rolling_metrics(
            scope_type="campaign",
            scope_id=campaign_id,
            windows=["1h"],
        )

    assert len(metrics) == 1
    m = metrics[0]
    assert m.sends == 4
    assert m.bounces == 1
    assert m.bounce_rate is not None
    from decimal import Decimal
    assert m.bounce_rate == Decimal("0.2500")


async def test_rollup_domain_metrics_produces_correct_counts(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    now = datetime.now(UTC)
    domain_id, _ = await _seed_sent_message(auth_test_context, sent_at=now)
    await _seed_sent_message(auth_test_context, sent_at=now)  # different domain, control

    service = auth_test_context.analytics_service
    await service.rollup_domain_metrics()

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        repo = AnalyticsRepository(uow.require_session())
        metrics = await repo.get_rolling_metrics(
            scope_type="domain",
            scope_id=domain_id,
            windows=["24h"],
        )

    assert len(metrics) == 1
    assert metrics[0].sends == 1


async def test_rollup_account_metrics_sums_all_domains(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    now = datetime.now(UTC)

    # Capture baseline before seeding
    service = auth_test_context.analytics_service
    await service.rollup_account_metrics()

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        repo = AnalyticsRepository(uow.require_session())
        before_metrics = await repo.get_rolling_metrics(
            scope_type="account",
            scope_id="00000000-0000-0000-0000-000000000000",
            windows=["24h"],
        )
    before_sends = before_metrics[0].sends if before_metrics else 0

    # Seed 2 more messages
    await _seed_sent_message(auth_test_context, sent_at=now)
    await _seed_sent_message(auth_test_context, sent_at=now)

    await service.rollup_account_metrics()

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        repo = AnalyticsRepository(uow.require_session())
        after_metrics = await repo.get_rolling_metrics(
            scope_type="account",
            scope_id="00000000-0000-0000-0000-000000000000",
            windows=["24h"],
        )

    assert len(after_metrics) == 1
    assert after_metrics[0].sends == before_sends + 2


async def test_rollup_is_idempotent(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    campaign_id = await _seed_campaign(auth_test_context)
    now = datetime.now(UTC)
    await _seed_sent_message(auth_test_context, campaign_id=campaign_id, sent_at=now)

    service = auth_test_context.analytics_service

    # Run rollup twice — second run should overwrite, not double-count
    await service.rollup_campaign_metrics()
    await service.rollup_campaign_metrics()

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        repo = AnalyticsRepository(uow.require_session())
        metrics = await repo.get_rolling_metrics(
            scope_type="campaign",
            scope_id=campaign_id,
            windows=["1h"],
        )

    assert metrics[0].sends == 1
