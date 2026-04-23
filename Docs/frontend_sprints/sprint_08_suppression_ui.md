# Sprint 08 — Suppression UI

**Phase:** MVP
**Estimated duration:** 3–5 days
**Branch:** `frontend/sprint-08-suppression-ui`
**Depends on:** frontend Sprint 04, backend Sprint 08

---

## 1. Purpose

Give operators a dedicated surface for the platform-wide suppression list: browsing, filtering by reason, bulk-adding, and (rare, audited) removing.

## 2. What Should Be Done

Build `(dashboard)/suppression/` with a reason-aware table, bulk import, and a guarded removal flow that requires a justification string.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.4
- [../21_domain_model.md](../21_domain_model.md) §3.3
- [../14_security.md](../14_security.md) — audit + compliance

## 4. Tasks

### 4.1 List
- [ ] `suppression/page.tsx` paginated table with columns: email (masked), reason, source, first-seen.
- [ ] Filters: reason, source, date range.

### 4.2 Add
- [ ] Single-add dialog (email + reason picker + optional note).
- [ ] Bulk add via CSV (reuses wizard primitives from Sprint 05).

### 4.3 Remove
- [ ] Removal requires admin role + typed justification + confirm dialog.
- [ ] After remove, show a success toast linking to the audit entry.

### 4.4 Email masking
- [ ] Masked display by default (`jo****@example.com`); admin can reveal with a click that emits an audit event server-side.

### 4.5 SES sync indicator
- [ ] Read-only panel showing last SES sync timestamp and drift count (read from backend).

## 5. Deliverables

- Full lifecycle UX for suppression entries under strict audit.
- Bulk import and export work end-to-end.

## 6. Exit Criteria

- E2E: add → appears in list → remove (admin only) → audit entry visible in Settings.
- Non-admins cannot see or trigger the remove action.
- Email masking passes a visual snapshot test.

## 7. Risks to Watch

- Exposing unmasked emails to non-admins. Enforce masking server-side and in the UI.
- Allowing silent bulk removal. Cap batch removes and alert on large batches.
- Accidental CSV double-imports. Dedup client-side before submission.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/suppression/**`
- Playwright: `tests/e2e/suppression_flow.spec.ts`
- axe on suppression pages
