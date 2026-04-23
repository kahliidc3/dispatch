from __future__ import annotations

import asyncio
from typing import Any

from apps.workers import import_tasks
from libs.core.auth.schemas import CurrentActor

AuthTestContext = Any
UserFactory = Any


async def _create_admin_actor(auth_user_factory: UserFactory) -> CurrentActor:
    user = await auth_user_factory(
        email="worker-import-admin@dispatch.test",
        password="worker-password-value",
        role="admin",
    )
    return CurrentActor(actor_type="user", user=user)


def test_run_import_worker_task(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
    monkeypatch: Any,
) -> None:
    async def _prepare() -> str:
        actor = await _create_admin_actor(auth_user_factory)
        auth_test_context.mx_lookup.set_result(domain="good.com", has_mx=True)
        auth_test_context.mx_lookup.set_result(domain="nomx.test", has_mx=False)
        csv_content = (
            "email,first_name,last_name\n"
            "valid@good.com,Valid,One\n"
            "invalid-email,Bad,Format\n"
            "nomx@nomx.test,No,Mx\n"
            "info@good.com,Role,Account\n"
        )
        created_job = await auth_test_context.import_service.create_import_job(
            actor=actor,
            file_name="worker-seed.csv",
            file_bytes=csv_content.encode("utf-8"),
            source_label="worker",
            target_list_id=None,
            ip_address=None,
            user_agent=None,
        )
        return str(created_job.id)

    job_id = asyncio.run(_prepare())
    monkeypatch.setattr(
        import_tasks,
        "get_import_service",
        lambda: auth_test_context.import_service,
    )

    result = import_tasks.run_import(job_id)
    assert result["job_id"] == job_id
    assert result["status"] == "complete"
    assert result["total_rows"] == 4
    assert result["valid_rows"] == 1
    assert result["invalid_rows"] == 2
    assert result["suppressed_rows"] == 1
