# Sprint 20 — Platform Ops Console

**Phase:** 1M/Day
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-20-platform-ops-console`
**Depends on:** frontend Sprints 12, 13, 16; backend Sprint 20

---

## 1. Purpose

Surface the 1M/day-scale operational controls: partition state, archival job history, backpressure settings, and queue priority tuning — so the on-call engineer can steer the platform through load events without shelling in.

## 2. What Should Be Done

Extend `(dashboard)/ops/` with three new pages: Partitions, Archival, and Backpressure. Tie each to existing ops UI (queues, breakers, pipeline health).

## 3. Docs to Follow

- [../09_data_model.md](../09_data_model.md) §7.3 Partitioning
- [../16_rollout_plan.md](../16_rollout_plan.md) §14.4
- [../04_operations_runbook.md](../04_operations_runbook.md)

## 4. Tasks

### 4.1 Partitions
- [ ] Table per partitioned table (`messages`, event tables): partition name, date range, row count, size on disk, state (`live`, `archived`, `detached`).
- [ ] "Create next month's partition" button (admin, idempotent).
- [ ] Warning banner if the next partition isn't yet created within N days of the boundary.

### 4.2 Archival
- [ ] Archival job history: partition, started-at, duration, rows exported, S3 URI.
- [ ] "Rehydrate" action for a rare query (admin, typed justification).

### 4.3 Backpressure
- [ ] Global send concurrency cap (admin), with warning on drastic reductions.
- [ ] Queue priorities: transactional > campaign > rollups.
- [ ] Status view showing current saturation per tier.

### 4.4 Cross-linking
- [ ] From pipeline health (Sprint 16), deep-link to the relevant ops page on red cards.

## 5. Deliverables

- On-call can prevent and mitigate load events from the UI.
- Archival is visible and reversible (via rehydrate).

## 6. Exit Criteria

- E2E: create next-month partition → appears in list within a polling cycle.
- E2E: lower backpressure cap by 20% → backend applies and UI reflects.
- a11y clean; all destructive actions require typed confirmation.

## 7. Risks to Watch

- Admin lowering concurrency to zero by accident. Guard with confirmation + automatic revert timer option.
- Rehydrate being treated as routine. Surface cost / latency implications in the confirmation dialog.
- UI caching stale partition state during a migration. Force refresh after mutations.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/ops/**`
- Playwright: `tests/e2e/platform_ops_controls.spec.ts`
- axe on new pages
