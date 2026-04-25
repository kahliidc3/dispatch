from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from apps.api.deps import get_analytics_service_dep, get_current_actor
from libs.core.analytics.schemas import (
    CampaignAnalyticsResponse,
    DomainAnalyticsResponse,
    MessageListItem,
    MessageListResponse,
    OverviewResponse,
    RollingWindowSchema,
    TopCampaignItem,
    TopFailingDomainItem,
)
from libs.core.analytics.service import (
    AnalyticsService,
    CampaignAnalyticsResult,
    DomainAnalyticsResult,
    OverviewResult,
)
from libs.core.auth.schemas import CurrentActor

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _build_campaign_response(result: CampaignAnalyticsResult) -> CampaignAnalyticsResponse:
    return CampaignAnalyticsResponse(
        campaign_id=result.campaign_id,
        campaign_name=result.campaign_name,
        status=result.status,
        total_sent=result.total_sent,
        total_delivered=result.total_delivered,
        total_bounced=result.total_bounced,
        total_complained=result.total_complained,
        total_opened=result.total_opened,
        total_clicked=result.total_clicked,
        total_replied=result.total_replied,
        total_unsubscribed=result.total_unsubscribed,
        rolling_windows=[
            RollingWindowSchema(
                window=w.window,
                sends=w.sends,
                deliveries=w.deliveries,
                bounces=w.bounces,
                complaints=w.complaints,
                opens=w.opens,
                clicks=w.clicks,
                bounce_rate=w.bounce_rate,
                complaint_rate=w.complaint_rate,
                window_end=w.window_end,
            )
            for w in result.rolling_windows
        ],
        last_updated_at=result.last_updated_at,
    )


def _build_domain_response(result: DomainAnalyticsResult) -> DomainAnalyticsResponse:
    return DomainAnalyticsResponse(
        domain_id=result.domain_id,
        domain_name=result.domain_name,
        reputation_status=result.reputation_status,
        circuit_breaker_state=result.circuit_breaker_state,
        rolling_windows=[
            RollingWindowSchema(
                window=w.window,
                sends=w.sends,
                deliveries=w.deliveries,
                bounces=w.bounces,
                complaints=w.complaints,
                opens=w.opens,
                clicks=w.clicks,
                bounce_rate=w.bounce_rate,
                complaint_rate=w.complaint_rate,
                window_end=w.window_end,
            )
            for w in result.rolling_windows
        ],
        last_updated_at=result.last_updated_at,
    )


def _build_overview_response(result: OverviewResult) -> OverviewResponse:
    return OverviewResponse(
        sends_today=result.sends_today,
        sends_7d=result.sends_7d,
        top_campaigns=[
            TopCampaignItem(
                campaign_id=c.campaign_id,
                name=c.name,
                sends_today=c.sends_today,
                delivered=c.delivered,
            )
            for c in result.top_campaigns
        ],
        top_failing_domains=[
            TopFailingDomainItem(
                domain_id=d.domain_id,
                name=d.name,
                bounce_rate=d.bounce_rate,
                circuit_breaker_state=d.circuit_breaker_state,
            )
            for d in result.top_failing_domains
        ],
        last_updated_at=result.last_updated_at,
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignAnalyticsResponse)
async def get_campaign_analytics(
    campaign_id: str,
    _: Annotated[CurrentActor, Depends(get_current_actor)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service_dep)],
) -> CampaignAnalyticsResponse:
    result = await service.get_campaign_analytics(campaign_id=campaign_id)
    return _build_campaign_response(result)


@router.get("/domains/{domain_id}", response_model=DomainAnalyticsResponse)
async def get_domain_analytics(
    domain_id: str,
    _: Annotated[CurrentActor, Depends(get_current_actor)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service_dep)],
) -> DomainAnalyticsResponse:
    result = await service.get_domain_analytics(domain_id=domain_id)
    return _build_domain_response(result)


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    _: Annotated[CurrentActor, Depends(get_current_actor)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service_dep)],
) -> OverviewResponse:
    result = await service.get_overview()
    return _build_overview_response(result)


@router.get("/campaigns/{campaign_id}/messages", response_model=MessageListResponse)
async def list_campaign_messages(
    campaign_id: str,
    _: Annotated[CurrentActor, Depends(get_current_actor)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service_dep)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: Annotated[str | None, Query()] = None,
) -> MessageListResponse:
    page = await service.list_campaign_messages(
        campaign_id=campaign_id,
        limit=limit,
        cursor=cursor,
    )
    return MessageListResponse(
        items=[
            MessageListItem(
                message_id=str(item["message_id"]),
                to_email=str(item["to_email"]),
                status=str(item["status"]),
                created_at=item["created_at"],  # type: ignore[arg-type]
                sent_at=item.get("sent_at"),  # type: ignore[arg-type]
                delivered_at=item.get("delivered_at"),  # type: ignore[arg-type]
                bounce_type=item.get("bounce_type"),  # type: ignore[arg-type]
                complaint_type=item.get("complaint_type"),  # type: ignore[arg-type]
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )
