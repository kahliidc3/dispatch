# Sprint 16 — Observability Surfaces

**Phase:** Scale
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-16-observability-ui`
**Depends on:** frontend Sprints 11, 13; backend Sprint 16

---

## 1. Purpose

Close the loop between alerts and the UI. Operators should land on the right page from a page/alert link, see pipeline health at a glance, and deep-link to traces or metrics dashboards when they need to go deeper.

## 2. What Should Be Done

Add `(dashboard)/ops/pipeline/page.tsx` showing queues, workers, DB, Redis, and webhook backlog health. Add an alerts feed with active/resolved state. Add deep links from messages and campaigns to the external trace backend.

## 3. Docs to Follow

- [../15_observability.md](../15_observability.md) — full spec
- [../04_operations_runbook.md](../04_operations_runbook.md) — alert → action mapping

## 4. Tasks

### 4.1 Pipeline health
- [ ] Cards: API P95, webhook P95, webhook backlog, DB CPU, Redis memory, worker heartbeat age, analytics rollup lag.
- [ ] Color-coded against SEV thresholds from [../15_observability.md](../15_observability.md).

### 4.2 Alerts feed
- [ ] Active alerts list with severity badge, first-fired-at, last-seen, runbook link.
- [ ] Resolved history (last 7 days).

### 4.3 Deep links
- [ ] From message inspector: "Open trace" → external trace backend for `trace_id`.
- [ ] From campaign run: "Open metrics dashboard" → external metrics backend for the `campaign_run_id`.

### 4.4 Webhook status banner
- [ ] Global banner when webhook backlog exceeds threshold, with a link to the ops page.

## 5. Deliverables

- A single page tells operators whether the pipeline is healthy.
- Alert → runbook → action flow works with zero context-switching.

## 6. Exit Criteria

- E2E: simulate webhook backlog → banner appears, ops page shows red card.
- Every active alert shows a runbook link that loads the right section of [../04_operations_runbook.md](../04_operations_runbook.md) (or a rendered version).
- Deep links pass `trace_id` / `campaign_run_id` correctly.

## 7. Risks to Watch

- Banner fatigue. Snooze affordances per-operator.
- Deep-link URL changes breaking silently. Centralize external URL construction in `src/lib/observability.ts`.
- Alert feed becoming a noisy timeline. Default filter to active-only.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/ops/**`
- Playwright: `tests/e2e/pipeline_health.spec.ts`
- axe on ops surfaces
