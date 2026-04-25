import pytest
from sqlalchemy import text

from libs.core.config import reset_settings_cache
from libs.core.db import session as db_session
from libs.core.db.uow import UnitOfWork


@pytest.mark.asyncio
async def test_db_session_lifecycle_and_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    reset_settings_cache()

    await db_session.dispose_db()
    await db_session.init_db()

    async for session in db_session.get_session():
        assert await db_session.is_database_ready(session) is True
        break

    await db_session.dispose_db()
    reset_settings_cache()


@pytest.mark.asyncio
async def test_unit_of_work_commits_and_rolls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    reset_settings_cache()

    await db_session.dispose_db()
    engine = db_session.get_engine()

    async with engine.begin() as conn:
        await conn.execute(text("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)"))

    session_factory = db_session.get_session_factory()

    async with UnitOfWork(session_factory) as uow:
        session = uow.require_session()
        await session.execute(text("INSERT INTO sample (value) VALUES ('ok')"))

    with pytest.raises(RuntimeError):
        UnitOfWork(session_factory).require_session()

    with pytest.raises(ValueError):
        async with UnitOfWork(session_factory) as uow:
            session = uow.require_session()
            await session.execute(text("INSERT INTO sample (value) VALUES ('rollback')"))
            raise ValueError("force rollback")

    async with session_factory() as verify_session:
        result = await verify_session.execute(text("SELECT COUNT(*) FROM sample"))
        assert result.scalar_one() == 1

    await db_session.dispose_db()
    reset_settings_cache()
