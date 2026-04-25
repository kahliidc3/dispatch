from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from apps.workers import send_tasks
from libs.core.campaigns.repository import CampaignRepository
from libs.core.campaigns.service import CampaignService
from libs.core.circuit_breaker.models import CircuitBreakerState
from libs.core.circuit_breaker.service import CircuitBreakerService
from libs.core.db.uow import UnitOfWork
from tests.integration.workers.test_send_tasks import _create_admin_actor, _prepare_campaign

AuthTestContext = Any
UserFactory = Any


class _FailingRedisClient:
    async def get(self, key: str) -> object:
        _ = key
        raise RuntimeError("redis unavailable")

    async def setex(self, key: str, ttl: int, value: str) -> object:
        _ = (key, ttl, value)
        raise RuntimeError("redis unavailable")

    async def delete(self, key: str) -> object:
        _ = key
        raise RuntimeError("redis unavailable")


def test_send_task_pauses_and_requeues_when_breaker_open(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: Any,
) -> None:
    from apps.workers import celery_app as celery_module

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

    async def _get_dispatch_target() -> tuple[str, str, str]:
        async with auth_test_context.session_factory() as session:
            repo = CampaignRepository(session)
            targets = await repo.list_queued_message_dispatch_targets_for_run(
                launch.campaign_run.id
            )
            target = targets[0]
            return target.message_id, target.domain_id, target.domain_name

    message_id, domain_id, domain_name = asyncio.run(_get_dispatch_target())

    async def _open_domain_breaker() -> None:
        async with UnitOfWork(auth_test_context.session_factory) as uow:
            uow.require_session().add(
                CircuitBreakerState(
                    scope_type="domain",
                    scope_id=domain_id,
                    state="open",
                    tripped_reason="seed_for_test",
                    tripped_at=datetime.now(UTC),
                    auto_reset_at=datetime.now(UTC) + timedelta(hours=24),
                )
            )
            await uow.require_session().flush()

    asyncio.run(_open_domain_breaker())

    requeues: list[dict[str, object]] = []

    def _capture_send_task(task_name: str, kwargs: dict[str, object], **options: object) -> None:
        assert task_name == "send.send_message"
        requeues.append(
            {
                "kwargs": kwargs,
                "countdown": options.get("countdown"),
            }
        )

    monkeypatch.setattr(send_tasks, "get_campaign_service", lambda: service)
    monkeypatch.setattr(celery_module.celery_app, "send_task", _capture_send_task)

    result = send_tasks.send_message(message_id, domain_id, domain_name)

    assert result["status"] == "paused"
    assert result["error_code"] == "circuit_open"
    assert len(requeues) == 1
    queued_kwargs = requeues[0]["kwargs"]
    assert isinstance(queued_kwargs, dict)
    assert queued_kwargs["message_id"] == message_id
    assert len(fake_transport.send_calls) == 0

    async def _assert_paused() -> None:
        async with auth_test_context.session_factory() as session:
            repo = CampaignRepository(session)
            message = await repo.get_message_by_id(message_id)
            assert message is not None
            assert message.status == "paused"
            assert message.error_code == "circuit_open"

    asyncio.run(_assert_paused())


def test_send_task_fail_closed_when_redis_unavailable(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: Any,
) -> None:
    from apps.workers import celery_app as celery_module

    actor = asyncio.run(_create_admin_actor(auth_user_factory))
    campaign_id, base_service, fake_transport = asyncio.run(
        _prepare_campaign(auth_test_context=auth_test_context, actor=actor)
    )
    monkeypatch.setattr(celery_module.celery_app, "send_task", lambda *args, **kwargs: None)
    launch = asyncio.run(
        base_service.launch_campaign(
            actor=actor,
            campaign_id=campaign_id,
            ip_address=None,
            user_agent=None,
        )
    )

    async def _get_dispatch_target() -> tuple[str, str, str]:
        async with auth_test_context.session_factory() as session:
            repo = CampaignRepository(session)
            targets = await repo.list_queued_message_dispatch_targets_for_run(
                launch.campaign_run.id
            )
            target = targets[0]
            return target.message_id, target.domain_id, target.domain_name

    message_id, domain_id, domain_name = asyncio.run(_get_dispatch_target())

    failing_settings = auth_test_context.settings.model_copy(update={"app_env": "local"})
    failing_breaker = CircuitBreakerService(
        failing_settings,
        redis_client=_FailingRedisClient(),
    )
    service = CampaignService(
        auth_test_context.settings,
        ses_client=base_service._ses_client,  # noqa: SLF001 - test-only reuse
        segment_service=auth_test_context.segment_service,
        circuit_breaker_service=failing_breaker,
    )

    requeues: list[dict[str, object]] = []

    def _capture_send_task(task_name: str, kwargs: dict[str, object], **options: object) -> None:
        assert task_name == "send.send_message"
        requeues.append(
            {
                "kwargs": kwargs,
                "countdown": options.get("countdown"),
            }
        )

    monkeypatch.setattr(send_tasks, "get_campaign_service", lambda: service)
    monkeypatch.setattr(celery_module.celery_app, "send_task", _capture_send_task)

    result = send_tasks.send_message(message_id, domain_id, domain_name)

    assert result["status"] == "paused"
    assert result["error_code"] == "circuit_open"
    assert len(requeues) == 1
    assert len(fake_transport.send_calls) == 0
