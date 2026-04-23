from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qs, urlparse

import pyotp
import pytest
from cryptography.fernet import Fernet

from libs.core.auth.schemas import CurrentActor
from libs.core.auth.service import AuthService, InMemoryLoginAttemptStore
from libs.core.errors import (
    AuthenticationError,
    ConflictError,
    PermissionDeniedError,
    RateLimitedError,
    ValidationError,
)

AuthTestContext = Any
UserFactory = Any


@pytest.mark.asyncio
async def test_login_session_and_logout_roundtrip(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    user = await auth_user_factory(
        email="admin@example.com",
        password="correct-horse-battery-staple",
        role="admin",
    )

    login = await auth_test_context.auth_service.login(
        email=user.email,
        password="correct-horse-battery-staple",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    assert login.authenticated is True
    assert login.session_cookie is not None

    actor = await auth_test_context.auth_service.resolve_current_actor(
        authorization=None,
        session_cookie=login.session_cookie,
    )
    assert actor.actor_type == "user"
    assert actor.user.id == user.id

    await auth_test_context.auth_service.logout(session_cookie=login.session_cookie)
    with pytest.raises(AuthenticationError):
        await auth_test_context.auth_service.resolve_current_actor(
            authorization=None,
            session_cookie=login.session_cookie,
        )


@pytest.mark.asyncio
async def test_login_failures_trigger_lockout(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="lock@example.com",
        password="the-right-password",
    )

    for _ in range(3):
        with pytest.raises(AuthenticationError):
            await auth_test_context.auth_service.login(
                email="lock@example.com",
                password="wrong-password",
                ip_address=None,
                user_agent=None,
            )

    with pytest.raises(RateLimitedError):
        await auth_test_context.auth_service.login(
            email="lock@example.com",
            password="wrong-password",
            ip_address=None,
            user_agent=None,
        )


@pytest.mark.asyncio
async def test_mfa_login_challenge_and_verify(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    await auth_user_factory(
        email="mfa@example.com",
        password="top-secret-password",
        mfa_enabled=True,
    )

    initial = await auth_test_context.auth_service.login(
        email="mfa@example.com",
        password="top-secret-password",
        ip_address=None,
        user_agent=None,
    )
    assert initial.authenticated is False
    assert initial.requires_mfa is True
    assert initial.mfa_token is not None

    with pytest.raises(AuthenticationError):
        await auth_test_context.auth_service.verify_mfa_login(
            mfa_token=initial.mfa_token,
            code="000000",
            ip_address=None,
            user_agent=None,
        )

    code = pyotp.TOTP("JBSWY3DPEHPK3PXP").now()
    verified = await auth_test_context.auth_service.verify_mfa_login(
        mfa_token=initial.mfa_token,
        code=code,
        ip_address=None,
        user_agent=None,
    )
    assert verified.authenticated is True
    assert verified.session_cookie is not None


@pytest.mark.asyncio
async def test_mfa_enrollment_flow_updates_user_and_login_path(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    user = await auth_user_factory(
        email="enroll@example.com",
        password="twelve-plus-chars",
    )
    actor = CurrentActor(actor_type="user", user=user)

    enrollment_token, otp_auth_uri = await auth_test_context.user_service.enroll_mfa_start(
        actor=actor
    )
    secret = parse_qs(urlparse(otp_auth_uri).query)["secret"][0]

    with pytest.raises(ValidationError):
        await auth_test_context.user_service.verify_mfa_enrollment(
            actor=actor,
            enrollment_token=enrollment_token,
            code="000000",
            ip_address=None,
            user_agent=None,
        )

    await auth_test_context.user_service.verify_mfa_enrollment(
        actor=actor,
        enrollment_token=enrollment_token,
        code=pyotp.TOTP(secret).now(),
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    login = await auth_test_context.auth_service.login(
        email="enroll@example.com",
        password="twelve-plus-chars",
        ip_address=None,
        user_agent=None,
    )
    assert login.requires_mfa is True


@pytest.mark.asyncio
async def test_api_key_create_rotate_revoke_and_actor_resolution(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    user = await auth_user_factory(
        email="keys@example.com",
        password="twelve-plus-chars",
    )
    actor = CurrentActor(actor_type="user", user=user)

    created = await auth_test_context.user_service.create_api_key(
        actor=actor,
        name="ci-key",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        ip_address=None,
        user_agent=None,
    )
    assert created.plaintext_key.startswith("ak_live_")

    resolved = await auth_test_context.auth_service.resolve_current_actor(
        authorization=f"Bearer {created.plaintext_key}",
        session_cookie=None,
    )
    assert resolved.actor_type == "api_key"
    assert resolved.api_key is not None

    rotated = await auth_test_context.user_service.rotate_api_key(
        actor=actor,
        api_key_id=created.model.id,
        name="ci-key-rotated",
        expires_at=None,
        ip_address=None,
        user_agent=None,
    )
    assert rotated.plaintext_key != created.plaintext_key

    with pytest.raises(AuthenticationError):
        await auth_test_context.auth_service.resolve_current_actor(
            authorization=f"Bearer {created.plaintext_key}",
            session_cookie=None,
        )

    await auth_test_context.user_service.revoke_api_key(
        actor=actor,
        api_key_id=rotated.model.id,
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(AuthenticationError):
        await auth_test_context.auth_service.resolve_current_actor(
            authorization=f"Bearer {rotated.plaintext_key}",
            session_cookie=None,
        )


@pytest.mark.asyncio
async def test_password_change_revokes_sessions(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    user = await auth_user_factory(
        email="pwchange@example.com",
        password="initial-password",
    )

    login = await auth_test_context.auth_service.login(
        email=user.email,
        password="initial-password",
        ip_address=None,
        user_agent=None,
    )
    assert login.session_cookie is not None

    actor = await auth_test_context.auth_service.resolve_current_actor(
        authorization=None,
        session_cookie=login.session_cookie,
    )

    await auth_test_context.user_service.change_password(
        actor=actor,
        current_password="initial-password",
        new_password="newer-password-value",
        ip_address=None,
        user_agent=None,
    )

    with pytest.raises(AuthenticationError):
        await auth_test_context.auth_service.resolve_current_actor(
            authorization=None,
            session_cookie=login.session_cookie,
        )

    relogin = await auth_test_context.auth_service.login(
        email=user.email,
        password="newer-password-value",
        ip_address=None,
        user_agent=None,
    )
    assert relogin.authenticated is True


@pytest.mark.asyncio
async def test_admin_user_management_rules(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin = await auth_user_factory(
        email="root@example.com",
        password="root-password-value",
        role="admin",
    )
    non_admin = await auth_user_factory(
        email="member@example.com",
        password="member-password",
    )
    admin_actor = CurrentActor(actor_type="user", user=admin)
    user_actor = CurrentActor(actor_type="user", user=non_admin)

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.user_service.create_user(
            actor=user_actor,
            email="blocked@example.com",
            password="blocked-password",
            role="user",
            ip_address=None,
            user_agent=None,
        )

    created = await auth_test_context.user_service.create_user(
        actor=admin_actor,
        email="new-user@example.com",
        password="new-user-password",
        role="user",
        ip_address=None,
        user_agent=None,
    )
    assert created.email == "new-user@example.com"

    with pytest.raises(ConflictError):
        await auth_test_context.user_service.create_user(
            actor=admin_actor,
            email="new-user@example.com",
            password="new-user-password",
            role="user",
            ip_address=None,
            user_agent=None,
        )

    await auth_test_context.user_service.disable_user(
        actor=admin_actor,
        user_id=created.id,
        reason="cleanup",
        ip_address=None,
        user_agent=None,
    )


@pytest.mark.asyncio
async def test_service_mfa_key_validation(auth_test_context: AuthTestContext) -> None:
    invalid_settings = auth_test_context.settings.model_copy(
        update={"mfa_kms_data_key": "not-base64"}
    )
    with pytest.raises(ValidationError):
        AuthService(invalid_settings, attempts=InMemoryLoginAttemptStore(invalid_settings))

    valid_key = Fernet.generate_key().decode("utf-8")
    valid_settings = auth_test_context.settings.model_copy(update={"mfa_kms_data_key": valid_key})
    service = AuthService(valid_settings, attempts=InMemoryLoginAttemptStore(valid_settings))
    assert service.decrypt_mfa_secret(service.encrypt_mfa_secret("ABCDEF123456")) == "ABCDEF123456"


@pytest.mark.asyncio
async def test_auth_utility_guards(auth_test_context: AuthTestContext) -> None:
    with pytest.raises(AuthenticationError):
        auth_test_context.auth_service.decode_mfa_enrollment_token("bad-token")

    with pytest.raises(AuthenticationError):
        auth_test_context.auth_service.decrypt_mfa_secret("bad-secret")

    assert auth_test_context.auth_service.verify_password(
        auth_test_context.auth_service.hash_password("hello-world-123"),
        "hello-world-123",
    )
