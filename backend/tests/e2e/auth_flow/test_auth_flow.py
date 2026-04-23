from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import parse_qs, urlparse

import pyotp
import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.deps import get_auth_service_dep, get_settings_dep, get_user_service_dep
from apps.api.main import app

AuthTestContext = Any
UserFactory = Any


@pytest.fixture
async def shared_transport(auth_test_context: AuthTestContext) -> AsyncIterator[ASGITransport]:
    app.dependency_overrides[get_settings_dep] = lambda: auth_test_context.settings
    app.dependency_overrides[get_auth_service_dep] = lambda: auth_test_context.auth_service
    app.dependency_overrides[get_user_service_dep] = lambda: auth_test_context.user_service
    transport = ASGITransport(app=app)
    try:
        yield transport
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_end_to_end_auth_user_api_key_flow(
    shared_transport: ASGITransport,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="admin-flow@example.com",
        password="admin-password-value",
        role="admin",
    )

    async with AsyncClient(transport=shared_transport, base_url="http://test") as admin_client:
        admin_login = await admin_client.post(
            "/auth/login",
            json={"email": "admin-flow@example.com", "password": "admin-password-value"},
        )
        assert admin_login.status_code == 200

        create_user = await admin_client.post(
            "/users",
            json={
                "email": "flow-user@example.com",
                "password": "flow-user-password",
                "role": "user",
            },
        )
        assert create_user.status_code == 201

    async with AsyncClient(transport=shared_transport, base_url="http://test") as user_client:
        initial_login = await user_client.post(
            "/auth/login",
            json={"email": "flow-user@example.com", "password": "flow-user-password"},
        )
        assert initial_login.status_code == 200
        assert initial_login.json()["authenticated"] is True

        enroll_start = await user_client.post("/users/me/mfa/enroll")
        assert enroll_start.status_code == 200
        enrollment_token = enroll_start.json()["enrollment_token"]
        otp_auth_uri = enroll_start.json()["otp_auth_uri"]
        secret = parse_qs(urlparse(otp_auth_uri).query)["secret"][0]

        enroll_verify = await user_client.post(
            "/users/me/mfa/verify",
            json={
                "flow": "enroll",
                "token": enrollment_token,
                "code": pyotp.TOTP(secret).now(),
            },
        )
        assert enroll_verify.status_code == 200

        await user_client.post("/auth/logout")

        mfa_login = await user_client.post(
            "/auth/login",
            json={"email": "flow-user@example.com", "password": "flow-user-password"},
        )
        assert mfa_login.status_code == 200
        assert mfa_login.json()["requires_mfa"] is True
        login_token = mfa_login.json()["mfa_token"]

        mfa_verify = await user_client.post(
            "/auth/mfa/verify",
            json={"flow": "login", "token": login_token, "code": pyotp.TOTP(secret).now()},
        )
        assert mfa_verify.status_code == 200
        assert mfa_verify.json()["authenticated"] is True

        create_key = await user_client.post("/users/me/api-keys", json={"name": "flow-key"})
        assert create_key.status_code == 201
        plaintext_key = create_key.json()["plaintext_key"]
        key_id = create_key.json()["api_key"]["id"]

        protected = await user_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {plaintext_key}"},
        )
        assert protected.status_code == 200

        revoke = await user_client.delete(f"/users/me/api-keys/{key_id}")
        assert revoke.status_code == 200

        rejected = await user_client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {plaintext_key}"},
        )
        assert rejected.status_code == 401
