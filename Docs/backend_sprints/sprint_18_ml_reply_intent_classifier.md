# Sprint 18 — ML: Reply Intent Classifier (Model 2)

**Phase:** ML
**Estimated duration:** 1.5 weeks
**Branch:** `backend/sprint-18-ml-reply-intent`
**Depends on:** Sprint 17 (ML infrastructure patterns)

---

## 1. Purpose

Automatically classify incoming replies into actionable intent buckets. This is what turns one-way broadcast into a feedback loop: unsubscribe requests, out-of-office, complaints, and leads are routed without a human in the loop.

## 2. What Should Be Done

Build `libs/ml/reply_intent.py` with two model tiers: V1 TF-IDF + LinearSVC for a fast seed model, V2 DistilBERT fine-tuned once we have enough labeled data. Define seven intent classes and the actions each triggers.

## 3. Docs to Follow

- [../12_ml_services.md](../12_ml_services.md) §10.2 Reply Intent Classifier
- [../02_system_design.md](../02_system_design.md) — event pipeline (reply events)
- [../21_domain_model.md](../21_domain_model.md) §2.4 Event & Reputation (`ReplyEvent`)

## 4. Tasks

### 4.1 Intent taxonomy (seven classes)
- [ ] `positive_interest`, `question`, `objection`, `out_of_office`, `unsubscribe_request`, `complaint`, `auto_reply_other`.
- [ ] Each intent has a typed `ReplyAction` (e.g., `unsubscribe_request → unsubscribe + suppress`).

### 4.2 Data & labeling
- [ ] Ingest reply emails via SES inbound → S3 → event worker → `reply_events` table.
- [ ] Seed labeling: 500–1,000 hand-labeled replies across the seven classes.
- [ ] Active-learning loop to grow the labeled set over time.

### 4.3 V1 (TF-IDF + LinearSVC)
- [ ] Preprocessing: strip quoted reply chains, normalize whitespace, lowercase.
- [ ] Train + calibrate; confidence threshold below which we do nothing.
- [ ] Deploy as first production classifier.

### 4.4 V2 (DistilBERT)
- [ ] Fine-tune distilbert-base-uncased on accumulated labels.
- [ ] CPU inference acceptable (batch size 1, ≤ 100 ms p95).
- [ ] Promote only if macro-F1 beats V1 by ≥ 5 points.

### 4.5 Actions
- [ ] `unsubscribe_request` → write suppression entry + mark contact `unsubscribed`.
- [ ] `complaint` → suppression entry + circuit-breaker signal (not direct trip).
- [ ] `out_of_office` → store and ignore for campaign engagement.
- [ ] `positive_interest` / `question` / `objection` → notify assigned user (webhook or UI inbox).
- [ ] `auto_reply_other` → log and drop.

### 4.6 Safety rails
- [ ] Low-confidence replies queued for human review, not auto-actioned.
- [ ] Every auto-action audited with model version + confidence.

## 5. Deliverables

- Every reply lands in the system, gets classified, and triggers the right action (or a human review ticket when low-confidence).
- Unsubscribe-via-reply takes effect within 60 seconds.

## 6. Exit Criteria

- V2 macro-F1 ≥ 0.80 on held-out set, with ≥ 0.90 on `unsubscribe_request` and `complaint`.
- No action taken on a confidence below the class-specific threshold.
- Shadow-mode period of 7 days before enabling auto-unsubscribe from replies.

## 7. Risks to Watch

- Classifying a question ("remove this from the campaign?") as an unsubscribe. Be conservative on auto-unsubscribe; require high confidence or keyword confirmation.
- Adversarial inputs (huge replies, attachments). Enforce size limits upstream.
- Latency under DistilBERT. Warm model on worker startup; benchmark.

## 8. Tests to Run

- `pytest tests/unit/ml/test_reply_intent_preprocess.py`
- `pytest tests/integration/ml/test_reply_intent_inference.py`
- `pytest tests/integration/workers/test_reply_action_router.py`
