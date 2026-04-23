from libs.core.analytics.repository import AnalyticsRepository


class AnalyticsService:
    """Service wrapper for analytics/readiness operations."""

    def __init__(self, repository: AnalyticsRepository) -> None:
        self.repository = repository

    async def is_ready(self) -> bool:
        return await self.repository.database_ready()
