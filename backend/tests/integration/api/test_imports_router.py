from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.deps import (
    get_auth_service_dep,
    get_import_service_dep,
    get_settings_dep,
    get_user_service_dep,
)
from apps.api.main import app

AuthTestContext = Any
UserFactory = Any


@pytest.fixture
async def auth_client(auth_test_context: AuthTestContext) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_settings_dep] = lambda: auth_test_context.settings
    app.dependency_overrides[get_auth_service_dep] = lambda: auth_test_context.auth_service
    app.dependency_overrides[get_user_service_dep] = lambda: auth_test_context.user_service
    app.dependency_overrides[get_import_service_dep] = lambda: auth_test_context.import_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_imports_router_create_and_get_status(
    auth_client: AsyncClient,
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="admin-imports-router@dispatch.test",
        password="correct-password-value",
        role="admin",
    )
    login_response = await auth_client.post(
        "/auth/login",
        json={
            "email": "admin-imports-router@dispatch.test",
            "password": "correct-password-value",
        },
    )
    assert login_response.status_code == 200

    auth_test_context.mx_lookup.set_result(domain="good.com", has_mx=True)
    auth_test_context.mx_lookup.set_result(domain="nomx.test", has_mx=False)

    csv_content = (
        "email,first_name,last_name\n"
        "valid@good.com,Valid,One\n"
        "invalid-email,Bad,Format\n"
        "nomx@nomx.test,No,Mx\n"
        "info@good.com,Role,Account\n"
        "valid@good.com,Dupe,Row\n"
    )
    create_response = await auth_client.post(
        "/imports",
        files={"file": ("contacts.csv", csv_content, "text/csv")},
        data={"source_label": "integration"},
    )
    assert create_response.status_code == 201
    create_payload = create_response.json()
    job_id = create_payload["id"]
    assert create_payload["status"] == "queued"

    queued_status = await auth_client.get(f"/imports/{job_id}")
    assert queued_status.status_code == 200
    assert queued_status.json()["status"] == "queued"

    await auth_test_context.import_service.run_import_job(job_id=job_id)

    complete_status = await auth_client.get(f"/imports/{job_id}")
    assert complete_status.status_code == 200
    payload = complete_status.json()
    assert payload["status"] == "complete"
    assert payload["total_rows"] == 5
    assert payload["valid_rows"] == 1
    assert payload["invalid_rows"] == 2
    assert payload["suppressed_rows"] == 1
    assert payload["duplicate_rows"] == 1
    assert len(payload["sample_error_rows"]) >= 3
