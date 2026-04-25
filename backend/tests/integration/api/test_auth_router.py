from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pyotp
import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.deps import get_auth_service_dep, get_settings_dep, get_user_service_dep
from apps.api.main import app

AuthTestContext = Any
UserFactory = Any


@pytest.fixture
async def auth_client(auth_test_context: AuthTestContext) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_settings_dep] = lambda: auth_test_context.settings
    app.dependency_overrides[get_auth_service_dep] = lambda: auth_test_context.auth_service
    app.dependency_overrides[get_user_service_dep] = lambda: auth_test_context.user_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_logout_cookie_session_roundtrip(
    auth_client: AsyncClient,
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="session@example.com",
        password="correct-password-value",
        role="admin",
    )

    login_response = await auth_client.post(
        "/auth/login",
        json={"email": "session@example.com", "password": "correct-password-value"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["authenticated"] is True
    assert auth_test_context.settings.session_cookie_name in login_response.headers["set-cookie"]

    me_response = await auth_client.get("/users/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "session@example.com"

    logout_response = await auth_client.post("/auth/logout")
    assert logout_response.status_code == 200

    rejected_response = await auth_client.get("/users/me")
    assert rejected_response.status_code == 401
    assert rejected_response.json()["error"]["code"] == "authentication_error"


@pytest.mark.asyncio
async def test_login_mfa_verify_endpoint(
    auth_client: AsyncClient,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="mfaroute@example.com",
        password="correct-password-value",
        mfa_enabled=True,
    )

    login_response = await auth_client.post(
        "/auth/login",
        json={"email": "mfaroute@example.com", "password": "correct-password-value"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["authenticated"] is False
    assert login_payload["requires_mfa"] is True
    mfa_token = login_payload["mfa_token"]
    assert isinstance(mfa_token, str)

    wrong_flow_response = await auth_client.post(
        "/auth/mfa/verify",
        json={"flow": "enroll", "token": mfa_token, "code": "123456"},
    )
    assert wrong_flow_response.status_code == 422

    verify_response = await auth_client.post(
        "/auth/mfa/verify",
        json={
            "flow": "login",
            "token": mfa_token,
            "code": pyotp.TOTP("JBSWY3DPEHPK3PXP").now(),
        },
    )
    assert verify_response.status_code == 200
    assert verify_response.json() == {
        "authenticated": True,
        "requires_mfa": False,
        "mfa_token": None,
    }
