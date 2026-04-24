from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from apps.api.deps import get_current_actor, get_domain_service_dep, require_admin
from apps.workers.celery_app import celery_app
from libs.core.auth.models import User
from libs.core.auth.schemas import CurrentActor, MessageResponse
from libs.core.domains.provisioning import DomainProvisioningStatus
from libs.core.domains.schemas import (
    DomainCreateRequest,
    DomainListResponse,
    DomainProvisionEnqueueResponse,
    DomainProvisioningStatusResponse,
    DomainProvisioningStepResponse,
    DomainProvisionRequest,
    DomainResponse,
    DomainRetireRequest,
    DomainVerifyResponse,
)
from libs.core.domains.service import DomainService

router = APIRouter(prefix="/domains", tags=["domains"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(
    payload: DomainCreateRequest,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    domain_service: Annotated[DomainService, Depends(get_domain_service_dep)],
) -> DomainResponse:
    detail = await domain_service.create_domain(
        actor=actor,
        name=payload.name,
        dns_provider=payload.dns_provider,
        parent_domain=payload.parent_domain,
        ses_region=payload.ses_region,
        default_configuration_set_name=payload.default_configuration_set_name,
        event_destination_sns_topic_arn=payload.event_destination_sns_topic_arn,
        route53_hosted_zone_id=payload.route53_hosted_zone_id,
        cloudflare_zone_id=payload.cloudflare_zone_id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return DomainResponse.from_model(detail.domain, dns_records=detail.dns_records)


@router.get("", response_model=DomainListResponse)
async def list_domains(
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    domain_service: Annotated[DomainService, Depends(get_domain_service_dep)],
) -> DomainListResponse:
    details = await domain_service.list_domains()
    return DomainListResponse(
        items=[
            DomainResponse.from_model(detail.domain, dns_records=detail.dns_records)
            for detail in details
        ]
    )


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: str,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    domain_service: Annotated[DomainService, Depends(get_domain_service_dep)],
) -> DomainResponse:
    detail = await domain_service.get_domain(domain_id)
    return DomainResponse.from_model(detail.domain, dns_records=detail.dns_records)


@router.post("/{domain_id}/verify", response_model=DomainVerifyResponse)
async def verify_domain(
    domain_id: str,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    domain_service: Annotated[DomainService, Depends(get_domain_service_dep)],
) -> DomainVerifyResponse:
    result = await domain_service.verify_domain(
        actor=actor,
        domain_id=domain_id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return DomainVerifyResponse(
        domain=DomainResponse.from_model(result.domain, dns_records=result.dns_records),
        fully_verified=result.fully_verified,
        verified_records=result.verified_records,
        total_records=result.total_records,
    )


@router.post("/{domain_id}/retire", response_model=MessageResponse)
async def retire_domain(
    domain_id: str,
    payload: DomainRetireRequest,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    domain_service: Annotated[DomainService, Depends(get_domain_service_dep)],
) -> MessageResponse:
    await domain_service.retire_domain(
        actor=actor,
        domain_id=domain_id,
        reason=payload.reason,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return MessageResponse(message="Domain retired")


@router.post(
    "/{domain_id}/provision",
    response_model=DomainProvisionEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def provision_domain(
    domain_id: str,
    payload: DomainProvisionRequest,
    request: Request,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    domain_service: Annotated[DomainService, Depends(get_domain_service_dep)],
) -> DomainProvisionEnqueueResponse:
    result = await domain_service.enqueue_domain_provisioning(
        actor=actor,
        domain_id=domain_id,
        force=payload.force,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    if result.status != "verified":
        celery_app.send_task(
            "domains.provision_domain",
            kwargs={"domain_id": result.domain_id, "run_id": result.run_id},
        )
    return DomainProvisionEnqueueResponse(
        domain_id=result.domain_id,
        run_id=result.run_id,
        status=result.status,
    )


@router.get(
    "/{domain_id}/provisioning-status",
    response_model=DomainProvisioningStatusResponse,
)
async def get_domain_provisioning_status(
    domain_id: str,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    domain_service: Annotated[DomainService, Depends(get_domain_service_dep)],
) -> DomainProvisioningStatusResponse:
    status_payload: DomainProvisioningStatus = await domain_service.get_domain_provisioning_status(
        domain_id=domain_id
    )
    return DomainProvisioningStatusResponse(
        domain_id=status_payload.domain_id,
        run_id=status_payload.run_id,
        status=status_payload.status,
        reason_code=status_payload.reason_code,
        started_at=status_payload.started_at,
        completed_at=status_payload.completed_at,
        steps=[
            DomainProvisioningStepResponse(
                name=step.name,
                status=step.status,
                at=step.at,
                message=step.message,
            )
            for step in status_payload.steps
        ],
    )
