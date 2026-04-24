from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SesMetricEvent:
    operation: str
    latency_ms: float
    success: bool
    error_class: str | None = None


class SesMetricsRecorder:
    def record(
        self,
        *,
        operation: str,
        latency_ms: float,
        success: bool,
        error_class: str | None = None,
    ) -> None:
        raise NotImplementedError


class NoopSesMetricsRecorder(SesMetricsRecorder):
    def record(
        self,
        *,
        operation: str,
        latency_ms: float,
        success: bool,
        error_class: str | None = None,
    ) -> None:
        _ = (operation, latency_ms, success, error_class)


@dataclass(slots=True)
class InMemorySesMetricsRecorder(SesMetricsRecorder):
    events: list[SesMetricEvent] = field(default_factory=list)

    def record(
        self,
        *,
        operation: str,
        latency_ms: float,
        success: bool,
        error_class: str | None = None,
    ) -> None:
        self.events.append(
            SesMetricEvent(
                operation=operation,
                latency_ms=latency_ms,
                success=success,
                error_class=error_class,
            )
        )
