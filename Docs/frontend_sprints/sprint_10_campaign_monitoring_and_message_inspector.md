# Sprint 10 — Campaign Monitoring & Message Inspector

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-10-campaign-monitoring`
**Depends on:** frontend Sprint 09, backend Sprint 10

---

## 1. Purpose

Give operators real-time-enough visibility into a running campaign: funnel counts, send velocity, bounce / complaint rates, and the ability to drill into individual messages and inspect their full event timeline.

## 2. What Should Be Done

Build `(dashboard)/campaigns/[campaignId]/` with header KPIs, a funnel chart, a messages table with keyset pagination, and a message-detail drawer showing the event timeline.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.5
- [../21_domain_model.md](../21_domain_model.md) §2.3, §2.4, §5.2 Message Lifecycle
- [../11_operational_guardrails.md](../11_operational_guardrails.md)

## 4. Tasks

### 4.1 Campaign header
- [ ] Status badge reflecting lifecycle (`draft`, `scheduled`, `running`, `paused`, `completed`, `cancelled`, `failed`).
- [ ] Actions: pause, resume, cancel (each with typed confirm).
- [ ] KPIs: queued / sending / sent / delivered / bounced / complained / opened / clicked.

### 4.2 Funnel & velocity
- [ ] `_components/campaign-metrics.tsx` funnel chart.
- [ ] Velocity sparkline: sends per minute over the last hour.

### 4.3 Messages table
- [ ] Keyset-paginated message list with status badges and last event.
- [ ] Filters: status, has-bounce, has-click, has-complaint.
- [ ] Bulk action: re-queue `failed` messages (idempotent).

### 4.4 Message inspector drawer
- [ ] Tabs: Overview (contact, sender profile, SES ID), Rendered email, Event timeline.
- [ ] Timeline shows every `DeliveryEvent`/`BounceEvent`/`ComplaintEvent`/etc. in chronological order with source data (redacted PII).

### 4.5 Polling
- [ ] Metrics polled every 15–30s while campaign is `running`.
- [ ] Stop polling when campaign completes.

## 5. Deliverables

- Operator can monitor a running campaign, intervene (pause/cancel), and diagnose individual-message failures without shell access.

## 6. Exit Criteria

- E2E: launch campaign → monitor shows `running` → backend completion → UI transitions to `completed` without reload.
- Pause / resume / cancel all produce expected backend state and audit entries.
- Inspector drawer renders the rendered email safely (sandboxed iframe).

## 7. Risks to Watch

- Polling storm with multiple tabs open. Use visibilitychange API to pause polling on hidden tabs.
- Showing raw SES bounce payloads with PII. Redact before render.
- Re-queuing already-sent messages. The action must be gated by `status='failed'` in the UI (server is authoritative).

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/campaigns/[campaignId]/**`
- Playwright: `tests/e2e/campaign_monitor.spec.ts`
- Visual regression on the metrics header + funnel
