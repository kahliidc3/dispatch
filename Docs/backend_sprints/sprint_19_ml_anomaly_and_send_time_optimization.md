# Sprint 19 — ML: Anomaly Detection & Send-Time Optimization

**Phase:** ML
**Estimated duration:** 1 week
**Branch:** `backend/sprint-19-ml-anomaly-sto`
**Depends on:** Sprints 11 (analytics), 13 (circuit breakers), 17–18 (ML infra)

---

## 1. Purpose

Close the ML phase with two lower-stakes but high-value models: anomaly detection over the rolling metrics stream (early warning, complements circuit breakers) and per-contact send-time optimization (STO).

## 2. What Should Be Done

Build `libs/ml/anomaly.py` (EMA + 3σ detector on every scope's rolling metrics) and `libs/ml/send_time_optimization.py` (gradient-boosted model that predicts the optimal send hour per contact).

## 3. Docs to Follow

- [../12_ml_services.md](../12_ml_services.md) §10.3 Anomaly Detection, §10.4 Send-Time Optimization
- [../11_operational_guardrails.md](../11_operational_guardrails.md)
- [../15_observability.md](../15_observability.md) — alert wiring for anomalies

## 4. Tasks

### 4.1 Anomaly detection
- [ ] EMA baseline per (scope_type, scope_id, metric, hour_of_day).
- [ ] Flag a sample when |actual - EMA| > 3σ for N consecutive windows.
- [ ] Write `AnomalyAlert` and emit a SEV-3 alert (SEV-2 for account scope).
- [ ] Backfill-safe: when a breaker trips, pause anomaly learning for that scope so the model doesn't learn the outage.

### 4.2 Send-time optimization
- [ ] Feature store per contact: historical open times, timezone guess from domain, day-of-week patterns.
- [ ] Gradient-boosted regressor predicting `p(open | send_hour)`.
- [ ] `pick_send_hour(contact_id, allowed_window) → hour` service used by the scheduler.
- [ ] Optional at the campaign level (opt-in flag per campaign).

### 4.3 Integration
- [ ] Campaign scheduler respects STO when enabled; messages are batched by target hour within the campaign's allowed send window.
- [ ] Fall back to a default hour when we have < N data points for the contact.

### 4.4 Evaluation
- [ ] A/B test framework: random 50/50 split between STO and default scheduling.
- [ ] Success metric: open-rate lift with statistical significance.

## 5. Deliverables

- Anomaly alerts firing before circuit breakers trip in realistic scenarios.
- Campaign can opt into STO and see measurable lift over default scheduling.

## 6. Exit Criteria

- Backtest: anomaly detector catches ≥ 80% of historical SEV-2 incidents at least 5 minutes before the circuit breaker tripped.
- STO A/B test shows ≥ 5% relative open-rate lift with p < 0.05.
- No regression in send throughput with STO enabled.

## 7. Risks to Watch

- Anomaly false positives drowning the pager. Require multi-window confirmation; tune thresholds per scope.
- STO batching creating uneven worker load. Schedule pre-computation offline so workers just pull.
- Cold-start contacts: fall back gracefully, do not delay those sends.

## 8. Tests to Run

- `pytest tests/unit/ml/test_anomaly.py`
- `pytest tests/unit/ml/test_send_time_optimization.py`
- `pytest tests/integration/ml/test_sto_scheduler.py`
