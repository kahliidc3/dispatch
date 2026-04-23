# Sprint 06 — Template Editor & Versions

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-06-templates-ui`
**Depends on:** frontend Sprint 01, backend Sprint 06

---

## 1. Purpose

Give campaign authors a safe, predictable editor for templates with live preview, strict merge-tag hints, and an immutable version history they can diff and restore from.

## 2. What Should Be Done

Build `(dashboard)/templates/` list and detail. Detail has a split-pane editor / preview with a version switcher. Previewing uses a sample contact payload that the user can edit.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.3 (templates)
- [../21_domain_model.md](../21_domain_model.md) §2.3
- [../20_frontend_file_structure.md](../20_frontend_file_structure.md) §`templates/`

## 4. Tasks

### 4.1 List & create
- [ ] `templates/page.tsx` with a table (name, last updated, active version).
- [ ] Create dialog for a new template.

### 4.2 Editor
- [ ] `templates/[templateId]/page.tsx` Client Component after the server shell.
- [ ] `_components/template-editor.tsx`: subject, plain-text body, HTML body tabs.
- [ ] Merge-tag autocomplete from the backend's allow-listed fields.
- [ ] CRLF-safe subject input; strip/reject newlines.

### 4.3 Preview pane
- [ ] `_components/preview-pane.tsx` renders the rendered HTML iframe with `sandbox="allow-same-origin"` and no external network.
- [ ] Editable sample-contact JSON with a reset button.
- [ ] "Save as new version" creates an immutable version and updates head pointer.

### 4.4 Version history
- [ ] Version list with diff view (text-level for body + subject).
- [ ] "Restore as new version" (never mutates existing versions).

### 4.5 Safety
- [ ] Confirm dialog on navigate-away with unsaved changes.
- [ ] Disable save during an in-flight request.

## 5. Deliverables

- Authors can draft, preview, version, diff, and restore templates.
- Existing versions are never editable (server rejects too).

## 6. Exit Criteria

- E2E: create template → v1 → edit → save v2 → restore v1 as v3 → version list shows 3 entries.
- Preview iframe cannot make outbound network requests (verified via Playwright network intercept).
- axe a11y: 0 violations on editor.

## 7. Risks to Watch

- Rendering user HTML in the same origin without sandbox. Always sandbox the iframe.
- Autocomplete leaking internal-only merge tags. Filter against the backend's explicit allow-list.
- Data loss on accidental refresh. Persist a local draft per template ID (scoped, cleared on save).

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/templates/**`
- Playwright: `tests/e2e/template_versioning.spec.ts`
- Playwright network assertion: preview iframe makes 0 external requests.
