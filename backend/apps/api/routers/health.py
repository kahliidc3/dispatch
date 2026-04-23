from typing import Annotated

from fastapi import APIRouter, Depends

from apps.api.deps import get_analytics_service
from libs.core.analytics.schemas import ReadinessResponse
from libs.core.analytics.service import AnalyticsService
from libs.core.errors import ExternalServiceError

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=ReadinessResponse)
async def healthz() -> ReadinessResponse:
    return ReadinessResponse(status="ok")


@router.get("/readyz", response_model=ReadinessResponse)
async def readyz(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ReadinessResponse:
    if not await service.is_ready():
        raise ExternalServiceError("Database readiness check failed")
    return ReadinessResponse(status="ready")
