# Sprint 21 — Security & SOC 2 Review UI

**Phase:** 1M/Day
**Estimated duration:** 1.5 weeks
**Branch:** `frontend/sprint-21-security-soc2-ui`
**Depends on:** frontend Sprint 02, backend Sprint 21

---

## 1. Purpose

Deliver the UI artifacts that make SOC 2 evidence collection routine: an audit-log explorer, an access-review flow, an API key usage overview, and a secret-rotation status board.

## 2. What Should Be Done

Build `(dashboard)/settings/audit/`, `(dashboard)/settings/access-reviews/`, and a security dashboard under `(dashboard)/settings/security/`. Everything read-only for most users; admins drive reviews.

## 3. Docs to Follow

- [../14_security.md](../14_security.md)
- [../08_non_functional_requirements.md](../08_non_functional_requirements.md) §Compliance
- [../04_operations_runbook.md](../04_operations_runbook.md) — incident response

## 4. Tasks

### 4.1 Audit log explorer
- [ ] Searchable, filterable table over `audit_log`.
- [ ] Filters: actor, event type, resource, date range, severity.
- [ ] Export to CSV / JSON (admin only; export itself is audited).
- [ ] Never show raw secrets / PII; confirmed by an automated test.

### 4.2 Access reviews
- [ ] Quarterly review UI: list of users × roles × last login × last action.
- [ ] Mark-reviewed / approve-revoke workflow for each row.
- [ ] Completion report exportable for compliance.

### 4.3 API key usage
- [ ] Board showing every active key, owner, last used, call volume 24h / 7d.
- [ ] Warn on unused keys > N days.
- [ ] Bulk revoke flow (admin).

### 4.4 Secret rotation status
- [ ] Status for every rotatable secret (provider API keys, DB passwords, KMS keys).
- [ ] Next rotation date; overdue badges.

### 4.5 Final a11y + polish pass
- [ ] Whole product a11y sweep with axe across every route.
- [ ] Fix any remaining contrast / focus / ARIA issues before GA.

## 5. Deliverables

- Auditable, reviewable, and compliance-ready product surface.
- Final a11y pass with 0 open axe violations.

## 6. Exit Criteria

- E2E: run a full access review cycle → export completion report.
- Automated test: no audit-log UI response ever contains an unredacted email or secret.
- Platform-wide axe sweep: 0 violations on release-candidate build.
- Compliance sign-off on evidence package.

## 7. Risks to Watch

- Audit-log size hitting the UI. Always use keyset pagination + server-side filters; cap result sizes.
- Approval UX encouraging rubber-stamping. Require an explicit "changes needed" path and log every click.
- Secrets accidentally surfaced in export. Test hard against this.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/settings/audit/**`
- `pnpm test src/app/(dashboard)/settings/access-reviews/**`
- Playwright: `tests/e2e/access_review_cycle.spec.ts`
- Platform-wide a11y run: `tests/e2e/a11y_sweep.spec.ts`
