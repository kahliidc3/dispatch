import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class CursorPaginationParams:
    limit: int = 50
    cursor: str | None = None


@dataclass(frozen=True)
class OffsetPaginationParams:
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class CursorPage[T]:
    items: list[T]
    next_cursor: str | None


@dataclass(frozen=True)
class OffsetPage[T]:
    items: list[T]
    total: int
    limit: int
    offset: int


def encode_cursor(created_at: datetime, record_id: str) -> str:
    # Treat naive datetimes as UTC (SQLite returns naive UTC values).
    utc_dt = created_at if created_at.tzinfo is not None else created_at.replace(tzinfo=UTC)
    payload = {
        "created_at": utc_dt.astimezone(UTC).isoformat(),
        "id": record_id,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
    payload = json.loads(decoded)
    return datetime.fromisoformat(payload["created_at"]), payload["id"]
