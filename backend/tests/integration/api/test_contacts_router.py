from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.deps import (
    get_auth_service_dep,
    get_contact_service_dep,
    get_list_service_dep,
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
    app.dependency_overrides[get_contact_service_dep] = lambda: auth_test_context.contact_service
    app.dependency_overrides[get_list_service_dep] = lambda: auth_test_context.list_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unsubscribed_contact_cannot_be_set_back_to_active(
    auth_client: AsyncClient,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="admin-contacts-router@dispatch.test",
        password="correct-password-value",
        role="admin",
    )
    login_response = await auth_client.post(
        "/auth/login",
        json={
            "email": "admin-contacts-router@dispatch.test",
            "password": "correct-password-value",
        },
    )
    assert login_response.status_code == 200

    create_response = await auth_client.post(
        "/contacts",
        json={"email": "router-unsub@dispatch.test", "source_type": "api"},
    )
    assert create_response.status_code == 201
    contact_id = create_response.json()["id"]

    unsubscribe_response = await auth_client.post(
        f"/contacts/{contact_id}/unsubscribe",
        json={"reason": "requested"},
    )
    assert unsubscribe_response.status_code == 200
    assert unsubscribe_response.json()["lifecycle_status"] == "unsubscribed"

    invalid_reactivate = await auth_client.patch(
        f"/contacts/{contact_id}",
        json={"lifecycle_status": "active"},
    )
    assert invalid_reactivate.status_code == 409
    payload = invalid_reactivate.json()
    assert payload["error"]["code"] == "conflict"
