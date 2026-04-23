# Sprint 19 — Anomaly Alerts & STO Opt-in

**Phase:** ML
**Estimated duration:** 4–6 days
**Branch:** `frontend/sprint-19-anomaly-sto-ui`
**Depends on:** frontend Sprint 16, backend Sprint 19

---

## 1. Purpose

Expose anomaly detection as its own feed (separate from, and earlier than, circuit breaker trips) and give campaign authors a one-toggle way to enable send-time optimization.

## 2. What Should Be Done

Add an `ops/anomalies/page.tsx` feed. Add an STO toggle on the campaign authoring wizard (Sprint 09). Surface STO performance on campaign monitoring.

## 3. Docs to Follow

- [../12_ml_services.md](../12_ml_services.md) §10.3, §10.4
- [../15_observability.md](../15_observability.md)

## 4. Tasks

### 4.1 Anomaly feed
- [ ] Table of anomalies: scope + metric + z-score + detected-at + current state.
- [ ] Drilldown shows time series with EMA baseline overlaid.
- [ ] "Acknowledge" flow with typed note; audited.

### 4.2 STO toggle
- [ ] New step in campaign wizard: "Send-time optimization (optional)".
- [ ] Allowed-hours window picker (timezone-aware).
- [ ] Warn when audience is small and model confidence is low; allow anyway.

### 4.3 STO monitoring
- [ ] On campaign monitoring, a card showing scheduled send distribution by hour.
- [ ] Post-campaign: A/B lift panel comparing STO vs. default.

### 4.4 Integration with observability
- [ ] Anomalies feed links to pipeline health (Sprint 16) and to the scope's detail page.

## 5. Deliverables

- Anomaly feed gives ≥ 5 min advance notice before circuit breakers trip in realistic scenarios.
- STO opt-in adds zero friction for campaigns that want default behavior.

## 6. Exit Criteria

- E2E: seeded anomaly → appears in feed → acknowledge → audited.
- STO on a small-audience campaign shows the confidence warning but proceeds.
- a11y clean on all new surfaces.

## 7. Risks to Watch

- Feed noise. Tune defaults with the backend team; let operators mute per-scope.
- STO delaying urgent sends. Respect the author's allowed-hours window; never delay outside it.
- Confusing "acknowledged" with "resolved." Keep them visually distinct.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/ops/anomalies/**`
- Playwright: `tests/e2e/sto_optin.spec.ts`, `tests/e2e/anomaly_ack.spec.ts`
- axe on new pages
