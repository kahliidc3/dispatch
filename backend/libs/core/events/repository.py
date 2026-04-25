from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from libs.core.campaigns.models import Message
from libs.core.events.models import (
    BounceEvent,
    ClickEvent,
    ComplaintEvent,
    DeliveryEvent,
    OpenEvent,
    RollingMetric,
)
from libs.core.sender_profiles.models import SenderProfile


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_message_by_ses_message_id(self, ses_message_id: str) -> Message | None:
        stmt = select(Message).where(Message.ses_message_id == ses_message_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def insert_delivery_event(
        self,
        *,
        message_id: str,
        occurred_at: datetime,
        smtp_response: str | None,
        processing_time_ms: int | None,
        raw_payload: dict[str, object],
    ) -> DeliveryEvent:
        row = DeliveryEvent(
            message_id=message_id,
            occurred_at=occurred_at,
            smtp_response=smtp_response,
            processing_time_ms=processing_time_ms,
            raw_payload=raw_payload,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def insert_bounce_event(
        self,
        *,
        message_id: str,
        occurred_at: datetime,
        bounce_type: str,
        bounce_subtype: str | None,
        diagnostic_code: str | None,
        raw_payload: dict[str, object],
    ) -> BounceEvent:
        row = BounceEvent(
            message_id=message_id,
            occurred_at=occurred_at,
            bounce_type=bounce_type,
            bounce_subtype=bounce_subtype,
            diagnostic_code=diagnostic_code,
            raw_payload=raw_payload,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def insert_complaint_event(
        self,
        *,
        message_id: str,
        occurred_at: datetime,
        complaint_type: str | None,
        user_agent: str | None,
        feedback_type: str | None,
        raw_payload: dict[str, object],
    ) -> ComplaintEvent:
        row = ComplaintEvent(
            message_id=message_id,
            occurred_at=occurred_at,
            complaint_type=complaint_type,
            user_agent=user_agent,
            feedback_type=feedback_type,
            raw_payload=raw_payload,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def insert_open_event(
        self,
        *,
        message_id: str,
        occurred_at: datetime,
        user_agent: str | None,
        ip_address: str | None,
        is_machine_open: bool,
    ) -> OpenEvent:
        row = OpenEvent(
            message_id=message_id,
            occurred_at=occurred_at,
            user_agent=user_agent,
            ip_address=ip_address,
            is_machine_open=is_machine_open,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def insert_click_event(
        self,
        *,
        message_id: str,
        occurred_at: datetime,
        link_url: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> ClickEvent:
        row = ClickEvent(
            message_id=message_id,
            occurred_at=occurred_at,
            link_url=link_url,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def mark_message_delivered(self, *, message_id: str, occurred_at: datetime) -> bool:
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .where(Message.status == "sent")
            .values(status="delivered", delivered_at=occurred_at)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def mark_message_bounced(
        self,
        *,
        message_id: str,
        occurred_at: datetime,
        bounce_type: str | None,
        diagnostic_code: str | None,
    ) -> bool:
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .where(Message.status == "sent")
            .values(
                status="bounced",
                bounce_type=bounce_type,
                error_code="ses_bounce",
                error_message=diagnostic_code,
                delivered_at=occurred_at,
            )
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def mark_message_complained(
        self,
        *,
        message_id: str,
        occurred_at: datetime,
        complaint_type: str | None,
    ) -> bool:
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .where(Message.status == "sent")
            .values(
                status="complained",
                complaint_type=complaint_type,
                error_code="ses_complaint",
                delivered_at=occurred_at,
            )
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def set_first_opened_at(self, *, message_id: str, occurred_at: datetime) -> bool:
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .where(Message.first_opened_at.is_(None))
            .values(first_opened_at=occurred_at)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def set_first_clicked_at(self, *, message_id: str, occurred_at: datetime) -> bool:
        stmt = (
            update(Message)
            .where(Message.id == message_id)
            .where(Message.first_clicked_at.is_(None))
            .values(first_clicked_at=occurred_at)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.session.execute(stmt)
        return bool(getattr(result, "rowcount", 0))

    async def get_sender_profile_ip_pool_id(self, sender_profile_id: str) -> str | None:
        stmt = select(SenderProfile.ip_pool_id).where(SenderProfile.id == sender_profile_id)
        result = await self.session.execute(stmt)
        value = result.scalar_one_or_none()
        if value is None:
            return None
        return str(value)

    async def get_rolling_metric(
        self,
        *,
        scope_type: str,
        scope_id: str,
        window: str,
    ) -> RollingMetric | None:
        stmt = (
            select(RollingMetric)
            .where(RollingMetric.scope_type == scope_type)
            .where(RollingMetric.scope_id == scope_id)
            .where(RollingMetric.window == window)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_rolling_metric(
        self,
        *,
        scope_type: str,
        scope_id: str,
        window: str,
        window_end: datetime,
        increments: dict[str, int],
    ) -> RollingMetric:
        metric = await self.get_rolling_metric(
            scope_type=scope_type,
            scope_id=scope_id,
            window=window,
        )
        if metric is None:
            metric = RollingMetric(
                scope_type=scope_type,
                scope_id=scope_id,
                window=window,
                window_end=window_end,
                sends=max(increments.get("sends", 0), 0),
                deliveries=max(increments.get("deliveries", 0), 0),
                bounces=max(increments.get("bounces", 0), 0),
                complaints=max(increments.get("complaints", 0), 0),
                opens=max(increments.get("opens", 0), 0),
                clicks=max(increments.get("clicks", 0), 0),
                replies=max(increments.get("replies", 0), 0),
                unsubscribes=max(increments.get("unsubscribes", 0), 0),
                updated_at=datetime.now(UTC),
            )
            self.session.add(metric)
            await self.session.flush()
            return metric

        metric.window_end = max(
            self._coerce_utc(metric.window_end),
            self._coerce_utc(window_end),
        )
        metric.sends += increments.get("sends", 0)
        metric.deliveries += increments.get("deliveries", 0)
        metric.bounces += increments.get("bounces", 0)
        metric.complaints += increments.get("complaints", 0)
        metric.opens += increments.get("opens", 0)
        metric.clicks += increments.get("clicks", 0)
        metric.replies += increments.get("replies", 0)
        metric.unsubscribes += increments.get("unsubscribes", 0)
        metric.updated_at = datetime.now(UTC)
        await self.session.flush()
        return metric

    @staticmethod
    def _coerce_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
