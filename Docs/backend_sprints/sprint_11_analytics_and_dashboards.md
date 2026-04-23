# Sprint 11 — Analytics & Dashboard APIs

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `backend/sprint-11-analytics`
**Depends on:** Sprint 10

---

## 1. Purpose

Expose the metrics and time-series data the frontend dashboards need: per-campaign delivery stats, per-domain reputation snapshots, and the platform-wide scoreboard. This sprint closes out the MVP phase.

## 2. What Should Be Done

Build `libs/core/analytics/` with services and materialized views (or scheduled rollup tasks) that compute sent / delivered / bounced / complained / opened / clicked counts per campaign, per domain, and per time window. Expose paginated endpoints for dashboard consumption.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.5 Analytics
- [../09_data_model.md](../09_data_model.md) — `rolling_metrics` and event tables
- [../15_observability.md](../15_observability.md) — RED metrics framing
- [../21_domain_model.md](../21_domain_model.md) §2.4 Event & Reputation

## 4. Tasks

### 4.1 Rollup tasks
- [ ] `apps/workers/metrics_tasks.py::rollup_campaign_metrics` — scheduled every 60s; aggregates event counts per campaign_run.
- [ ] `rollup_domain_metrics` — per-domain 24h / 7d windows for bounce, complaint, delivery rates.
- [ ] `rollup_account_metrics` — account-wide rolling stats.
- [ ] Upsert into `rolling_metrics` keyed by `(scope_type, scope_id, window)`.

### 4.2 Analytics API
- [ ] `GET /analytics/campaigns/{id}` → summary + time series.
- [ ] `GET /analytics/domains/{id}` → reputation snapshot, bounce + complaint rates, current circuit-breaker state.
- [ ] `GET /analytics/overview` → account-wide KPIs (sends today, 7d trend, top campaigns, top failing domains).
- [ ] `GET /analytics/campaigns/{id}/messages` paginated list of messages with status and last event.

### 4.3 Query performance
- [ ] Add supporting indexes identified during load testing.
- [ ] Cache hot reads in Redis with 30–60s TTL.
- [ ] Enforce hard timeouts on analytical queries to avoid starving the API pool.

## 5. Deliverables

- Frontend can render campaign and domain dashboards from stable APIs.
- Rollup tasks run on schedule without errors and keep `rolling_metrics` fresh within 60s of event ingestion.

## 6. Exit Criteria

- Integration test: after a seeded event bundle, `/analytics/campaigns/{id}` returns the exact expected counts.
- Load test: dashboard endpoints return in < 200 ms P95 under realistic data volumes.
- No unindexed full-table scans in EXPLAIN for any analytics query.

## 7. Risks to Watch

- Heavy analytics queries blocking OLTP traffic. If latencies regress, move to a read replica in Sprint 20.
- Stale metrics giving false comfort. Expose `last_updated_at` on every response so consumers can detect staleness.
- Unbounded pagination — cap `limit` and use keyset pagination everywhere.

## 8. Tests to Run

- `pytest tests/unit/core/analytics/`
- `pytest tests/integration/workers/test_metrics_tasks.py`
- `pytest tests/integration/api/test_analytics_router.py`
