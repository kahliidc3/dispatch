# Sprint 09 — Campaign Authoring & Launch UI

**Phase:** MVP
**Estimated duration:** 1.5 weeks
**Branch:** `frontend/sprint-09-campaign-authoring`
**Depends on:** frontend Sprints 03, 06, 07, 08; backend Sprint 09

---

## 1. Purpose

Deliver the flagship authoring experience: a step-by-step campaign builder that ties sender profile, template version, segment, and scheduling choices into a single, reviewable artifact — then launches it.

## 2. What Should Be Done

Build `(dashboard)/campaigns/create/` as a wizard, a review screen with pre-launch checks, and a confirmation dialog that invokes the backend launch endpoint. Surface backend pre-flight warnings (suppression estimate, circuit breaker state, low-risk spam-score estimate) before launch.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.3 campaigns
- [../10_delivery_pipeline.md](../10_delivery_pipeline.md) — seven gates
- [../21_domain_model.md](../21_domain_model.md) §2.3, §3.2, §5.1

## 4. Tasks

### 4.1 Wizard steps
- [ ] Step 1: details (name, internal tag).
- [ ] Step 2: sender profile selection (only profiles on verified domains).
- [ ] Step 3: template version selection (pick template + pinned version).
- [ ] Step 4: audience (segment or list) with live size preview.
- [ ] Step 5: schedule (immediate or future datetime, timezone-aware).
- [ ] Step 6: review.

### 4.2 Review screen
- [ ] Full rendered-email preview with a sample contact from the audience.
- [ ] Pre-flight checks: suppression exclusion count, breaker state for domain/profile/account, sample spam-score (Gate 7 stub shows 0 in MVP).
- [ ] Block launch if any pre-flight is `critical`; warn but allow for `warnings`.

### 4.3 Launch
- [ ] Confirmation dialog that requires typing the campaign name.
- [ ] On success → redirect to campaign monitoring view (Sprint 10).
- [ ] On failure → show backend error envelope in a retryable toast.

### 4.4 Save draft
- [ ] Draft is persisted after each step via backend campaign draft API.
- [ ] List view shows drafts vs. scheduled vs. running.

## 5. Deliverables

- Non-technical user launches a real campaign in under 5 minutes.
- Pre-launch checks prevent foreseeable deliverability failures.

## 6. Exit Criteria

- E2E: create draft → fill every step → review → launch → monitoring view shows `running`.
- Launch is disabled when the destination domain has an open circuit breaker.
- axe a11y: every wizard step clean.

## 7. Risks to Watch

- Users launching large campaigns without seeing the audience count. Require preview render + exclusion view before enabling the Launch button.
- Race between draft auto-save and step navigation. Queue writes; latest wins.
- Launch double-click → duplicate campaign run. Disable button on submit; idempotent backend call.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/campaigns/create/**`
- Playwright: `tests/e2e/campaign_launch.spec.ts`
- axe on every wizard step + review screen
