from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from typing import cast

from redis import asyncio as redis_async

from libs.core.config import Settings, get_settings
from libs.core.db.session import get_session_factory
from libs.core.db.uow import UnitOfWork
from libs.core.errors import ValidationError
from libs.core.events.repository import EventRepository
from libs.core.events.schemas import EventProcessResult, NormalizedSesEvent
from libs.core.logging import get_logger
from libs.core.suppression.schemas import SuppressionReasonCode
from libs.core.suppression.service import SuppressionService, get_suppression_service

logger = get_logger("core.events")

_ACCOUNT_SCOPE_ID = "00000000-0000-0000-0000-000000000000"
_METRIC_WINDOWS = ("1h", "6h", "24h")


class EventService:
    def __init__(
        self,
        settings: Settings,
        *,
        suppression_service: SuppressionService | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = get_session_factory()
        self._suppression_service = suppression_service or get_suppression_service()
        self._redis = cast(
            redis_async.Redis,
            redis_async.from_url(settings.redis_url, decode_responses=True),  # type: ignore[no-untyped-call]
        )
        self._dedup_fallback: dict[str, float] = {}
        self._metrics_fallback: dict[str, dict[str, int]] = {}

    async def process_ses_event(self, *, payload: dict[str, object]) -> EventProcessResult:
        normalized = self.normalize_payload(payload)
        dedup_key = self._build_dedup_key(normalized)
        first_seen = await self._mark_event_seen(dedup_key)
        if not first_seen:
            return EventProcessResult(
                event_type=normalized.event_type,
                ses_message_id=normalized.ses_message_id,
                deduplicated=True,
                message_found=False,
                occurred_at=normalized.occurred_at,
            )

        status_updated = False
        suppression_written = False
        metrics_updated = False
        message_found = False
        suppression_email: str | None = None
        suppression_reason: SuppressionReasonCode | None = None

        async with UnitOfWork(self._session_factory) as uow:
            repo = EventRepository(uow.require_session())
            message = await repo.get_message_by_ses_message_id(normalized.ses_message_id)
            if message is None:
                return EventProcessResult(
                    event_type=normalized.event_type,
                    ses_message_id=normalized.ses_message_id,
                    deduplicated=False,
                    message_found=False,
                    occurred_at=normalized.occurred_at,
                )

            message_found = True

            if normalized.event_type == "Delivery":
                await repo.insert_delivery_event(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                    smtp_response=normalized.smtp_response,
                    processing_time_ms=normalized.processing_time_ms,
                    raw_payload=normalized.raw_payload,
                )
                status_updated = await repo.mark_message_delivered(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                )
            elif normalized.event_type in {"Bounce", "Reject", "Rendering", "DeliveryDelay"}:
                bounce_type = normalized.bounce_type or "Undetermined"
                bounce_subtype = normalized.bounce_subtype
                diagnostic_code = normalized.diagnostic_code
                if normalized.event_type in {"Reject", "Rendering", "DeliveryDelay"}:
                    bounce_type = "Undetermined"
                    bounce_subtype = normalized.event_type.lower()

                await repo.insert_bounce_event(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                    bounce_type=bounce_type,
                    bounce_subtype=bounce_subtype,
                    diagnostic_code=diagnostic_code,
                    raw_payload=normalized.raw_payload,
                )

                if normalized.event_type != "DeliveryDelay":
                    status_updated = await repo.mark_message_bounced(
                        message_id=message.id,
                        occurred_at=normalized.occurred_at,
                        bounce_type=bounce_type,
                        diagnostic_code=diagnostic_code,
                    )

                if bounce_type == "Permanent" and normalized.recipient_email is not None:
                    suppression_email = normalized.recipient_email
                    suppression_reason = "hard_bounce"
            elif normalized.event_type == "Complaint":
                await repo.insert_complaint_event(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                    complaint_type=normalized.complaint_type,
                    user_agent=normalized.user_agent,
                    feedback_type=normalized.feedback_type,
                    raw_payload=normalized.raw_payload,
                )
                status_updated = await repo.mark_message_complained(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                    complaint_type=normalized.complaint_type,
                )
                if normalized.recipient_email is not None:
                    suppression_email = normalized.recipient_email
                    suppression_reason = "complaint"
            elif normalized.event_type == "Open":
                await repo.insert_open_event(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                    user_agent=normalized.user_agent,
                    ip_address=normalized.ip_address,
                    is_machine_open=normalized.is_machine_open,
                )
                await repo.set_first_opened_at(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                )
            elif normalized.event_type == "Click":
                await repo.insert_click_event(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                    link_url=normalized.link_url or "unknown",
                    user_agent=normalized.user_agent,
                    ip_address=normalized.ip_address,
                )
                await repo.set_first_clicked_at(
                    message_id=message.id,
                    occurred_at=normalized.occurred_at,
                )
            else:
                raise ValidationError(f"Unsupported normalized event_type: {normalized.event_type}")

            increments = self._metric_increments_for_event(normalized.event_type)
            if any(value > 0 for value in increments.values()):
                scopes = [
                    ("domain", message.domain_id),
                    ("sender_profile", message.sender_profile_id),
                    ("account", _ACCOUNT_SCOPE_ID),
                ]
                ip_pool_id = await repo.get_sender_profile_ip_pool_id(message.sender_profile_id)
                if ip_pool_id is not None:
                    scopes.append(("ip_pool", ip_pool_id))

                for scope_type, scope_id in scopes:
                    for window in _METRIC_WINDOWS:
                        await repo.upsert_rolling_metric(
                            scope_type=scope_type,
                            scope_id=scope_id,
                            window=window,
                            window_end=normalized.occurred_at,
                            increments=increments,
                        )
                        await self._increment_metrics_cache(
                            scope_type=scope_type,
                            scope_id=scope_id,
                            window=window,
                            increments=increments,
                        )
                metrics_updated = True

        if suppression_email is not None and suppression_reason is not None:
            suppression_written = await self._suppression_service.upsert_system_suppression(
                email=suppression_email,
                reason_code=suppression_reason,
                source=f"ses_event:{normalized.event_type.lower()}",
            )

        return EventProcessResult(
            event_type=normalized.event_type,
            ses_message_id=normalized.ses_message_id,
            deduplicated=False,
            message_found=message_found,
            status_updated=status_updated,
            suppression_written=suppression_written,
            metrics_updated=metrics_updated,
            occurred_at=normalized.occurred_at,
        )

    def normalize_payload(self, payload: dict[str, object]) -> NormalizedSesEvent:
        if not isinstance(payload, dict):
            raise ValidationError("SNS event payload must be an object")

        raw_event_type = self._coerce_str(payload.get("eventType"), "eventType")
        event_type = self._normalize_event_type(raw_event_type)

        mail = payload.get("mail")
        if not isinstance(mail, dict):
            raise ValidationError("SES payload is missing mail block")

        ses_message_id = self._coerce_str(mail.get("messageId"), "mail.messageId")

        destinations = mail.get("destination")
        recipient_email: str | None = None
        if isinstance(destinations, list) and destinations:
            first_destination = destinations[0]
            if isinstance(first_destination, str):
                recipient_email = first_destination.strip().lower()

        occurred_at = self._extract_occurred_at(payload=payload, mail=mail, event_type=event_type)

        bounce_type: str | None = None
        bounce_subtype: str | None = None
        diagnostic_code: str | None = None
        complaint_type: str | None = None
        feedback_type: str | None = None
        user_agent: str | None = None
        ip_address: str | None = None
        link_url: str | None = None
        smtp_response: str | None = None
        processing_time_ms: int | None = None
        is_machine_open = False

        if event_type == "Delivery":
            delivery = payload.get("delivery")
            if isinstance(delivery, dict):
                smtp_response = self._coerce_optional_str(delivery.get("smtpResponse"))
                processing_time_raw = delivery.get("processingTimeMillis")
                if isinstance(processing_time_raw, int):
                    processing_time_ms = processing_time_raw
                elif isinstance(processing_time_raw, str) and processing_time_raw.isdigit():
                    processing_time_ms = int(processing_time_raw)
        elif event_type == "Bounce":
            bounce = payload.get("bounce")
            if isinstance(bounce, dict):
                bounce_type = self._normalize_bounce_type(
                    self._coerce_optional_str(bounce.get("bounceType"))
                )
                bounce_subtype = self._coerce_optional_str(bounce.get("bounceSubType"))
                recipients = bounce.get("bouncedRecipients")
                if isinstance(recipients, list) and recipients:
                    first_recipient = recipients[0]
                    if isinstance(first_recipient, dict):
                        diagnostic_code = self._coerce_optional_str(
                            first_recipient.get("diagnosticCode")
                        )
                        recipient_candidate = self._coerce_optional_str(
                            first_recipient.get("emailAddress")
                        )
                        if recipient_candidate:
                            recipient_email = recipient_candidate.lower()
        elif event_type == "Complaint":
            complaint = payload.get("complaint")
            if isinstance(complaint, dict):
                complaint_type = self._coerce_optional_str(complaint.get("complaintSubType"))
                feedback_type = self._coerce_optional_str(complaint.get("complaintFeedbackType"))
                user_agent = self._coerce_optional_str(complaint.get("userAgent"))
                recipients = complaint.get("complainedRecipients")
                if isinstance(recipients, list) and recipients:
                    first_recipient = recipients[0]
                    if isinstance(first_recipient, dict):
                        recipient_candidate = self._coerce_optional_str(
                            first_recipient.get("emailAddress")
                        )
                        if recipient_candidate:
                            recipient_email = recipient_candidate.lower()
        elif event_type == "Open":
            open_block = payload.get("open")
            if isinstance(open_block, dict):
                user_agent = self._coerce_optional_str(open_block.get("userAgent"))
                ip_address = self._coerce_optional_str(open_block.get("ipAddress"))
            is_machine_open = self._is_machine_open(user_agent)
        elif event_type == "Click":
            click = payload.get("click")
            if isinstance(click, dict):
                link_url = self._coerce_optional_str(click.get("link"))
                user_agent = self._coerce_optional_str(click.get("userAgent"))
                ip_address = self._coerce_optional_str(click.get("ipAddress"))
        elif event_type in {"Reject", "Rendering", "DeliveryDelay"}:
            reason_block_name = {
                "Reject": "reject",
                "Rendering": "failure",
                "DeliveryDelay": "deliveryDelay",
            }[event_type]
            block = payload.get(reason_block_name)
            if isinstance(block, dict):
                diagnostic_code = self._coerce_optional_str(
                    block.get("reason")
                    or block.get("errorMessage")
                    or block.get("statusCode")
                )

        return NormalizedSesEvent(
            event_type=event_type,
            ses_message_id=ses_message_id,
            occurred_at=occurred_at,
            recipient_email=recipient_email,
            smtp_response=smtp_response,
            processing_time_ms=processing_time_ms,
            bounce_type=bounce_type,
            bounce_subtype=bounce_subtype,
            diagnostic_code=diagnostic_code,
            complaint_type=complaint_type,
            feedback_type=feedback_type,
            user_agent=user_agent,
            ip_address=ip_address,
            link_url=link_url,
            is_machine_open=is_machine_open,
            raw_payload=payload,
        )

    def _build_dedup_key(self, event: NormalizedSesEvent) -> str:
        timestamp = event.occurred_at.astimezone(UTC).isoformat()
        return f"eventdedup:{event.ses_message_id}:{event.event_type}:{timestamp}"

    async def _mark_event_seen(self, dedup_key: str) -> bool:
        now_ts = datetime.now(UTC).timestamp()
        expires_at = now_ts + self._settings.event_dedup_ttl_seconds

        for key in list(self._dedup_fallback.keys()):
            if self._dedup_fallback[key] <= now_ts:
                del self._dedup_fallback[key]

        if dedup_key in self._dedup_fallback:
            return False

        self._dedup_fallback[dedup_key] = expires_at

        if self._settings.app_env == "test":
            return True

        try:
            inserted = await self._redis.set(
                dedup_key,
                "1",
                ex=self._settings.event_dedup_ttl_seconds,
                nx=True,
            )
            if inserted:
                return True
            return False
        except Exception:
            return True

    async def _increment_metrics_cache(
        self,
        *,
        scope_type: str,
        scope_id: str,
        window: str,
        increments: dict[str, int],
    ) -> None:
        key = f"metrics:{scope_type}:{scope_id}:{window}"
        fallback = self._metrics_fallback.setdefault(key, {})
        for field_name, increment in increments.items():
            if increment <= 0:
                continue
            fallback[field_name] = fallback.get(field_name, 0) + increment

        if self._settings.app_env == "test":
            return

        try:
            pipeline = self._redis.pipeline()
            for field_name, increment in increments.items():
                if increment <= 0:
                    continue
                pipeline.hincrby(key, field_name, increment)
            pipeline.expire(key, self._settings.event_dedup_ttl_seconds)
            await pipeline.execute()
        except Exception:
            logger.warning("events.metrics_cache_write_failed", key=key)

    @staticmethod
    def _metric_increments_for_event(event_type: str) -> dict[str, int]:
        base = {
            "sends": 0,
            "deliveries": 0,
            "bounces": 0,
            "complaints": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "unsubscribes": 0,
        }
        if event_type == "Delivery":
            base["deliveries"] = 1
        elif event_type in {"Bounce", "Reject", "Rendering"}:
            base["bounces"] = 1
        elif event_type == "Complaint":
            base["complaints"] = 1
        elif event_type == "Open":
            base["opens"] = 1
        elif event_type == "Click":
            base["clicks"] = 1
        return base

    def _extract_occurred_at(
        self,
        *,
        payload: dict[str, object],
        mail: dict[str, object],
        event_type: str,
    ) -> datetime:
        ordered_paths: list[tuple[str, str]] = []
        if event_type == "Delivery":
            ordered_paths.append(("delivery", "timestamp"))
        elif event_type == "Bounce":
            ordered_paths.append(("bounce", "timestamp"))
        elif event_type == "Complaint":
            ordered_paths.append(("complaint", "timestamp"))
        elif event_type == "Open":
            ordered_paths.append(("open", "timestamp"))
        elif event_type == "Click":
            ordered_paths.append(("click", "timestamp"))
        elif event_type == "Reject":
            ordered_paths.append(("reject", "timestamp"))
        elif event_type == "Rendering":
            ordered_paths.append(("failure", "timestamp"))
        elif event_type == "DeliveryDelay":
            ordered_paths.append(("deliveryDelay", "timestamp"))

        ordered_paths.append(("mail", "timestamp"))

        for block_name, field_name in ordered_paths:
            source: object
            if block_name == "mail":
                source = mail
            else:
                source = payload.get(block_name)
            if not isinstance(source, dict):
                continue
            raw_value = source.get(field_name)
            text_value = self._coerce_optional_str(raw_value)
            if text_value is None:
                continue
            return self._parse_datetime(text_value)

        raise ValidationError("Event payload does not contain a valid timestamp")

    @staticmethod
    def _normalize_event_type(raw_event_type: str) -> str:
        cleaned = raw_event_type.strip()
        mapping = {
            "Rendering Failure": "Rendering",
            "RenderingFailure": "Rendering",
        }
        normalized = mapping.get(cleaned, cleaned)
        allowed = {
            "Delivery",
            "Bounce",
            "Complaint",
            "Open",
            "Click",
            "Reject",
            "Rendering",
            "DeliveryDelay",
        }
        if normalized not in allowed:
            raise ValidationError(f"Unsupported SES eventType: {cleaned}")
        return normalized

    @staticmethod
    def _normalize_bounce_type(raw: str | None) -> str:
        if raw in {"Permanent", "Transient", "Undetermined"}:
            return raw
        return "Undetermined"

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        candidate = value.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise ValidationError("Invalid event timestamp format") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    @staticmethod
    def _coerce_str(value: object, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"Missing or invalid {field_name}")
        return value.strip()

    @staticmethod
    def _coerce_optional_str(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        return cleaned

    @staticmethod
    def _is_machine_open(user_agent: str | None) -> bool:
        if user_agent is None:
            return False
        lowered = user_agent.lower()
        return "googleimageproxy" in lowered or "prefetch" in lowered


@lru_cache(maxsize=1)
def get_event_service() -> EventService:
    return EventService(get_settings())


def reset_event_service_cache() -> None:
    get_event_service.cache_clear()
