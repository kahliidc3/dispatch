# Sprint 11 — Analytics Dashboards

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-11-analytics-dashboards`
**Depends on:** frontend Sprint 10, backend Sprint 11

---

## 1. Purpose

Close Phase 1 with cross-campaign analytics: an account-wide overview, a per-campaign analytics view, and a reputation view that surfaces per-domain health ahead of circuit breakers tripping.

## 2. What Should Be Done

Build `(dashboard)/analytics/` with the overview page, `analytics/reputation/` for the per-domain view, and enrich `campaigns/[id]` with time-series visuals.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.5
- [../15_observability.md](../15_observability.md) §RED metrics
- [../11_operational_guardrails.md](../11_operational_guardrails.md) — thresholds on dashboards

## 4. Tasks

### 4.1 Overview
- [ ] KPI cards: sends today, 7-day trend, bounce rate, complaint rate, open rate, click rate.
- [ ] Top campaigns (last 7 days) with inline sparkline.
- [ ] Top failing domains (by bounce + complaint rate) with breaker status.

### 4.2 Reputation view
- [ ] Per-domain table with: bounce%, complaint%, delivery%, current breaker state, last-warmup-stage.
- [ ] Color-coded thresholds matching backend (warn at 50% of threshold, critical at 100%).
- [ ] Drilldown to domain detail (Sprint 03 page).

### 4.3 Engagement charts
- [ ] Line chart for sends/delivered/bounced over time.
- [ ] Heatmap of open rate by hour × day-of-week (feeds STO work later).

### 4.4 Freshness indicator
- [ ] Every page displays `last_updated_at` (from backend rollup).
- [ ] Warning banner if older than 5 minutes.

## 5. Deliverables

- Complete analytics surface that makes per-domain health visible without SQL access.
- Dashboards are fast (P95 render under 1s after data).

## 6. Exit Criteria

- E2E: overview loads, reputation view reflects seeded data correctly.
- Charts render under a11y-readable alt text or data-table fallback.
- No unbounded `limit` on any table; always keyset pagination.

## 7. Risks to Watch

- Chart libs loading on the server and blowing server bundle. Keep chart components client-only via dynamic import.
- Stale metrics going unnoticed. Make freshness indicator prominent and color-coded.
- Over-fetching by rendering every chart on first paint. Lazy-load below-the-fold charts.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/analytics/**`
- Playwright: `tests/e2e/analytics_overview.spec.ts`, `tests/e2e/reputation_view.spec.ts`
- axe on each analytics page
