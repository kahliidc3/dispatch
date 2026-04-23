from __future__ import annotations

import logging
import re
import sys
from contextvars import ContextVar
from typing import cast

import structlog
from structlog.typing import EventDict, WrappedLogger

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
_service_name: str = "dispatch-api"
_REDACTED = "[REDACTED]"
_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "api_key",
    "session",
    "cookie",
    "authorization",
)
_API_KEY_PATTERN = re.compile(r"\bak_live_[a-zA-Z0-9]+_[a-zA-Z0-9]+\b")
_BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+\b", re.IGNORECASE)


def _ensure_required_fields(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    event_dict.setdefault("request_id", request_id_var.get())
    event_dict.setdefault("trace_id", trace_id_var.get() or request_id_var.get())
    event_dict.setdefault("service", _service_name)
    event_dict.setdefault("event", event_dict.get("event", "log"))
    return event_dict


def _redact_string(value: str) -> str:
    redacted = _API_KEY_PATTERN.sub(_REDACTED, value)
    redacted = _BEARER_PATTERN.sub("Bearer [REDACTED]", redacted)
    return redacted


def _redact_value(key: str | None, value: object) -> object:
    if key and any(fragment in key.lower() for fragment in _SENSITIVE_KEY_FRAGMENTS):
        return _REDACTED

    if isinstance(value, dict):
        return {str(k): _redact_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_value(None, item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(None, item) for item in value)
    if isinstance(value, str):
        return _redact_string(value)
    return value


def _redact_sensitive_fields(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    return cast(EventDict, {key: _redact_value(key, value) for key, value in event_dict.items()})


def configure_logging(*, service_name: str, log_level: str = "INFO") -> None:
    global _service_name
    _service_name = service_name

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            _ensure_required_fields,
            _redact_sensitive_fields,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


def bind_request_context(*, request_id: str, trace_id: str | None = None) -> None:
    request_id_var.set(request_id)
    trace_id_var.set(trace_id or request_id)
    structlog.contextvars.bind_contextvars(request_id=request_id, trace_id=trace_id or request_id)


def clear_request_context() -> None:
    structlog.contextvars.clear_contextvars()
    request_id_var.set(None)
    trace_id_var.set(None)


def get_request_id() -> str | None:
    return request_id_var.get()
