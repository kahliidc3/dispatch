# Sprint 20 — Partitioning, Archival & Performance Hardening

**Phase:** 1M/Day
**Estimated duration:** 1.5 weeks
**Branch:** `backend/sprint-20-partitioning-perf`
**Depends on:** Sprints 10, 11, 16

---

## 1. Purpose

The schema works at 300K/day but starts hurting at 1M+. Partition the hot tables, move aged data to cold storage, and do the last round of query/index tuning needed to sustain 1M sends/day.

## 2. What Should Be Done

Convert `messages` and all event tables to monthly declarative partitions with automatic partition creation. Build an archival pipeline that moves partitions older than N months to S3 (parquet). Run a targeted performance pass on the remaining hot paths.

## 3. Docs to Follow

- [../09_data_model.md](../09_data_model.md) §7.3 Partitioning Strategy
- [../16_rollout_plan.md](../16_rollout_plan.md) §14.4 Phase 4
- [../13_deployment_infrastructure.md](../13_deployment_infrastructure.md) — RDS sizing, read replicas

## 4. Tasks

### 4.1 Partitioning
- [ ] Alembic migration that converts `messages`, `delivery_events`, `bounce_events`, `complaint_events`, `open_events`, `click_events` to declarative range partitioning on `created_at` (monthly).
- [ ] Use `pg_partman` or a scheduled task to auto-create next month's partition.
- [ ] Update queries for partition pruning (always filter by `created_at`).

### 4.2 Archival
- [ ] `scripts/data/archive_events.py` exports partitions older than N months to parquet in S3 and detaches the partition.
- [ ] Metadata catalog in `archived_partitions` table pointing at S3 URIs.
- [ ] Re-hydration script for rare historical analytics queries.

### 4.3 Index & query pass
- [ ] EXPLAIN every analytics and list endpoint; add missing composite indexes.
- [ ] Enable autovacuum tuning for high-churn tables.
- [ ] Add read replica for analytics routes; route via a `read_only=True` session flag.

### 4.4 Backpressure
- [ ] Cap concurrent send tasks platform-wide to protect DB and SES.
- [ ] Prioritized queues: transactional UI / provisioning > campaign sends > metric rollups.

## 5. Deliverables

- `messages` and event tables partitioned and auto-extending.
- Archival pipeline live; cold data accessible via S3.
- Sustained 1M sends/day in a load test without DB saturation.

## 6. Exit Criteria

- Load test: 1M sends in 24h with P95 API latency < 300 ms and no stuck queues.
- Partition pruning verified in EXPLAIN on all relevant queries.
- Archival idempotent and audited; re-hydration tested end-to-end.
- No regressions in existing test suites.

## 7. Risks to Watch

- Long-running migrations on large tables. Use `pg_partman` with gradual migration; never block writes.
- Partition-pruning misses from queries that forgot the `created_at` filter. Add a lint rule.
- Read-replica lag causing stale dashboards. Surface lag on admin view.

## 8. Tests to Run

- `pytest tests/integration/db/test_partition_pruning.py`
- `pytest tests/integration/db/test_archive_restore.py`
- Load test harness in `tests/load/` targeting 1M/day burst profile.
