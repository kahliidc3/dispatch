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
