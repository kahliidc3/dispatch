from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from apps.api.deps import get_campaign_service_dep, get_current_actor, require_admin
from libs.core.auth.models import User
from libs.core.auth.schemas import CurrentActor
from libs.core.campaigns.schemas import (
    CampaignLaunchResponse,
    CampaignResponse,
    CampaignStateChangeResponse,
)
from libs.core.campaigns.service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/{campaign_id}/launch", response_model=CampaignLaunchResponse)
async def launch_campaign(
    campaign_id: str,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[CampaignService, Depends(get_campaign_service_dep)],
) -> CampaignLaunchResponse:
    result = await service.launch_campaign(
        actor=actor,
        campaign_id=campaign_id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return CampaignLaunchResponse.build(
        campaign=result.campaign,
        campaign_run=result.campaign_run,
        snapshot_rows=result.snapshot_rows,
        created_messages=result.created_messages,
        enqueued_messages=result.enqueued_messages,
        already_launched=result.already_launched,
    )


@router.post("/{campaign_id}/pause", response_model=CampaignStateChangeResponse)
async def pause_campaign(
    campaign_id: str,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[CampaignService, Depends(get_campaign_service_dep)],
) -> CampaignStateChangeResponse:
    result = await service.pause_campaign(
        actor=actor,
        campaign_id=campaign_id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return CampaignStateChangeResponse(
        campaign=CampaignResponse.from_model(result.campaign),
    )


@router.post("/{campaign_id}/resume", response_model=CampaignStateChangeResponse)
async def resume_campaign(
    campaign_id: str,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[CampaignService, Depends(get_campaign_service_dep)],
) -> CampaignStateChangeResponse:
    result = await service.resume_campaign(
        actor=actor,
        campaign_id=campaign_id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return CampaignStateChangeResponse(
        campaign=CampaignResponse.from_model(result.campaign),
        enqueued_messages=result.enqueued_messages,
    )


@router.post("/{campaign_id}/cancel", response_model=CampaignStateChangeResponse)
async def cancel_campaign(
    campaign_id: str,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[CampaignService, Depends(get_campaign_service_dep)],
) -> CampaignStateChangeResponse:
    result = await service.cancel_campaign(
        actor=actor,
        campaign_id=campaign_id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return CampaignStateChangeResponse(
        campaign=CampaignResponse.from_model(result.campaign),
        cancelled_queued_messages=result.cancelled_queued_messages,
    )
