from __future__ import annotations

import asyncio
from typing import Any

from apps.workers import send_tasks
from tests.integration.workers.test_send_tasks import _create_admin_actor, _prepare_campaign

AuthTestContext = Any
UserFactory = Any


def test_send_task_is_idempotent(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: Any,
) -> None:
    from apps.workers import celery_app as celery_module
    from libs.core.campaigns.repository import CampaignRepository

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

    first = send_tasks.send_message(message_id)
    second = send_tasks.send_message(message_id)

    assert first["status"] == "sent"
    assert second["status"] == "sent"
    assert first["ses_message_id"] == second["ses_message_id"]
    assert len(fake_transport.send_calls) == 1
