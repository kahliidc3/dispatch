from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from libs.core.config import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_engine(settings: Settings) -> AsyncEngine:
    parsed_url = make_url(settings.database_url)
    engine_kwargs: dict[str, int | bool] = {"pool_pre_ping": True}

    # SQLite's in-memory and static pools don't accept pool sizing arguments.
    if not parsed_url.drivername.startswith("sqlite"):
        engine_kwargs.update(
            {
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_timeout": settings.database_pool_timeout,
            }
        )

    return create_async_engine(settings.database_url, **engine_kwargs)


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _build_engine(get_settings())
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session


async def init_db() -> None:
    """Warm a connection and fail fast on startup connectivity issues."""

    async with get_engine().connect() as connection:
        await connection.execute(text("SELECT 1"))


async def dispose_db() -> None:
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()

    _engine = None
    _session_factory = None


async def is_database_ready(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT 1"))
    return bool(result.scalar_one() == 1)
