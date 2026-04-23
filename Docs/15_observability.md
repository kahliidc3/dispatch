# Observability

---

## 13.1 Metrics

Every service exports Prometheus-compatible metrics. Datadog agent scrapes and ships.

- **RED metrics per service:** Rate, Errors, Duration (p50, p95, p99)
- **Business metrics:** `sends_total`, `deliveries_total`, `bounces_total`, `complaints_total` (per domain, per campaign)
- **Queue metrics:** `queue_depth`, `task_latency`, `retry_count`
- **DB metrics:** `connection_pool_usage`, `replication_lag`, `slow_query_count`
- **Reputation metrics:** `postmaster_reputation` (per domain), `seed_inbox_placement`

---

## 13.2 Logging

- **Format:** structured JSON (structlog)
- **Required fields:** `timestamp`, `level`, `service`, `trace_id`, `event`
- **Retention:** 30 days hot in Datadog; 1 year in S3 (Parquet, queryable via Athena)
- **PII policy:** no email addresses, no message bodies, no API keys. Hashes only.

---

## 13.3 Tracing

- OpenTelemetry instrumentation on FastAPI, Celery, SQLAlchemy, boto3
- Trace context propagated through Celery tasks (via task headers)
- Traces ingested into Datadog APM
- Sampling: 100% in staging; 10% in production (with 100% on errors)

---

## 13.4 Alerting

Alerts are tiered by severity. Runbooks link from each alert to `04_operations_runbook.md`.

| Severity | Routing | Response time | Examples |
|---|---|---|---|
| SEV-1 | PagerDuty, wake on-call | < 5 min | Sending stopped, complaint spike > 0.08% |
| SEV-2 | PagerDuty, business hours | < 15 min | Webhook lag, domain burn, DB replication lag |
| SEV-3 | Slack `#alerts` | < 1 hour | Single worker failure, elevated 4xx |
| SEV-4 | Ticket queue | Next day | Metric drift, minor lag |
