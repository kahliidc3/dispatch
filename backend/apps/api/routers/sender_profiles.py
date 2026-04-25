from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from apps.api.deps import get_current_actor, get_sender_profile_service_dep, require_admin
from libs.core.auth.models import User
from libs.core.auth.schemas import CurrentActor, MessageResponse
from libs.core.sender_profiles.schemas import (
    SenderProfileCreateRequest,
    SenderProfileDeleteRequest,
    SenderProfileListResponse,
    SenderProfileResponse,
    SenderProfileUpdateRequest,
)
from libs.core.sender_profiles.service import SenderProfileService

router = APIRouter(prefix="/sender-profiles", tags=["sender_profiles"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=SenderProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_sender_profile(
    payload: SenderProfileCreateRequest,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[SenderProfileService, Depends(get_sender_profile_service_dep)],
) -> SenderProfileResponse:
    profile = await service.create_sender_profile(
        actor=actor,
        payload=payload,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return SenderProfileResponse.from_model(profile)


@router.get("", response_model=SenderProfileListResponse)
async def list_sender_profiles(
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[SenderProfileService, Depends(get_sender_profile_service_dep)],
) -> SenderProfileListResponse:
    items = await service.list_sender_profiles(actor=actor)
    return SenderProfileListResponse(
        items=[SenderProfileResponse.from_model(item) for item in items],
    )


@router.patch("/{sender_profile_id}", response_model=SenderProfileResponse)
async def update_sender_profile(
    sender_profile_id: str,
    payload: SenderProfileUpdateRequest,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[SenderProfileService, Depends(get_sender_profile_service_dep)],
) -> SenderProfileResponse:
    profile = await service.update_sender_profile(
        actor=actor,
        sender_profile_id=sender_profile_id,
        payload=payload,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return SenderProfileResponse.from_model(profile)


@router.delete("/{sender_profile_id}", response_model=MessageResponse)
async def delete_sender_profile(
    sender_profile_id: str,
    payload: SenderProfileDeleteRequest,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[SenderProfileService, Depends(get_sender_profile_service_dep)],
) -> MessageResponse:
    await service.delete_sender_profile(
        actor=actor,
        sender_profile_id=sender_profile_id,
        payload=payload,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return MessageResponse(message="Sender profile soft-deleted")
