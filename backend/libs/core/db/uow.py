from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from libs.core.db.session import get_session_factory


class UnitOfWork:
    """Explicit async transaction boundary for service-layer writes."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._session_factory = session_factory or get_session_factory()
        self.session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        await self.session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.session is None:
            return

        if exc is None:
            await self.session.commit()
        else:
            await self.session.rollback()

        await self.session.close()

    def require_session(self) -> AsyncSession:
        if self.session is None:
            raise RuntimeError("UnitOfWork session accessed before entering context")
        return self.session
