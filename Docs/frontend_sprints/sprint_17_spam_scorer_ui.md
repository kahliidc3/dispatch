# Sprint 17 — Spam Scorer UI: Shadow Mode & Rejection Review

**Phase:** ML
**Estimated duration:** 4–6 days
**Branch:** `frontend/sprint-17-spam-scorer-ui`
**Depends on:** frontend Sprint 09, backend Sprint 17

---

## 1. Purpose

Make the spam scorer observable and controllable. Operators can see which messages would be rejected (shadow mode), review true/false positives, and flip individual campaigns or the whole platform into hard-block mode.

## 2. What Should Be Done

Add a "Spam score" surface to campaign review + monitoring, a global Model Ops page showing live score distribution and rejection rate, and an admin toggle for shadow vs. block mode per campaign.

## 3. Docs to Follow

- [../12_ml_services.md](../12_ml_services.md) §10.1
- [../10_delivery_pipeline.md](../10_delivery_pipeline.md) — Gate 7
- [../21_domain_model.md](../21_domain_model.md) §2.3 Campaign Management

## 4. Tasks

### 4.1 Campaign integration
- [ ] On the campaign review screen (Sprint 09), show predicted score + rejection likelihood over the audience.
- [ ] Per-campaign toggle: `shadow`, `block`, `disabled` (admin only).

### 4.2 Rejection review
- [ ] On campaign monitoring (Sprint 10), new tab "Rejections (Gate 7)" listing messages rejected by the scorer.
- [ ] Drill-in shows features that contributed to the score.
- [ ] "Mark as false positive" flags the sample for model retraining data.

### 4.3 Model Ops page
- [ ] `(dashboard)/ops/models/page.tsx` shows active model version, AUC, rejection rate over time, score distribution histogram.
- [ ] Rollback button (admin) to revert to previous version with typed justification.

### 4.4 Alerts
- [ ] Surface SEV-3 drift alerts from Sprint 16 on this page.

## 5. Deliverables

- Operators can run the scorer in shadow mode for 7+ days with full visibility before enabling hard-block.
- False-positive samples loop back into the training dataset.

## 6. Exit Criteria

- E2E: toggle campaign to shadow → messages that would have been blocked show in the Rejections tab but still send.
- Rollback button requires justification and is audited.
- a11y clean on Model Ops page.

## 7. Risks to Watch

- Confusing shadow and block modes. Always display the active mode in the campaign header.
- Exposing raw feature vectors with PII. Redact before display.
- Operators rolling back a model reactively. Require a cooldown before another rollback.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/ops/models/**`
- Playwright: `tests/e2e/spam_scorer_shadow.spec.ts`
- axe on Model Ops
