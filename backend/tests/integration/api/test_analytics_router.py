from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.deps import (
    get_analytics_service_dep,
    get_auth_service_dep,
    get_settings_dep,
    get_user_service_dep,
)
from apps.api.main import app
from libs.core.analytics.service import reset_analytics_service_cache
from libs.core.campaigns.models import Campaign, Message
from libs.core.db.uow import UnitOfWork
from libs.core.domains.models import Domain
from libs.core.sender_profiles.models import SenderProfile
from libs.core.templates.models import Template, TemplateVersion

AuthTestContext = Any
UserFactory = Any


@pytest.fixture
async def auth_client(auth_test_context: AuthTestContext) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_settings_dep] = lambda: auth_test_context.settings
    app.dependency_overrides[get_auth_service_dep] = lambda: auth_test_context.auth_service
    app.dependency_overrides[get_user_service_dep] = lambda: auth_test_context.user_service
    app.dependency_overrides[get_analytics_service_dep] = (
        lambda: auth_test_context.analytics_service
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
    reset_analytics_service_cache()


async def _login(client: AsyncClient, *, email: str, password: str) -> None:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200


async def _seed_campaign_with_messages(
    auth_test_context: AuthTestContext,
    *,
    message_count: int = 3,
) -> str:
    unique = uuid4().hex[:8]
    async with UnitOfWork(auth_test_context.session_factory) as uow:
        from libs.core.auth.repository import AuthRepository

        repo = AuthRepository(uow.require_session())
        user = await repo.create_user(
            email=f"analytics-api-{unique}@dispatch.test",
            password_hash="x",
            role="admin",
        )
        await uow.require_session().flush()

        domain = Domain(
            name=f"api-analytics-{unique}.dispatch.test",
            verification_status="verified",
            spf_status="verified",
            dkim_status="verified",
            dmarc_status="verified",
            reputation_status="healthy",
        )
        uow.require_session().add(domain)
        await uow.require_session().flush()

        sender = SenderProfile(
            display_name="API Analytics Sender",
            from_name="Dispatch",
            from_email=f"api-{unique}@{domain.name}",
            domain_id=domain.id,
            configuration_set_id=None,
            ip_pool_id=None,
            allowed_campaign_types=["outreach"],
            daily_send_limit=1000,
        )
        uow.require_session().add(sender)
        await uow.require_session().flush()

        template = Template(name=f"t-api-{unique}")
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
            name=f"API Campaign {unique}",
            campaign_type="outreach",
            sender_profile_id=sender.id,
            template_version_id=version.id,
            created_by=user.id,
            status="completed",
            total_sent=message_count,
            total_delivered=message_count - 1,
            total_bounced=1,
            total_complained=0,
            total_opened=1,
            total_clicked=0,
            total_replied=0,
            total_unsubscribed=0,
        )
        uow.require_session().add(campaign)
        await uow.require_session().flush()

        for i in range(message_count):
            msg = Message(
                campaign_id=campaign.id,
                send_batch_id=None,
                contact_id=None,
                sender_profile_id=sender.id,
                domain_id=domain.id,
                to_email=f"r{i}-{unique}@example.com",
                from_email=sender.from_email,
                subject="Test",
                ses_message_id=f"ses-api-{unique}-{i}",
                status="sent",
                sent_at=datetime.now(UTC),
            )
            uow.require_session().add(msg)
        await uow.require_session().flush()

        return campaign.id


@pytest.mark.asyncio
async def test_get_campaign_analytics_requires_auth(
    auth_client: AsyncClient,
) -> None:
    response = await auth_client.get(f"/analytics/campaigns/{uuid4()}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_campaign_analytics_returns_200(
    auth_client: AsyncClient,
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="analytics-reader@dispatch.test",
        password="analytics-pw",
        role="user",
    )
    await _login(auth_client, email="analytics-reader@dispatch.test", password="analytics-pw")
    campaign_id = await _seed_campaign_with_messages(auth_test_context)

    response = await auth_client.get(f"/analytics/campaigns/{campaign_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["campaign_id"] == campaign_id
    assert body["total_sent"] == 3
    assert body["total_delivered"] == 2
    assert body["total_bounced"] == 1
    assert "rolling_windows" in body
    assert "last_updated_at" in body


@pytest.mark.asyncio
async def test_get_campaign_analytics_404_for_unknown(
    auth_client: AsyncClient,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="analytics-reader-404@dispatch.test",
        password="analytics-pw",
        role="user",
    )
    await _login(
        auth_client, email="analytics-reader-404@dispatch.test", password="analytics-pw"
    )

    response = await auth_client.get(f"/analytics/campaigns/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_overview_returns_200(
    auth_client: AsyncClient,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="overview-reader@dispatch.test",
        password="overview-pw",
        role="user",
    )
    await _login(auth_client, email="overview-reader@dispatch.test", password="overview-pw")

    response = await auth_client.get("/analytics/overview")

    assert response.status_code == 200
    body = response.json()
    assert "sends_today" in body
    assert "sends_7d" in body
    assert "top_campaigns" in body
    assert "top_failing_domains" in body
    assert "last_updated_at" in body


@pytest.mark.asyncio
async def test_list_campaign_messages_returns_paginated_results(
    auth_client: AsyncClient,
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="msg-list-reader@dispatch.test",
        password="msg-list-pw",
        role="user",
    )
    await _login(auth_client, email="msg-list-reader@dispatch.test", password="msg-list-pw")
    campaign_id = await _seed_campaign_with_messages(auth_test_context, message_count=5)

    response = await auth_client.get(
        f"/analytics/campaigns/{campaign_id}/messages?limit=3"
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 3
    assert body["next_cursor"] is not None

    cursor = body["next_cursor"]
    response2 = await auth_client.get(
        f"/analytics/campaigns/{campaign_id}/messages?limit=3&cursor={cursor}"
    )
    assert response2.status_code == 200
    body2 = response2.json()
    assert len(body2["items"]) == 2
    assert body2["next_cursor"] is None

    ids1 = {item["message_id"] for item in body["items"]}
    ids2 = {item["message_id"] for item in body2["items"]}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_list_campaign_messages_respects_limit_cap(
    auth_client: AsyncClient,
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="limit-cap-reader@dispatch.test",
        password="limit-cap-pw",
        role="user",
    )
    await _login(auth_client, email="limit-cap-reader@dispatch.test", password="limit-cap-pw")
    campaign_id = await _seed_campaign_with_messages(auth_test_context, message_count=3)

    # limit > 200 is rejected by FastAPI query validation
    response = await auth_client.get(
        f"/analytics/campaigns/{campaign_id}/messages?limit=201"
    )
    assert response.status_code == 422
