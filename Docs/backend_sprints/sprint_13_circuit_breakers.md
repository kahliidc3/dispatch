# Sprint 13 — Circuit Breakers (4 Scopes) & Evaluator

**Phase:** Scale
**Estimated duration:** 1 week
**Branch:** `backend/sprint-13-circuit-breakers`
**Depends on:** Sprints 10 (rolling metrics), 12 (per-domain queues)

---

## 1. Purpose

Implement the deliverability safety net: automated circuit breakers that pause sending when bounce or complaint rates exceed safe thresholds — set at *half* of SES's warning levels so we react before AWS does.

## 2. What Should Be Done

Build `libs/core/circuit_breaker/` covering all four scopes (domain, IP pool, sender profile, account). A scheduled evaluator runs every 60 seconds, reads rolling metrics, and flips breaker state. Send tasks (Sprint 09) consult the breaker state and refuse to send when any relevant scope is `open`.

## 3. Docs to Follow

- [../11_operational_guardrails.md](../11_operational_guardrails.md) §9.1 Circuit Breakers (thresholds table)
- [../../CLAUDE.md](../../CLAUDE.md) — "Circuit Breakers" invariants (fail-closed)
- [../09_data_model.md](../09_data_model.md) — `circuit_breaker_state`
- [../21_domain_model.md](../21_domain_model.md) §3.4 Domain Health Aggregate

## 4. Tasks

### 4.1 Model & service
- [ ] `CircuitBreakerState(scope_type, scope_id, state, reason_code, tripped_at, auto_reset_at, ...)`.
- [ ] State machine: `closed → open → half_open → closed`.
- [ ] `is_open(scope_type, scope_id) → bool` with 10s Redis cache.
- [ ] `trip(scope, reason)` and `reset(scope, by_user)`; both audited.

### 4.2 Thresholds
- [ ] Domain: bounce ≥ 1.5% OR complaint ≥ 0.05% over trailing 24h.
- [ ] IP pool: same thresholds on pool-wide metrics.
- [ ] Sender profile: bounce ≥ 2% OR complaint ≥ 0.05%.
- [ ] Account: bounce ≥ 1% OR complaint ≥ 0.03% (most conservative).

### 4.3 Evaluator
- [ ] Celery Beat task `evaluate_circuit_breakers` every 60 seconds.
- [ ] Reads `rolling_metrics` (Sprint 11).
- [ ] Trips breakers that cross thresholds; transitions tripped-for-24h breakers into `half_open`.

### 4.4 Integration
- [ ] `send_message` consults breaker state for every applicable scope before the suppression check.
- [ ] If any scope is `open`, transition the message to `paused` (new status) and re-queue when the breaker closes.
- [ ] Fail-closed: unknown state or Redis error → treat as `open`.

### 4.5 Alerts
- [ ] On every trip, emit an `AnomalyAlert` entry and a structured log event.
- [ ] Pager-grade alert for `account` scope trips (PagerDuty / Opsgenie wiring).

## 5. Deliverables

- Admin dashboard sees current state for every domain, pool, sender profile, and the account.
- Trips happen autonomously within 60s of a threshold breach; resets require admin action or the auto-reset timer.

## 6. Exit Criteria

- 95%+ coverage on `circuit_breaker/service.py`.
- Integration test: seed metrics that cross thresholds → breaker trips within one evaluator cycle.
- Chaos test: Redis outage during send flow → fail-closed, no messages go out.
- Integration test: manual `reset` is audited and writes `CircuitBreakerReset` event.

## 7. Risks to Watch

- Flapping: trips and resets thrashing under noisy metrics. Require N consecutive evaluations above threshold before tripping.
- Evaluator drift under high load — run it as a dedicated worker, not co-located with send workers.
- Over-tripping the account breaker blocks everything; require a human-signed reason for manual reset.

## 8. Tests to Run

- `pytest tests/unit/core/circuit_breaker/`
- `pytest tests/integration/workers/test_circuit_breaker_evaluator.py`
- `pytest tests/integration/workers/test_send_task_with_open_breaker.py`
