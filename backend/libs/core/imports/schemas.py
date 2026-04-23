from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, cast

from pydantic import BaseModel, Field

from libs.core.imports.models import ImportJob, ImportRow

ImportJobStatus = Literal[
    "queued",
    "parsing",
    "validating",
    "upserting",
    "complete",
    "failed",
    "cancelled",
]
ImportRowStatus = Literal["valid", "invalid", "duplicate", "suppressed", "upserted", "errored"]


class ImportErrorRowResponse(BaseModel):
    row_number: int
    parsed_email: str | None
    status: ImportRowStatus
    error_reason: str | None
    raw_data: dict[str, Any]

    @classmethod
    def from_model(cls, row: ImportRow) -> ImportErrorRowResponse:
        return cls(
            row_number=row.row_number,
            parsed_email=row.parsed_email,
            status=cast(ImportRowStatus, row.status),
            error_reason=row.error_reason,
            raw_data=dict(row.raw_data),
        )


class ImportJobResponse(BaseModel):
    id: str
    status: ImportJobStatus
    file_name: str
    file_size_bytes: int
    source_label: str | None
    target_list_id: str | None
    total_rows: int | None
    accepted_rows: int
    rejected_rows: int
    duplicate_rows: int
    valid_rows: int
    invalid_rows: int
    suppressed_rows: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    sample_error_rows: list[ImportErrorRowResponse] = Field(default_factory=list)

    @classmethod
    def from_model(
        cls,
        job: ImportJob,
        *,
        sample_error_rows: list[ImportRow] | None = None,
    ) -> ImportJobResponse:
        rejected = job.invalid_rows + job.duplicate_rows + job.suppressed_rows
        return cls(
            id=job.id,
            status=cast(ImportJobStatus, job.status),
            file_name=job.file_name,
            file_size_bytes=job.file_size_bytes,
            source_label=job.source_label,
            target_list_id=job.target_list_id,
            total_rows=job.total_rows,
            accepted_rows=job.valid_rows,
            rejected_rows=rejected,
            duplicate_rows=job.duplicate_rows,
            valid_rows=job.valid_rows,
            invalid_rows=job.invalid_rows,
            suppressed_rows=job.suppressed_rows,
            error_message=job.error_message,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
            sample_error_rows=[
                ImportErrorRowResponse.from_model(row) for row in (sample_error_rows or [])
            ],
        )


class ImportRunSummary(BaseModel):
    job_id: str
    status: ImportJobStatus
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    suppressed_rows: int
    rows_per_second: float
