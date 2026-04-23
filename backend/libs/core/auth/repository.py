from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.auth.models import ApiKey, AuditLog, User, UserSession


class AuthRepository:
    """CRUD-focused repository for auth, users, sessions, API keys, and audit logs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .where(func.lower(User.email) == email.lower())
            .where(User.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id).where(User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, *, email: str, password_hash: str, role: str) -> User:
        user = User(email=email, password_hash=password_hash, role=role)
        self.session.add(user)
        await self.session.flush()
        return user

    async def list_users(self) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def disable_user(self, user_id: str) -> bool:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(deleted_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def update_user_password_hash(self, user_id: str, password_hash: str) -> bool:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def update_last_login(self, user_id: str) -> None:
        stmt = update(User).where(User.id == user_id).values(last_login_at=datetime.now(UTC))
        await self.session.execute(stmt)

    async def set_mfa_secret(self, user_id: str, encrypted_secret: str) -> None:
        stmt = update(User).where(User.id == user_id).values(mfa_secret=encrypted_secret)
        await self.session.execute(stmt)

    async def clear_mfa_secret(self, user_id: str) -> None:
        stmt = update(User).where(User.id == user_id).values(mfa_secret=None)
        await self.session.execute(stmt)

    async def create_api_key(
        self,
        *,
        name: str,
        key_hash: str,
        key_prefix: str,
        key_last4: str,
        created_by: str,
        expires_at: datetime | None,
    ) -> ApiKey:
        api_key = ApiKey(
            name=name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            key_last4=key_last4,
            created_by=created_by,
            expires_at=expires_at,
        )
        self.session.add(api_key)
        await self.session.flush()
        return api_key

    async def list_api_keys_for_user(self, user_id: str) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.created_by == user_id).order_by(ApiKey.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_api_key_for_user(self, user_id: str, api_key_id: str) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.created_by == user_id).where(ApiKey.id == api_key_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_api_key_candidates_by_prefix(self, key_prefix: str) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.key_prefix == key_prefix)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def revoke_api_key(self, api_key_id: str) -> bool:
        stmt = (
            update(ApiKey)
            .where(ApiKey.id == api_key_id)
            .where(ApiKey.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def touch_api_key_last_used(self, api_key_id: str) -> None:
        stmt = update(ApiKey).where(ApiKey.id == api_key_id).values(last_used_at=datetime.now(UTC))
        await self.session.execute(stmt)

    async def create_user_session(
        self,
        *,
        user_id: str,
        session_token_hash: str,
        csrf_token_hash: str,
        expires_at: datetime,
        ip_address: str | None,
        user_agent: str | None,
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            session_token_hash=session_token_hash,
            csrf_token_hash=csrf_token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            last_seen_at=datetime.now(UTC),
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def get_active_session_by_hash(self, session_token_hash: str) -> UserSession | None:
        now = datetime.now(UTC)
        stmt = (
            select(UserSession)
            .where(UserSession.session_token_hash == session_token_hash)
            .where(UserSession.revoked_at.is_(None))
            .where(UserSession.expires_at > now)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def touch_session_last_seen(self, session_id: str) -> None:
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(last_seen_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)

    async def revoke_session_by_hash(self, session_token_hash: str) -> bool:
        stmt = (
            update(UserSession)
            .where(UserSession.session_token_hash == session_token_hash)
            .where(UserSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def revoke_sessions_for_user(self, user_id: str) -> int:
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)

    async def write_audit_log(
        self,
        *,
        actor_type: str,
        actor_id: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        before_state: dict[str, object] | None = None,
        after_state: dict[str, object] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        log = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(log)
        await self.session.flush()
