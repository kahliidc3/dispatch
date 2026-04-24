from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from apps.api.deps import get_contact_service_dep
from libs.core.auth.schemas import MessageResponse
from libs.core.contacts.service import ContactService

router = APIRouter(prefix="/u", tags=["unsubscribe"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/{token}", response_class=HTMLResponse)
async def unsubscribe_get(
    token: str,
    request: Request,
    service: Annotated[ContactService, Depends(get_contact_service_dep)],
) -> HTMLResponse:
    await service.unsubscribe_public(
        token=token,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return HTMLResponse(
        "<html><body><h1>Unsubscribed</h1><p>You will no longer receive emails.</p></body></html>",
        status_code=200,
    )


@router.post("/{token}", response_model=MessageResponse)
async def unsubscribe_post(
    token: str,
    request: Request,
    service: Annotated[ContactService, Depends(get_contact_service_dep)],
) -> MessageResponse:
    await service.unsubscribe_public(
        token=token,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return MessageResponse(message="Contact unsubscribed")
