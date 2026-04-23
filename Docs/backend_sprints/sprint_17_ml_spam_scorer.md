# Sprint 17 — ML: Pre-Send Spam Scorer (Model 1)

**Phase:** ML
**Estimated duration:** 1.5 weeks
**Branch:** `backend/sprint-17-ml-spam-scorer`
**Depends on:** Sprint 09 (send pipeline with Gate 7 stub)

---

## 1. Purpose

Turn Gate 7 from a no-op into a real ML model that rejects content likely to get us blocked. Reject threshold: score > 0.2. This is the first ML component to ship.

## 2. What Should Be Done

Build `libs/ml/spam_scorer.py` with a training + inference pipeline. V1 = heuristic baseline; V2 = scikit-learn logistic regression on TF-IDF features; V3 = XGBoost with engineered features. Ship a feature store, a training pipeline, and an inference wrapper with caching.

## 3. Docs to Follow

- [../12_ml_services.md](../12_ml_services.md) §10.1 Spam Scorer
- [../10_delivery_pipeline.md](../10_delivery_pipeline.md) — Gate 7
- [../16_rollout_plan.md](../16_rollout_plan.md) §14.3 Phase 3

## 4. Tasks

### 4.1 Training data
- [ ] Pipeline that labels historical messages by outcome (delivered + engaged vs. complained + hard-bounced).
- [ ] Feature extractor: subject length, caps ratio, spam keyword hit count, link density, image:text ratio, HTML validity, sender reputation snapshot at send time.
- [ ] Script `scripts/data/extract_spam_features.py` that materializes training data into S3/parquet.

### 4.2 Baseline (V1 — heuristic)
- [ ] Rule-based scorer with hand-tuned weights, deployed on day 1 so Gate 7 is live.
- [ ] Log predictions alongside ground truth for later evaluation.

### 4.3 V2 (sklearn LogReg)
- [ ] Training: TF-IDF + logistic regression; 5-fold CV.
- [ ] Exit bar: AUC > 0.85 on held-out set.
- [ ] Model artifact saved to S3 under a versioned path.

### 4.4 V3 (XGBoost)
- [ ] Engineered features + GBM; calibrated probabilities.
- [ ] Gate promotion only if V3 outperforms V2 on the validation set without regressing latency.

### 4.5 Inference wrapper
- [ ] Load model at worker startup via lifespan hook.
- [ ] `score(payload) → float`; add Redis cache keyed by a hash of normalized content for 30s.
- [ ] p95 latency budget: ≤ 15 ms.

### 4.6 Integration
- [ ] Wire the scorer into `send_message` Gate 7.
- [ ] Messages with `score > 0.2` → transition to `failed` with reason `spam_scorer_reject`.
- [ ] Add an admin override flag on the campaign to log rejections without blocking (shadow mode) for the first week in production.

### 4.7 Monitoring
- [ ] Track score distribution, rejection rate, false-positive rate (manually labeled sample).
- [ ] Trigger SEV-3 alert on sudden drift.

## 5. Deliverables

- Live spam scorer blocking high-risk sends.
- Model registry pattern we can reuse for Models 2–4.

## 6. Exit Criteria

- V2 or V3 deployed with AUC > 0.85 on held-out set.
- Inference p95 ≤ 15 ms.
- Shadow mode telemetry for ≥ 7 days before hard-blocking.
- Documented rollback procedure to previous model version.

## 7. Risks to Watch

- Overfit on historical data that no longer reflects current traffic. Keep rolling evaluation windows.
- Hot-reload bugs on model swap. Use atomic pointer swap with validation before promotion.
- False positives blocking legitimate campaigns. Shadow mode first; monitor rejection rate carefully.

## 8. Tests to Run

- `pytest tests/unit/ml/test_spam_scorer.py`
- `pytest tests/integration/ml/test_scorer_latency.py`
- `pytest tests/integration/workers/test_send_task_gate_7.py`
