# Sprint 10 — Webhook Receiver & Event Worker

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `backend/sprint-10-event-pipeline`
**Depends on:** Sprints 08, 09

---

## 1. Purpose

Close the loop between sends and outcomes. SES emits delivery, bounce, complaint, open, and click events via SNS. A dedicated webhook service must receive them with sub-second ACK, hand off to a Celery worker, and update suppression plus rolling metrics.

## 2. What Should Be Done

Build `apps/webhook/` (a separate deployment from the API so campaign traffic can't starve it) and `apps/workers/event_tasks.py`. Verify SNS message signatures, normalize events, persist into the typed event tables, update suppression, and update rolling metrics for future circuit-breaker evaluation.

## 3. Docs to Follow

- [../02_system_design.md](../02_system_design.md) — event pipeline section
- [../21_domain_model.md](../21_domain_model.md) §2.4 Event & Reputation, §6 Domain Events
- [../09_data_model.md](../09_data_model.md) — event tables
- [../11_operational_guardrails.md](../11_operational_guardrails.md) — suppression write timing

## 4. Tasks

### 4.1 Webhook receiver
- [ ] `apps/webhook/main.py`: FastAPI app separate from `apps/api`.
- [ ] `apps/webhook/sns_verify.py`: verify SNS signature against the signing cert, validate `SigningCertURL` host, cache the cert.
- [ ] Handle `SubscriptionConfirmation` by fetching the confirmation URL.
- [ ] `apps/webhook/handlers.py`: parse the envelope, enqueue `process_event` on `events.ses.incoming`, return 200 within 200 ms.

### 4.2 Event worker
- [ ] `apps/workers/event_tasks.py::process_event(payload)`.
- [ ] Normalize SES notification types: `Delivery`, `Bounce` (Permanent/Transient + sub-types), `Complaint`, `Open`, `Click`, `Reject`, `Rendering`, `DeliveryDelay`.
- [ ] Insert into the correct event table (`delivery_events`, `bounce_events`, `complaint_events`, `open_events`, `click_events`).
- [ ] Update the originating `Message` status (`sent → delivered | bounced | complained`).
- [ ] Write suppression entries for hard bounces and complaints (Sprint 08 service).
- [ ] Update rolling metrics counters (keys under `metrics:{scope}:{window}`).

### 4.3 Deduplication
- [ ] SES can deliver SNS messages more than once. Dedup by `(ses_message_id, event_type, event_timestamp)` unique index or Redis-backed seen-set with a TTL.

### 4.4 Unsubscribe link handling
- [ ] Public `GET /u/{token}` and `POST /u/{token}` endpoints (on the API, not the webhook) that flip the contact to `unsubscribed` and write a suppression entry.
- [ ] List-Unsubscribe headers added at send time (Sprint 09 adjustment acceptable here).

## 5. Deliverables

- Webhook service accepts real-format SES/SNS payloads and returns 200 in < 200 ms.
- Every event type is persisted and updates the corresponding message + suppression + metrics.

## 6. Exit Criteria

- 95%+ coverage on `apps/webhook/handlers.py` and `event_tasks.py`.
- Integration test: replay a bundle of 1,000 mixed events; correct message status distribution and no duplicates.
- Chaos test: send the same event twice; no duplicate suppression, no double-counting.
- Security test: SNS payload with an invalid signature is rejected with 403.

## 7. Risks to Watch

- Slow webhook stalls the SNS endpoint and triggers retries → amplification. Keep the handler work to verify + enqueue only.
- Cert host spoofing — validate `SigningCertURL` against `sns.*.amazonaws.com` pattern.
- Event ordering: an `Open` event can arrive before `Delivery`. Service logic must tolerate out-of-order.
- Metric double-counting under retries. Dedup must be applied before counting.

## 8. Tests to Run

- `pytest tests/unit/webhook/`
- `pytest tests/integration/webhook/test_sns_verify.py`
- `pytest tests/integration/workers/test_event_tasks.py`
- `pytest tests/e2e/event_ingestion_flow/`
