from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.deps import (
    get_auth_service_dep,
    get_domain_service_dep,
    get_sender_profile_service_dep,
    get_settings_dep,
    get_user_service_dep,
)
from apps.api.main import app
from libs.core.domains.schemas import DnsRecordType

AuthTestContext = Any
UserFactory = Any


@pytest.fixture
async def auth_client(auth_test_context: AuthTestContext) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_settings_dep] = lambda: auth_test_context.settings
    app.dependency_overrides[get_auth_service_dep] = lambda: auth_test_context.auth_service
    app.dependency_overrides[get_user_service_dep] = lambda: auth_test_context.user_service
    app.dependency_overrides[get_domain_service_dep] = lambda: auth_test_context.domain_service
    app.dependency_overrides[get_sender_profile_service_dep] = (
        lambda: auth_test_context.sender_profile_service
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_domains_router_create_verify_retire_roundtrip(
    auth_client: AsyncClient,
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="admin-domains@example.com",
        password="correct-password-value",
        role="admin",
    )

    login_response = await auth_client.post(
        "/auth/login",
        json={"email": "admin-domains@example.com", "password": "correct-password-value"},
    )
    assert login_response.status_code == 200

    create_response = await auth_client.post(
        "/domains",
        json={
            "name": "api.dispatch.test",
            "dns_provider": "manual",
            "parent_domain": "dispatch.test",
            "ses_region": "us-east-1",
            "default_configuration_set_name": "api-default",
        },
    )
    assert create_response.status_code == 201
    create_payload = create_response.json()
    domain_id = create_payload["id"]
    dns_records = create_payload["dns_records"]
    assert len(dns_records) >= 6

    list_response = await auth_client.get("/domains")
    assert list_response.status_code == 200
    assert any(item["id"] == domain_id for item in list_response.json()["items"])

    get_response = await auth_client.get(f"/domains/{domain_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "api.dispatch.test"

    for record in dns_records:
        auth_test_context.dns_adapter.set_record(
            record_type=DnsRecordType(record["record_type"]),
            name=record["name"],
            values=[record["value"]],
        )

    verify_response = await auth_client.post(f"/domains/{domain_id}/verify")
    assert verify_response.status_code == 200
    verify_payload = verify_response.json()
    assert verify_payload["fully_verified"] is True
    assert verify_payload["domain"]["verification_status"] == "verified"

    retire_response = await auth_client.post(
        f"/domains/{domain_id}/retire",
        json={"reason": "domain lifecycle complete"},
    )
    assert retire_response.status_code == 200
    assert retire_response.json()["message"] == "Domain retired"


@pytest.mark.asyncio
async def test_domains_router_provisioning_endpoints_enqueue_and_status(
    auth_client: AsyncClient,
    auth_user_factory: UserFactory,
    monkeypatch: Any,
) -> None:
    await auth_user_factory(
        email="admin-provision@example.com",
        password="correct-password-value",
        role="admin",
    )

    login_response = await auth_client.post(
        "/auth/login",
        json={"email": "admin-provision@example.com", "password": "correct-password-value"},
    )
    assert login_response.status_code == 200

    create_response = await auth_client.post(
        "/domains",
        json={
            "name": "provision-api.dispatch.test",
            "dns_provider": "cloudflare",
            "parent_domain": "dispatch.test",
            "ses_region": "us-east-1",
            "default_configuration_set_name": "api-default",
        },
    )
    assert create_response.status_code == 201
    domain_id = create_response.json()["id"]

    task_calls: list[dict[str, Any]] = []

    def _fake_send_task(task_name: str, *, kwargs: dict[str, str]) -> None:
        task_calls.append({"task_name": task_name, "kwargs": kwargs})

    monkeypatch.setattr("apps.api.routers.domains.celery_app.send_task", _fake_send_task)

    provision_response = await auth_client.post(
        f"/domains/{domain_id}/provision",
        json={"force": False},
    )
    assert provision_response.status_code == 202
    provision_payload = provision_response.json()
    assert provision_payload["domain_id"] == domain_id
    assert provision_payload["status"] == "queued"
    assert len(task_calls) == 1
    assert task_calls[0]["task_name"] == "domains.provision_domain"
    assert task_calls[0]["kwargs"]["domain_id"] == domain_id
    assert task_calls[0]["kwargs"]["run_id"] == provision_payload["run_id"]

    status_response = await auth_client.get(f"/domains/{domain_id}/provisioning-status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["domain_id"] == domain_id
    assert status_payload["run_id"] == provision_payload["run_id"]
    assert status_payload["status"] == "queued"
    assert any(
        step["name"] == "queued" and step["status"] == "queued"
        for step in status_payload["steps"]
    )
