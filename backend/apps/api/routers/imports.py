from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from apps.api.deps import get_current_actor, get_import_service_dep, require_admin
from apps.workers.celery_app import celery_app
from libs.core.auth.models import User
from libs.core.auth.schemas import CurrentActor
from libs.core.imports.schemas import ImportJobResponse
from libs.core.imports.service import ImportService
from libs.core.logging import get_logger

logger = get_logger("api.imports")

router = APIRouter(prefix="/imports", tags=["imports"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
async def create_import_job(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    source_label: Annotated[str | None, Form()] = None,
    target_list_id: Annotated[str | None, Form()] = None,
    *,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ImportService, Depends(get_import_service_dep)],
) -> ImportJobResponse:
    file_bytes = await file.read()
    job = await service.create_import_job(
        actor=actor,
        file_name=file.filename or "import.csv",
        file_bytes=file_bytes,
        source_label=source_label,
        target_list_id=target_list_id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    try:
        celery_app.send_task("imports.run_import", kwargs={"job_id": job.id})
    except Exception as exc:
        logger.warning("imports.enqueue_failed", job_id=job.id, error=str(exc))

    return ImportJobResponse.from_model(job)


@router.get("/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: str,
    actor: Annotated[CurrentActor, Depends(get_current_actor)],
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[ImportService, Depends(get_import_service_dep)],
) -> ImportJobResponse:
    return await service.get_import_job(actor=actor, job_id=job_id)
