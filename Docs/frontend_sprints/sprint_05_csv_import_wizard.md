# Sprint 05 — CSV Import Wizard

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-05-csv-import`
**Depends on:** frontend Sprint 04, backend Sprint 05

---

## 1. Purpose

Turn the backend's import pipeline into a first-class admin experience. Operators upload, map columns, launch, watch progress, and drill into rejected rows — without leaving the app.

## 2. What Should Be Done

Build a multi-step wizard under `(dashboard)/contacts/import/`: upload → column mapping preview → submit → progress → error review.

## 3. Docs to Follow

- [../10_delivery_pipeline.md](../10_delivery_pipeline.md) §Seven-Gate Validation (gates 1–3)
- [../07_functional_requirements.md](../07_functional_requirements.md) §5.2 import
- [../20_frontend_file_structure.md](../20_frontend_file_structure.md) §`contacts/import/`

## 4. Tasks

### 4.1 Upload step
- [ ] Drag-and-drop uploader with file-size cap (matches backend).
- [ ] CSV sample header preview before upload.

### 4.2 Column mapping
- [ ] Auto-detect standard columns (`email`, `first_name`, `last_name`).
- [ ] Let user map arbitrary CSV columns to contact preferences.
- [ ] Save mapping templates per user for reuse.

### 4.3 Submit & progress
- [ ] On submit → create import job, navigate to progress page.
- [ ] Live counters: total / accepted / rejected / duplicates; updated via polling (no WebSockets in MVP).
- [ ] Completion state surfaces summary and link to errors.

### 4.4 Error review
- [ ] Paginated view of rejection rows with typed reasons: `format`, `invalid_mx`, `role_account`.
- [ ] CSV export of rejected rows for fixing upstream.

### 4.5 Safety
- [ ] Block navigation away mid-upload with a confirm.
- [ ] Cap concurrent jobs per user in UI (matches backend).

## 5. Deliverables

- Operator can import 100K contacts end-to-end with visible progress and actionable errors.

## 6. Exit Criteria

- E2E: upload fixture CSV with known bad rows → counts match backend's expected output.
- Import template re-run produces 0 duplicates.
- a11y: every wizard step is keyboard-navigable and announces step changes.

## 7. Risks to Watch

- Browser upload of very large CSVs crashing the tab. Stream upload via `FormData` + limit client-side with a clear error.
- PII leakage in error UI (showing entire bad rows). Truncate / redact email local-parts beyond preview.
- Polling storm if a user keeps the tab open. Back off polling interval exponentially.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/contacts/import/**`
- Playwright: `tests/e2e/csv_import_wizard.spec.ts`
- axe on every wizard step
