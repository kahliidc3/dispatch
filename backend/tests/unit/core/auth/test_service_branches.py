from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from libs.core.auth.schemas import CurrentActor
from libs.core.auth.service import (
    AuthService,
    InMemoryLoginAttemptStore,
    RedisLoginAttemptStore,
    get_auth_service,
    get_user_service,
)
from libs.core.config import get_settings
from libs.core.errors import (
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

AuthTestContext = Any
UserFactory = Any


class _FakePipeline:
    def __init__(self, attempts: int) -> None:
        self._attempts = attempts

    def incr(self, _: str) -> None:
        return None

    def expire(self, _: str, __: int) -> None:
        return None

    async def execute(self) -> list[int]:
        return [self._attempts, 1]


class _FakeRedisClient:
    def __init__(
        self,
        *,
        attempts: int = 1,
        exists_value: int = 0,
        fail_ops: bool = False,
    ) -> None:
        self._attempts = attempts
        self._exists_value = exists_value
        self._fail_ops = fail_ops
        self.set_calls: list[tuple[str, str, int]] = []
        self.delete_calls: list[tuple[str, str]] = []

    async def exists(self, _: str) -> int:
        if self._fail_ops:
            raise RuntimeError("redis down")
        return self._exists_value

    def pipeline(self, transaction: bool) -> _FakePipeline:
        if self._fail_ops:
            raise RuntimeError("redis down")
        assert transaction is True
        return _FakePipeline(self._attempts)

    async def set(self, key: str, value: str, *, ex: int) -> None:
        if self._fail_ops:
            raise RuntimeError("redis down")
        self.set_calls.append((key, value, ex))

    async def delete(self, fail_key: str, lock_key: str) -> None:
        if self._fail_ops:
            raise RuntimeError("redis down")
        self.delete_calls.append((fail_key, lock_key))


@pytest.mark.asyncio
async def test_inmemory_attempt_store_expiry_paths(auth_test_context: AuthTestContext) -> None:
    store = InMemoryLoginAttemptStore(auth_test_context.settings)
    now = datetime.now(UTC)

    store._locks["a@example.com"] = now - timedelta(seconds=1)  # noqa: SLF001
    assert await store.is_locked("a@example.com") is False

    store._attempts["b@example.com"] = (2, now - timedelta(seconds=1))  # noqa: SLF001
    await store.register_failure("b@example.com")
    attempts, _ = store._attempts["b@example.com"]  # noqa: SLF001
    assert attempts == 1


@pytest.mark.asyncio
async def test_redis_attempt_store_success(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    fake = _FakeRedisClient(attempts=settings.auth_lockout_max_attempts, exists_value=1)
    monkeypatch.setattr(
        "libs.core.auth.service.redis_async.from_url",
        lambda *_args, **_kwargs: fake,
    )

    store = RedisLoginAttemptStore(settings)
    assert await store.is_locked("user@example.com") is True
    await store.register_failure("user@example.com")
    await store.clear_failures("user@example.com")

    assert len(fake.set_calls) == 1
    assert len(fake.delete_calls) == 1


@pytest.mark.asyncio
async def test_redis_attempt_store_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    fake = _FakeRedisClient(fail_ops=True)
    monkeypatch.setattr(
        "libs.core.auth.service.redis_async.from_url",
        lambda *_args, **_kwargs: fake,
    )

    store = RedisLoginAttemptStore(settings)
    assert await store.is_locked("user@example.com") is False
    await store.register_failure("user@example.com")
    await store.clear_failures("user@example.com")


@pytest.mark.asyncio
async def test_authservice_error_branches(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    user = await auth_user_factory(
        email="branch@example.com",
        password="branch-password-value",
    )
    service = auth_test_context.auth_service
    assert service.password_hasher is not None

    with pytest.raises(AuthenticationError):
        await service.login(
            email="missing@example.com",
            password="does-not-matter",
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(AuthenticationError):
        await service.resolve_current_actor(authorization=None, session_cookie=None)

    with pytest.raises(AuthenticationError):
        await service.resolve_current_actor(
            authorization=None,
            session_cookie="invalid-cookie",
        )

    fake_cookie = service._session_serializer.dumps({"token": "does-not-exist"})  # noqa: SLF001
    with pytest.raises(AuthenticationError):
        await service.resolve_current_actor(
            authorization=None,
            session_cookie=fake_cookie,
        )

    bad_user_token = service._mfa_login_serializer.dumps(  # noqa: SLF001
        {"user_id": "00000000-0000-0000-0000-000000000000"}
    )
    with pytest.raises(AuthenticationError):
        await service.verify_mfa_login(
            mfa_token=bad_user_token,
            code="123456",
            ip_address=None,
            user_agent=None,
        )

    invalid_shape_token = service._mfa_login_serializer.dumps("bad-payload")  # noqa: SLF001
    with pytest.raises(AuthenticationError):
        service._deserialize_mfa_token(invalid_shape_token, flow="login")  # noqa: SLF001

    with pytest.raises(ValidationError):
        service.decode_mfa_enrollment_token(
            service._mfa_enroll_serializer.dumps({"user_id": user.id})  # noqa: SLF001
        )

    with pytest.raises(AuthenticationError):
        await service.resolve_current_actor(
            authorization="Bearer not-a-valid-key",
            session_cookie=None,
        )

    with pytest.raises(AuthenticationError):
        await service.resolve_current_actor(
            authorization="Bearer ak_live_x_y",
            session_cookie=None,
        )

    with pytest.raises(AuthenticationError):
        await service.verify_mfa_login(
            mfa_token=service._mfa_login_serializer.dumps({}),  # noqa: SLF001
            code="123456",
            ip_address=None,
            user_agent=None,
        )

    assert await service.logout(session_cookie=None) is None


@pytest.mark.asyncio
async def test_user_service_permission_and_notfound_branches(
    auth_test_context: AuthTestContext,
    auth_user_factory: UserFactory,
) -> None:
    admin = await auth_user_factory(
        email="admin-branch@example.com",
        password="admin-password-value",
        role="admin",
    )
    user = await auth_user_factory(
        email="user-branch@example.com",
        password="user-password-value",
        role="user",
    )
    admin_actor = CurrentActor(actor_type="user", user=admin)
    user_actor = CurrentActor(actor_type="user", user=user)

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.user_service.list_users(actor=user_actor)

    with pytest.raises(PermissionDeniedError):
        await auth_test_context.user_service.disable_user(
            actor=user_actor,
            user_id=admin.id,
            reason=None,
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.user_service.disable_user(
            actor=admin_actor,
            user_id="00000000-0000-0000-0000-000000000000",
            reason=None,
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(AuthenticationError):
        await auth_test_context.user_service.change_password(
            actor=user_actor,
            current_password="wrong-password",
            new_password="updated-password-value",
            ip_address=None,
            user_agent=None,
        )

    enroll_token, _ = await auth_test_context.user_service.enroll_mfa_start(actor=admin_actor)
    with pytest.raises(PermissionDeniedError):
        await auth_test_context.user_service.verify_mfa_enrollment(
            actor=user_actor,
            enrollment_token=enroll_token,
            code="123456",
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.user_service.rotate_api_key(
            actor=user_actor,
            api_key_id="00000000-0000-0000-0000-000000000000",
            name=None,
            expires_at=None,
            ip_address=None,
            user_agent=None,
        )

    with pytest.raises(NotFoundError):
        await auth_test_context.user_service.revoke_api_key(
            actor=user_actor,
            api_key_id="00000000-0000-0000-0000-000000000000",
            ip_address=None,
            user_agent=None,
        )

    assert await auth_test_context.user_service.get_user(actor=user_actor) == user
    assert await auth_test_context.user_service.list_api_keys(actor=user_actor) == []


def test_service_singletons_and_mfa_key_length_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    short_decoded_key = base64.urlsafe_b64encode(b"short-key").decode("utf-8")
    settings = get_settings().model_copy(update={"mfa_kms_data_key": short_decoded_key})
    with pytest.raises(ValidationError):
        AuthService(settings, attempts=InMemoryLoginAttemptStore(settings))

    fake_redis = _FakeRedisClient()
    monkeypatch.setattr(
        "libs.core.auth.service.redis_async.from_url",
        lambda *_args, **_kwargs: fake_redis,
    )
    get_auth_service.cache_clear()
    get_user_service.cache_clear()
    try:
        assert get_auth_service() is get_auth_service()
        assert get_user_service() is get_user_service()
    finally:
        get_auth_service.cache_clear()
        get_user_service.cache_clear()
