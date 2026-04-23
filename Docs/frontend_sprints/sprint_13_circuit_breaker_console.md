# Sprint 13 — Circuit Breaker Console

**Phase:** Scale
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-13-circuit-breakers-ui`
**Depends on:** frontend Sprint 12, backend Sprint 13

---

## 1. Purpose

Make circuit breakers legible. Operators need to see every open breaker across all four scopes at a glance, understand *why* it tripped, and reset it with full audit when safe.

## 2. What Should Be Done

Build `(dashboard)/ops/circuit-breakers/page.tsx` with a four-scope matrix, timeline of trips and resets, and a reset flow that requires a typed justification.

## 3. Docs to Follow

- [../11_operational_guardrails.md](../11_operational_guardrails.md) §9.1 thresholds table
- [../21_domain_model.md](../21_domain_model.md) §3.4 Domain Health Aggregate
- [../04_operations_runbook.md](../04_operations_runbook.md) — response procedures

## 4. Tasks

### 4.1 Scope matrix
- [ ] Grid view grouping by scope type: domain, IP pool, sender profile, account.
- [ ] Row per entity with state, tripped-at, reason, auto-reset-at.
- [ ] Quick-filter: only-open, last-24h, by reason code.

### 4.2 Badges on feature pages
- [ ] Reusable `<CircuitBreakerBadge scope=... id=... />` component.
- [ ] Drop it on domain detail, sender profile detail, and campaign monitoring.

### 4.3 Trip timeline
- [ ] Per-entity activity feed of trips / resets / auto-resets with actor and reason.

### 4.4 Reset flow
- [ ] Admin-only action.
- [ ] Requires typed justification and a linked runbook page (from [../04_operations_runbook.md](../04_operations_runbook.md)).
- [ ] Extra confirm when resetting the `account` scope (which blocks all sends).

### 4.5 Alerts integration
- [ ] Link from an active alert (from observability) directly into the relevant breaker row.

## 5. Deliverables

- One screen to answer "what's broken right now and what do I do."
- Every reset is audited with who / why / when.

## 6. Exit Criteria

- E2E: seed open breaker → appears in matrix → reset with justification → audit entry visible.
- Account-scope reset requires two confirmations.
- Badge component reused on at least 3 existing pages with no regressions.

## 7. Risks to Watch

- Tempting to add a "reset all" button. Do not. Every reset must be scoped + justified.
- Stale view during an active incident. Poll aggressively (5–10s) on this page.
- Color-only state encoding. Always pair with text + icon for color-blind users.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/ops/circuit-breakers/**`
- Playwright: `tests/e2e/circuit_breaker_reset.spec.ts`
- axe on breaker console
