# Sprint 16 — Full Observability Stack

**Phase:** Scale
**Estimated duration:** 1 week
**Branch:** `backend/sprint-16-observability`
**Depends on:** Sprints 01 (logging baseline), 10 (event pipeline), 13 (circuit breakers)

---

## 1. Purpose

Upgrade observability from "structured logs" to a full production stack: distributed tracing, RED metrics on every service boundary, and a four-tier alerting policy wired to on-call. You cannot run 300K sends/day without this.

## 2. What Should Be Done

Add OpenTelemetry instrumentation to API, webhook, and workers. Publish RED metrics to the metrics backend. Define alert rules for SEV-1 through SEV-4 signals and wire them to the pager of record.

## 3. Docs to Follow

- [../15_observability.md](../15_observability.md) — the spec for this sprint
- [../04_operations_runbook.md](../04_operations_runbook.md) — response procedures the alerts will reference

## 4. Tasks

### 4.1 Tracing
- [ ] OpenTelemetry SDK setup for FastAPI, SQLAlchemy, Celery, Redis, httpx.
- [ ] Trace context propagation from inbound HTTP → Celery task → SES client → webhook.
- [ ] Export via OTLP to the chosen backend (Jaeger locally, managed backend in prod).

### 4.2 Metrics (RED)
- [ ] Rate / Error / Duration for every API route.
- [ ] Rate / Error / Duration for every Celery task.
- [ ] Business metrics: sends/minute, bounce rate, complaint rate, circuit breaker states.
- [ ] Token bucket metrics: denials/minute per domain.

### 4.3 Logging polish
- [ ] Log sampling for high-volume debug lines in production.
- [ ] Redact PII (emails) at the log layer; enforce with a test that fails if unredacted emails appear.
- [ ] Correlate logs, traces, metrics via `trace_id` and `request_id`.

### 4.4 Alerts
- [ ] SEV-1 alerts: account circuit breaker open, API down, webhook backlog > N, DB at > 85% CPU for 5 minutes.
- [ ] SEV-2: domain circuit breaker open, bounce rate spike, token-bucket denial surge.
- [ ] SEV-3: warmup domain above budget, analytics rollup > 5 min behind.
- [ ] SEV-4: housekeeping failures.
- [ ] Route to PagerDuty/Opsgenie with appropriate escalation.

### 4.5 Dashboards
- [ ] Sending scoreboard dashboard (account view).
- [ ] Per-domain dashboard.
- [ ] Pipeline health dashboard (queues, workers, DB, Redis).

## 5. Deliverables

- A single trace spans request → service → DB → Celery → SES → webhook return.
- Every SEV tier has at least one alert wired and tested.
- On-call dashboard set is live.

## 6. Exit Criteria

- Fire-drill: manually trip a domain circuit breaker in staging → SEV-2 page fires and resolves correctly.
- Fire-drill: mid-send API outage → SEV-1 page fires within 60s.
- Smoke test: no unredacted email addresses in sampled production-path logs over a 1h load test.
- Team runbook links are valid from every alert.

## 7. Risks to Watch

- Alert fatigue: too many SEV-3/4 pages. Tune thresholds, do not widen pager scope.
- Telemetry overhead on hot paths (especially send task). Benchmark and cap sampling.
- PII leakage in traces/log attributes. Scrub before export.

## 8. Tests to Run

- `pytest tests/integration/observability/test_trace_propagation.py`
- `pytest tests/unit/observability/test_redaction.py`
- Manual fire-drills documented in [../04_operations_runbook.md](../04_operations_runbook.md).
