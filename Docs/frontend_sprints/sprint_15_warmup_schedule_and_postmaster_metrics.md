# Sprint 15 — Warmup Schedule & Postmaster Metrics

**Phase:** Scale
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-15-warmup-postmaster-ui`
**Depends on:** frontend Sprint 14, backend Sprint 15

---

## 1. Purpose

Make warmup behavior explicit and auditable. Admins see where a domain is in its ramp, can edit the schedule within safe bounds, and get an independent view of reputation from Google Postmaster alongside our own metrics.

## 2. What Should Be Done

Add a "Warmup" tab to domain detail showing the schedule, day-by-day progress, and an editor. Add a "Reputation" tab with Postmaster metrics (spam rate, authentication results, IP reputation if applicable).

## 3. Docs to Follow

- [../11_operational_guardrails.md](../11_operational_guardrails.md) §9
- [../21_domain_model.md](../21_domain_model.md) §5.4 Domain Reputation Lifecycle
- [../15_observability.md](../15_observability.md)

## 4. Tasks

### 4.1 Warmup tab
- [ ] Timeline visual: day N of M, current cap, today's sends, % to cap.
- [ ] Schedule editor (safe presets + custom). Warn loudly on aggressive schedules.
- [ ] "Extend warmup by N days" shortcut.
- [ ] Graduation state + graduation preview.

### 4.2 Postmaster tab
- [ ] Authorization status (OAuth connected or not).
- [ ] Daily metrics: spam rate, domain reputation (high / medium / low / bad), authentication (SPF / DKIM / DMARC pass %).
- [ ] Link out to Google Postmaster for full details.

### 4.3 Warmup on overview
- [ ] On the analytics overview, a widget listing warming domains with their current ramp progress.

### 4.4 Safety
- [ ] Block saving a schedule that would multiply today's cap by > 5x.
- [ ] Show an inline banner if real volume is outpacing the cap.

## 5. Deliverables

- Admins can tune warmup without operator tribal knowledge.
- Postmaster signals are visible next to our own — no context switching.

## 6. Exit Criteria

- E2E: edit schedule → change reflected immediately in UI and applied within a scheduler tick.
- Postmaster disconnected state shows a clear CTA to connect.
- a11y clean on both tabs.

## 7. Risks to Watch

- Schedule editor lets users shoot themselves in the foot. Require explicit confirmation for aggressive jumps.
- Stale Postmaster data presented as current. Always show "as of".
- OAuth connect flow leaving tokens in browser history. Use POST-based callbacks and/or ephemeral state.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/domains/[id]/**`
- Playwright: `tests/e2e/warmup_schedule_edit.spec.ts`
- axe on Warmup + Reputation tabs
