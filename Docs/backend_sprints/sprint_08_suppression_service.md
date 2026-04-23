# Sprint 08 — Suppression Service

**Phase:** MVP
**Estimated duration:** 4–6 days
**Branch:** `backend/sprint-08-suppression`
**Depends on:** Sprint 04

---

## 1. Purpose

Deliver the platform-wide suppression list — the single source of truth that stops emails going to addresses we must never contact again. Suppression is written at two points (segment eval + send time) and synced to SES account-level suppression.

## 2. What Should Be Done

Build `libs/core/suppression/` with strict `(email)` uniqueness, a typed reason taxonomy, and a sync service that pushes suppression entries to SES's account-level suppression list. Provide admin endpoints for manual add and (rare, audited) remove.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.4 Suppression & Compliance
- [../21_domain_model.md](../21_domain_model.md) §3.3 Suppression Aggregate
- [../09_data_model.md](../09_data_model.md) — `suppression_entries` (UNIQUE(email))
- [../11_operational_guardrails.md](../11_operational_guardrails.md)

## 4. Tasks

### 4.1 Core service
- [ ] Model `SuppressionEntry(email, reason_code, source, first_suppressed_at, expires_at_nullable)`.
- [ ] Reason taxonomy: `hard_bounce`, `complaint`, `unsubscribe`, `manual`, `spam_trap`, `role_account`, `global_suppression_sync`.
- [ ] `is_suppressed(email) → bool`, backed by a short-TTL Redis cache.

### 4.2 Write paths
- [ ] Called by the event worker (bounce / complaint / unsubscribe) — Sprint 10.
- [ ] Called by admin API: `POST /suppression`, `DELETE /suppression/{email}` (admin + reason required + audit).
- [ ] Called by segment snapshot filter — Sprint 07.
- [ ] Called by send-time gate 4 — Sprint 09.

### 4.3 SES account suppression sync
- [ ] Bidirectional sync with SES's account-level suppression list via `PutSuppressedDestination` / `GetSuppressedDestination`.
- [ ] Scheduled Celery task that reconciles entries (new in platform → push to SES; new in SES → pull to platform).
- [ ] Rate-limited sync to avoid SES API throttling.

### 4.4 API
- [ ] `GET /suppression` (paginated, filter by reason).
- [ ] `GET /suppression/{email}` → returns reason + first seen.
- [ ] `POST /suppression/bulk-import` (admin, CSV).

## 5. Deliverables

- Every send path consults suppression before delivery.
- Suppression list in platform DB and SES account suppression stay consistent within 5 minutes.

## 6. Exit Criteria

- 95%+ coverage on `suppression/service.py`.
- Integration test: `is_suppressed()` returns true within 100 ms of an `UnsubscribeEvent` being written.
- Integration test: removing a suppression entry is audited and rate-limited.
- End-to-end test: an email on the suppression list never produces a `SendEmail` call to the SES stub.

## 7. Risks to Watch

- Cache staleness → sending to a newly suppressed address. Keep TTL ≤ 60s and invalidate on write.
- Unbounded manual removal. Require admin role + justification string + audit log; alert on ≥ N removals/day.
- SES sync drift. Reconcile nightly with a full diff, not just incrementally.

## 8. Tests to Run

- `pytest tests/unit/core/suppression/`
- `pytest tests/integration/core/suppression/test_ses_sync.py`
- `pytest tests/integration/api/test_suppression_router.py`
