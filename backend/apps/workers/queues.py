from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

_DEFAULT_SEND_QUEUE = "send.default"
_QUEUE_SAFE_CHARS_PATTERN = re.compile(r"[^a-z0-9_.-]+")


def queue_name_for_domain(domain_name: str) -> str:
    normalized = _normalize_domain_fragment(domain_name)
    if not normalized:
        return _DEFAULT_SEND_QUEUE
    return f"send.{normalized}"


def task_kwargs_for_send_message(
    *,
    message_id: str,
    domain_id: str,
    domain_name: str,
) -> dict[str, str]:
    return {
        "message_id": message_id,
        "domain_id": domain_id,
        "domain_name": domain_name,
    }


@dataclass(slots=True)
class SendTaskRouter:
    _domain_cache: dict[str, str] = field(default_factory=dict)

    def __call__(
        self,
        name: str,
        args: tuple[object, ...],
        kwargs: Mapping[str, object] | None,
        options: Mapping[str, object] | None,
        task: Any = None,
        **kw: object,
    ) -> dict[str, str] | None:
        _ = (args, options, task, kw)
        if name != "send.send_message":
            return None

        payload = dict(kwargs or {})
        domain_id = _coerce_optional_string(payload.get("domain_id"))
        domain_name = _coerce_optional_string(payload.get("domain_name"))

        if domain_id and domain_name:
            self._domain_cache[domain_id] = domain_name
        elif domain_id:
            domain_name = self._domain_cache.get(domain_id)

        queue = queue_name_for_domain(domain_name or "")
        return {"queue": queue, "routing_key": queue}


def build_send_task_router() -> SendTaskRouter:
    return SendTaskRouter()


def _normalize_domain_fragment(value: str) -> str:
    lowered = value.strip().lower()
    normalized = _QUEUE_SAFE_CHARS_PATTERN.sub("-", lowered)
    return normalized.strip(".-")


def _coerce_optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned
