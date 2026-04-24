from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from libs.core.auth import models as auth_models  # noqa: F401
from libs.core.auth.models import User
from libs.core.auth.repository import AuthRepository
from libs.core.auth.service import AuthService, InMemoryLoginAttemptStore, UserService
from libs.core.campaigns import models as campaigns_models  # noqa: F401
from libs.core.config import Settings, get_settings, reset_settings_cache
from libs.core.contacts import models as contacts_models  # noqa: F401
from libs.core.contacts.service import ContactService
from libs.core.db import session as db_session
from libs.core.db.base import Base
from libs.core.db.uow import UnitOfWork
from libs.core.domains import models as domains_models  # noqa: F401
from libs.core.domains.schemas import DnsRecordType
from libs.core.domains.service import DomainService
from libs.core.events import models as events_models  # noqa: F401
from libs.core.imports import models as imports_models  # noqa: F401
from libs.core.imports.service import ImportService, MXLookupAdapter
from libs.core.lists import models as lists_models  # noqa: F401
from libs.core.lists.service import ListService
from libs.core.segments import models as segments_models  # noqa: F401
from libs.core.segments.service import SegmentService
from libs.core.sender_profiles import models as sender_profiles_models  # noqa: F401
from libs.core.sender_profiles.service import SenderProfileService
from libs.core.suppression import models as suppression_models  # noqa: F401
from libs.core.suppression.service import SuppressionService
from libs.core.templates import models as templates_models  # noqa: F401
from libs.core.templates.service import TemplateService
from libs.dns_provisioner.base import DNSVerificationAdapter, normalize_dns_value


class FakeDNSVerificationAdapter(DNSVerificationAdapter):
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], list[str]] = {}

    def set_record(self, *, record_type: DnsRecordType, name: str, values: list[str]) -> None:
        self.records[(record_type.value, name.lower())] = [
            normalize_dns_value(value) for value in values
        ]

    async def lookup(self, *, record_type: DnsRecordType, name: str) -> list[str]:
        return self.records.get((record_type.value, name.lower()), [])


class FakeMXLookupAdapter(MXLookupAdapter):
    def __init__(self) -> None:
        self.mx_results: dict[str, bool] = {}

    def set_result(self, *, domain: str, has_mx: bool) -> None:
        self.mx_results[domain.lower()] = has_mx

    async def has_mx(self, domain: str) -> bool:
        return self.mx_results.get(domain.lower(), True)


@dataclass(slots=True)
class AuthTestContext:
    settings: Settings
    auth_service: AuthService
    user_service: UserService
    domain_service: DomainService
    sender_profile_service: SenderProfileService
    contact_service: ContactService
    list_service: ListService
    segment_service: SegmentService
    import_service: ImportService
    suppression_service: SuppressionService
    template_service: TemplateService
    mx_lookup: FakeMXLookupAdapter
    dns_adapter: FakeDNSVerificationAdapter
    session_factory: async_sessionmaker[AsyncSession]


UserFactory = Callable[..., Awaitable[User]]


@pytest_asyncio.fixture
async def auth_test_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[AuthTestContext]:
    db_file = tmp_path / "dispatch-auth-tests.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("SECRET_KEY", "dispatch-test-secret")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AUTH_LOCKOUT_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("AUTH_LOCKOUT_SECONDS", "60")
    monkeypatch.setenv("AUTH_LOGIN_ATTEMPT_WINDOW_SECONDS", "60")
    monkeypatch.setenv(
        "IMPORT_STORAGE_ROOT",
        str((tmp_path / "import-storage").resolve()),
    )
    monkeypatch.setenv("SUPPRESSION_SES_SYNC_ENABLED", "false")
    monkeypatch.setenv("SUPPRESSION_MAX_REMOVALS_PER_DAY", "2")

    reset_settings_cache()
    await db_session.dispose_db()
    settings = get_settings()

    engine = db_session.get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    auth_service = AuthService(settings, attempts=InMemoryLoginAttemptStore(settings))
    user_service = UserService(auth_service)
    dns_adapter = FakeDNSVerificationAdapter()
    domain_service = DomainService(settings, dns_verifier=dns_adapter)
    sender_profile_service = SenderProfileService()
    contact_service = ContactService(settings)
    list_service = ListService()
    segment_service = SegmentService(settings)
    mx_lookup = FakeMXLookupAdapter()
    import_service = ImportService(settings, mx_lookup=mx_lookup)
    suppression_service = SuppressionService(settings)
    template_service = TemplateService(settings)
    context = AuthTestContext(
        settings=settings,
        auth_service=auth_service,
        user_service=user_service,
        domain_service=domain_service,
        sender_profile_service=sender_profile_service,
        contact_service=contact_service,
        list_service=list_service,
        segment_service=segment_service,
        import_service=import_service,
        suppression_service=suppression_service,
        template_service=template_service,
        mx_lookup=mx_lookup,
        dns_adapter=dns_adapter,
        session_factory=db_session.get_session_factory(),
    )

    try:
        yield context
    finally:
        await db_session.dispose_db()
        reset_settings_cache()


async def create_test_user(
    context: AuthTestContext,
    *,
    email: str,
    password: str,
    role: str = "user",
    mfa_enabled: bool = False,
) -> User:
    password_hash = context.auth_service.hash_password(password)
    async with UnitOfWork(context.session_factory) as uow:
        repository = AuthRepository(uow.require_session())
        user = await repository.create_user(email=email, password_hash=password_hash, role=role)
        if mfa_enabled:
            secret = context.auth_service.encrypt_mfa_secret("JBSWY3DPEHPK3PXP")
            await repository.set_mfa_secret(user.id, secret)
        return user


@pytest.fixture
def auth_user_factory(auth_test_context: AuthTestContext) -> UserFactory:
    async def _factory(
        *,
        email: str,
        password: str,
        role: str = "user",
        mfa_enabled: bool = False,
    ) -> User:
        return await create_test_user(
            auth_test_context,
            email=email,
            password=password,
            role=role,
            mfa_enabled=mfa_enabled,
        )

    return _factory
