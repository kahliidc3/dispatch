# Sprint 12 — Per-Domain Throttle & Queue Viewer

**Phase:** Scale
**Estimated duration:** 4–6 days
**Branch:** `frontend/sprint-12-throttle-queue-viewer`
**Depends on:** frontend Sprint 11, backend Sprint 12

---

## 1. Purpose

Surface the per-domain throttle and queue state in the UI so operators can see which domains are backing up, which are being throttled, and adjust caps without a deploy.

## 2. What Should Be Done

Extend the domain detail page with a "Throughput" tab and add a platform-wide "Queues" page under `(dashboard)/ops/queues/` showing per-domain queue depth and denial rates.

## 3. Docs to Follow

- [../11_operational_guardrails.md](../11_operational_guardrails.md) §9.2 Rate Limiting
- [../../CLAUDE.md](../../CLAUDE.md) — token bucket and per-domain queue pattern
- [../15_observability.md](../15_observability.md)

## 4. Tasks

### 4.1 Domain throughput tab
- [ ] Add "Throughput" tab on `domains/[id]`.
- [ ] Token-bucket status: tokens available, refill rate, denials per minute.
- [ ] Editable rate limit per hour (admin only); applies within 60s.
- [ ] Recent denial events table.

### 4.2 Ops queues page
- [ ] `(dashboard)/ops/queues/page.tsx` lists active `send.<domain>` queues.
- [ ] Columns: domain, worker count, queue depth, oldest queued age, denials/min.
- [ ] Search + sort.
- [ ] Warning row highlight if queue depth > threshold.

### 4.3 Audit
- [ ] Every rate limit change is audited with actor + old + new values; displayed in the domain's activity feed.

## 5. Deliverables

- On-call operators can diagnose a backup in seconds and adjust caps without shell access.

## 6. Exit Criteria

- E2E: edit rate limit → change reflected in UI and in backend within one polling cycle.
- Queues page handles 100+ queues without UI jank.
- a11y clean on both surfaces.

## 7. Risks to Watch

- Admin misconfiguring a rate limit to 0 by accident. Require confirm for drastic reductions (> 50%).
- High-cardinality queue list becoming a rendering bottleneck. Virtualize the list.
- Stale denial counts. Poll; display `last_updated_at`.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/ops/**`
- Playwright: `tests/e2e/throttle_admin.spec.ts`
