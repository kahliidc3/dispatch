# Sprint 09 — SES Client & Send Pipeline (Gates 4–7)

**Phase:** MVP
**Estimated duration:** 1.5 weeks
**Branch:** `backend/sprint-09-send-pipeline`
**Depends on:** Sprints 03, 06, 07, 08

---

## 1. Purpose

Deliver the heart of the platform: the idempotent send task that pulls a message, applies the remaining four pre-send gates, calls SES, and transitions the message through its lifecycle. MVP uses a single queue — per-domain queues arrive in Sprint 12.

## 2. What Should Be Done

Implement `libs/ses_client/`, `libs/core/campaigns/` (messaging side), and `apps/workers/send_tasks.py`. The send task accepts a `message_id`, reloads the entity, runs gates 4–7, calls SES, and updates status in one transaction.

## 3. Docs to Follow

- [../10_delivery_pipeline.md](../10_delivery_pipeline.md) — `send_email()` pseudocode and seven gates
- [../21_domain_model.md](../21_domain_model.md) §3.2 Campaign Aggregate, §5.2 Message Lifecycle
- [../09_data_model.md](../09_data_model.md) — `campaigns`, `campaign_runs`, `send_batches`, `messages`
- [../17_fastapi_documentation.md](../17_fastapi_documentation.md) §9 dispatch-Specific Conventions (idempotency)
- [../../CLAUDE.md](../../CLAUDE.md) — "Idempotent send tasks" and "Status transitions are one-way"

## 4. Tasks

### 4.1 SES client wrapper
- [ ] `libs/ses_client/client.py`: thin async wrapper around `SendEmail` / `SendRawEmail` (boto3 via aioboto3 or sync-in-threadpool).
- [ ] Typed responses; map SES error codes to `libs/ses_client/errors.py` domain errors.
- [ ] `libs/ses_client/retries.py`: exponential backoff only for transient errors; never retry `MessageRejected`.
- [ ] `libs/ses_client/metrics.py`: count / latency / error-class metrics.

### 4.2 Campaigns (send side)
- [ ] Services for `Campaign`, `CampaignRun`, `SendBatch`, `Message`.
- [ ] Campaign launch endpoint `POST /campaigns/{id}/launch` which:
      1. Creates a `CampaignRun`.
      2. Calls the snapshot freeze service (Sprint 07).
      3. Splits the snapshot into `SendBatch` chunks.
      4. Creates `Message` rows in `status='queued'`.
      5. Enqueues `send_message` tasks.
- [ ] `POST /campaigns/{id}/pause`, `POST /campaigns/{id}/resume`, `POST /campaigns/{id}/cancel`.

### 4.3 Send task (idempotent)
- [ ] `apps/workers/send_tasks.py::send_message(message_id)`.
- [ ] Reload message; return immediately if `status != 'queued'`.
- [ ] Transition `queued → sending` (DB guard: `UPDATE ... WHERE status='queued'`).
- [ ] Apply gates 4–7:
      - **Gate 4:** platform suppression check (Sprint 08).
      - **Gate 5:** SES account-level suppression check.
      - **Gate 6:** spam trap heuristic (seed-domain match + high-risk pattern).
      - **Gate 7:** ML spam scorer — stubbed in MVP as a no-op that always passes; real scorer in Sprint 17.
- [ ] Render template version against contact data.
- [ ] Call SES; on success transition to `sent` with `ses_message_id`; on terminal error transition to `failed` with reason; on retryable error re-raise.
- [ ] `task_acks_late=True`, `worker_prefetch_multiplier=1`.

### 4.4 Status machine
- [ ] Enforce `queued → sending → sent | failed` at DB level (CHECK constraint or trigger) and service level.
- [ ] `delivered | bounced | complained` transitions happen in Sprint 10 from the event worker.

## 5. Deliverables

- `POST /campaigns/{id}/launch` runs end-to-end against a faked SES and produces `sent` messages.
- Every send call is idempotent: re-running `send_message(id)` twice results in exactly one SES call.

## 6. Exit Criteria

- 95%+ coverage on `campaigns/service.py` and `ses_client/client.py`.
- End-to-end test: launch a 1,000-message campaign → 1,000 `sent` messages → 0 duplicates.
- Chaos test: kill the worker mid-send; restart; no duplicate SES calls; no stuck `sending` rows (idempotent re-drive).
- Every message has non-null `domain_id` and `sender_profile_id` (invariant).

## 7. Risks to Watch

- Duplicate sends from non-idempotent retry. The only safe pattern: check `status='queued'` inside a transactional update.
- Long-running rendering blocking the event loop. Keep rendering CPU-bound work off the async path or use thread pool.
- SES throttling — back off on `Throttling` errors; do not consume them silently.
- Partial launch: crash between snapshot and enqueue. Use a single transaction for row creation; enqueuing is idempotent on re-run.

## 8. Tests to Run

- `pytest tests/unit/ses_client/`
- `pytest tests/unit/core/campaigns/`
- `pytest tests/integration/workers/test_send_tasks.py`
- `pytest tests/integration/workers/test_send_tasks_idempotency.py`
- `pytest tests/e2e/campaign_launch_flow/`
