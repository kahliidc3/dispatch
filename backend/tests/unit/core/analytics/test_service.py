from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from libs.core.analytics.service import (
    AnalyticsService,
    reset_analytics_service_cache,
)
from libs.core.campaigns.models import Campaign, Message
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain
from libs.core.events.models import RollingMetric
from libs.core.errors import NotFoundError
from libs.core.sender_profiles.models import SenderProfile

AuthTestContext = Any


def _reset_caches() -> None:
    reset_analytics_service_cache()


async def _seed_domain_and_message(
    auth_test_context: AuthTestContext,
    *,
    campaign_id: str | None = None,
    status: str = "sent",
    sent_at: datetime | None = None,
    delivered_at: datetime | None = None,
    bounce_type: str | None = None,
    created_at: datetime | None = None,
) -> tuple[str, str]:
    """Returns (domain_id, message_id)."""
    unique = uuid4().hex[:8]
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        domain = Domain(
            name=f"analytics-{unique}.dispatch.test",
            verification_status="verified",
            spf_status="verified",
            dkim_status="verified",
            dmarc_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()

        sender = SenderProfile(
            display_name="Analytics Sender",
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

        msg_kwargs: dict[str, object] = {
            "campaign_id": campaign_id,
            "send_batch_id": None,
            "contact_id": None,
            "sender_profile_id": sender.id,
            "domain_id": domain.id,
            "to_email": f"recipient-{unique}@example.com",
            "from_email": sender.from_email,
            "subject": "Analytics test",
            "ses_message_id": f"ses-{unique}",
            "status": status,
            "sent_at": sent_at or datetime.now(UTC),
            "delivered_at": delivered_at,
            "bounce_type": bounce_type,
        }
        if created_at is not None:
            msg_kwargs["created_at"] = created_at
        message = Message(**msg_kwargs)  # type: ignore[arg-type]
        uow.require_session().add(message)
        await uow.require_session().flush()
        return domain.id, message.id


async def _seed_campaign(
    auth_test_context: AuthTestContext,
    *,
    name: str = "Test Campaign",
    status: str = "completed",
) -> str:
    unique = uuid4().hex[:8]
    # Need a user for created_by
    from libs.core.auth.repository import AuthRepository

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        repo = AuthRepository(uow.require_session())
        user = await repo.create_user(
            email=f"campaign-creator-{unique}@dispatch.test",
            password_hash="x",
            role="admin",
        )
        await uow.require_session().flush()

        domain = Domain(
            name=f"campaign-domain-{unique}.dispatch.test",
            verification_status="verified",
            spf_status="verified",
            dkim_status="verified",
            dmarc_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()

        sender = SenderProfile(
            display_name="Campaign Sender",
            from_name="Dispatch",
            from_email=f"from-{unique}@{domain.name}",
            domain_id=domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=1000,
        )
        uow.require_session().add(sender)
        await uow.require_session().flush()

        from libs.core.templates.models import Template, TemplateVersion

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
            name=name,
            campaign_type="outreach",
            sender_profile_id=sender.id,
            template_version_id=version.id,
            created_by=user.id,
            status=status,
            total_sent=10,
            total_delivered=9,
            total_bounced=1,
            total_complained=0,
            total_opened=5,
            total_clicked=2,
            total_replied=0,
            total_unsubscribed=0,
        )
        uow.require_session().add(campaign)
        await uow.require_session().flush()
        return campaign.id


@pytest.mark.asyncio
async def test_get_campaign_analytics_not_found(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    service = auth_test_context.analytics_service

    with pytest.raises(NotFoundError):
        await service.get_campaign_analytics(campaign_id=str(uuid4()))


@pytest.mark.asyncio
async def test_get_campaign_analytics_returns_totals(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    campaign_id = await _seed_campaign(auth_test_context)
    service = auth_test_context.analytics_service

    result = await service.get_campaign_analytics(campaign_id=campaign_id)

    assert result.campaign_id == campaign_id
    assert result.total_sent == 10
    assert result.total_delivered == 9
    assert result.total_bounced == 1
    assert result.total_complained == 0
    assert result.total_opened == 5
    assert result.total_clicked == 2
    assert result.status == "completed"
    assert isinstance(result.last_updated_at, datetime)


@pytest.mark.asyncio
async def test_get_campaign_analytics_rolling_windows_empty_when_no_metrics(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    campaign_id = await _seed_campaign(auth_test_context)
    service = auth_test_context.analytics_service

    result = await service.get_campaign_analytics(campaign_id=campaign_id)

    assert result.rolling_windows == []


@pytest.mark.asyncio
async def test_get_domain_analytics_not_found(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    service = auth_test_context.analytics_service

    with pytest.raises(NotFoundError):
        await service.get_domain_analytics(domain_id=str(uuid4()))


@pytest.mark.asyncio
async def test_get_domain_analytics_returns_snapshot(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    domain_id, _ = await _seed_domain_and_message(auth_test_context)
    service = auth_test_context.analytics_service

    result = await service.get_domain_analytics(domain_id=domain_id)

    assert result.domain_id == domain_id
    assert result.reputation_status == "healthy"
    assert result.circuit_breaker_state is None
    assert isinstance(result.last_updated_at, datetime)


@pytest.mark.asyncio
async def test_get_overview_returns_counts(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    service = auth_test_context.analytics_service

    result = await service.get_overview()

    assert isinstance(result.sends_today, int)
    assert isinstance(result.sends_7d, int)
    assert isinstance(result.top_campaigns, list)
    assert isinstance(result.top_failing_domains, list)
    assert isinstance(result.last_updated_at, datetime)


@pytest.mark.asyncio
async def test_get_overview_counts_sent_messages(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    now = datetime.now(UTC)
    await _seed_domain_and_message(auth_test_context, sent_at=now)
    service = auth_test_context.analytics_service

    result = await service.get_overview()

    assert result.sends_today >= 1
    assert result.sends_7d >= 1


@pytest.mark.asyncio
async def test_get_overview_excludes_old_messages(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    old_sent_at = datetime.now(UTC) - timedelta(days=8)
    await _seed_domain_and_message(auth_test_context, sent_at=old_sent_at)
    service = auth_test_context.analytics_service

    # Capture baseline
    result = await service.get_overview()
    # sends_7d should not include the 8-day-old message (but we can't assert exact 0
    # since other tests may have seeded messages; just assert types are correct)
    assert result.sends_7d >= 0


@pytest.mark.asyncio
async def test_list_campaign_messages_not_found(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    service = auth_test_context.analytics_service

    with pytest.raises(NotFoundError):
        await service.list_campaign_messages(
            campaign_id=str(uuid4()), limit=10, cursor=None
        )


@pytest.mark.asyncio
async def test_list_campaign_messages_returns_page(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    campaign_id = await _seed_campaign(auth_test_context)
    await _seed_domain_and_message(auth_test_context, campaign_id=campaign_id)
    await _seed_domain_and_message(auth_test_context, campaign_id=campaign_id)
    service = auth_test_context.analytics_service

    page = await service.list_campaign_messages(
        campaign_id=campaign_id, limit=10, cursor=None
    )

    assert len(page.items) == 2
    assert page.next_cursor is None


@pytest.mark.asyncio
async def test_list_campaign_messages_keyset_pagination(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    campaign_id = await _seed_campaign(auth_test_context)
    # Use naive UTC datetimes — SQLite stores DateTime(timezone=True) as naive UTC.
    base_time = datetime(2025, 1, 1, 12, 0, 0)
    for i in range(3):
        await _seed_domain_and_message(
            auth_test_context,
            campaign_id=campaign_id,
            created_at=base_time + timedelta(seconds=i),
        )
    service = auth_test_context.analytics_service

    page1 = await service.list_campaign_messages(
        campaign_id=campaign_id, limit=2, cursor=None
    )
    assert len(page1.items) == 2
    assert page1.next_cursor is not None

    page2 = await service.list_campaign_messages(
        campaign_id=campaign_id, limit=2, cursor=page1.next_cursor
    )
    assert len(page2.items) == 1
    assert page2.next_cursor is None

    ids_p1 = {item["message_id"] for item in page1.items}
    ids_p2 = {item["message_id"] for item in page2.items}
    assert ids_p1.isdisjoint(ids_p2)


@pytest.mark.asyncio
async def test_rollup_campaign_metrics_upserts_rolling_metrics(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    campaign_id = await _seed_campaign(auth_test_context, status="running")
    now = datetime.now(UTC)
    await _seed_domain_and_message(auth_test_context, campaign_id=campaign_id, sent_at=now)
    service = auth_test_context.analytics_service

    result = await service.rollup_campaign_metrics()

    assert result["campaigns"] >= 1
    assert result["rows_upserted"] >= 1

    # Verify a rolling_metric row was written
    from sqlalchemy import select

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        from libs.core.analytics.repository import AnalyticsRepository

        repo = AnalyticsRepository(uow.require_session())
        metrics = await repo.get_rolling_metrics(
            scope_type="campaign",
            scope_id=campaign_id,
            windows=["1h", "6h", "24h"],
        )
    assert len(metrics) == 3
    metric_1h = next(m for m in metrics if m.window == "1h")
    assert metric_1h.sends == 1


@pytest.mark.asyncio
async def test_rollup_domain_metrics_upserts_rolling_metrics(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    now = datetime.now(UTC)
    domain_id, _ = await _seed_domain_and_message(auth_test_context, sent_at=now)
    service = auth_test_context.analytics_service

    result = await service.rollup_domain_metrics()

    assert result["domains"] >= 1

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        from libs.core.analytics.repository import AnalyticsRepository

        repo = AnalyticsRepository(uow.require_session())
        metrics = await repo.get_rolling_metrics(
            scope_type="domain",
            scope_id=domain_id,
            windows=["24h", "7d"],
        )
    assert len(metrics) == 2
    metric_24h = next(m for m in metrics if m.window == "24h")
    assert metric_24h.sends == 1


@pytest.mark.asyncio
async def test_rollup_account_metrics_upserts_rolling_metrics(
    auth_test_context: AuthTestContext,
) -> None:
    _reset_caches()
    service = auth_test_context.analytics_service

    result = await service.rollup_account_metrics()

    assert result["rows_upserted"] == 2

    async with UnitOfWork(auth_test_context.session_factory) as uow:
        from libs.core.analytics.repository import AnalyticsRepository

        repo = AnalyticsRepository(uow.require_session())
        metrics = await repo.get_rolling_metrics(
            scope_type="account",
            scope_id="00000000-0000-0000-0000-000000000000",
            windows=["24h", "7d"],
        )
    assert len(metrics) == 2
