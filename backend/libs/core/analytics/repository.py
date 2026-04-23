from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.db.session import is_database_ready


class AnalyticsRepository:
    """Temporary repository used for infrastructure readiness checks in Sprint 01."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def database_ready(self) -> bool:
        return await is_database_ready(self.session)
