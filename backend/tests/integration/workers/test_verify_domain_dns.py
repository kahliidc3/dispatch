from __future__ import annotations

import asyncio
from typing import Any

from apps.workers import event_tasks
from libs.core.auth.schemas import CurrentActor
from libs.core.domains.schemas import DnsRecordType

AuthTestContext = Any
UserFactory = Any


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email="worker-admin@dispatch.test",
        password="worker-password-value",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


def test_verify_domain_dns_worker_task(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: Any,
) -> None:
    async def _prepare() -> str:
        actor = await _create_admin_actor(auth_user_factory)
        created = await auth_test_context.domain_service.create_domain(
            actor=actor,
            name="worker-verify.dispatch.test",
            dns_provider="manual",
            parent_domain="dispatch.test",
            ses_region="us-east-1",
            default_configuration_set_name=None,
            event_destination_sns_topic_arn=None,
            ip_address=None,
            user_agent=None,
        )
        for record in created.dns_records:
            auth_test_context.dns_adapter.set_record(
                record_type=DnsRecordType(record.record_type),
                name=record.name,
                values=[record.value],
            )
        return str(created.domain.id)

    domain_id = asyncio.run(_prepare())
    monkeypatch.setattr(event_tasks, "get_domain_service", lambda: auth_test_context.domain_service)

    result = event_tasks.verify_domain_dns(domain_id)
    assert result["domain_id"] == domain_id
    assert result["fully_verified"] is True
    assert result["verified_records"] == result["total_records"]
