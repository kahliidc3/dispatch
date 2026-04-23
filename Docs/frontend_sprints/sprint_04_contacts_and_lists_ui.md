# Sprint 04 — Contacts & Lists UI

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-04-contacts-ui`
**Depends on:** frontend Sprint 01, backend Sprint 04

---

## 1. Purpose

Deliver the audience-facing UI: browse contacts, view details and event history, manage list memberships, and handle unsubscribe overrides — all respecting the contact lifecycle state machine.

## 2. What Should Be Done

Build `(dashboard)/contacts/` list and detail pages, list CRUD under `(dashboard)/lists/`, and the public unsubscribe page under `(auth)` (or a standalone route group) that works without authentication.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.2
- [../21_domain_model.md](../21_domain_model.md) §2.2, §3.1, §5.3
- [../20_frontend_file_structure.md](../20_frontend_file_structure.md) §`contacts/`

## 4. Tasks

### 4.1 Contact list
- [ ] `contacts/page.tsx` with paginated, filterable table.
- [ ] Filters: lifecycle status, list membership, source, suppressed-yes/no.
- [ ] Bulk actions: add-to-list, remove-from-list, unsubscribe (with confirm + audit reason).

### 4.2 Contact detail drawer
- [ ] `_components/contact-drawer.tsx` with tabs: Overview, Lists, Preferences, Event history.
- [ ] Lifecycle badge strictly reflects backend state; transitions drive UI, never the other way.
- [ ] GDPR-compliant hard-delete behind admin gate + confirm dialog.

### 4.3 Lists
- [ ] `(dashboard)/lists/page.tsx` and `[listId]/page.tsx`.
- [ ] Add/remove members, see total counts, recent adds.

### 4.4 Public unsubscribe page
- [ ] A route outside `(dashboard)` that accepts `?t=<token>`.
- [ ] Confirms token server-side, offers "Yes, unsubscribe" and optional preference downgrade.
- [ ] No auth required; explicit noindex.

### 4.5 Single-contact add
- [ ] `contacts/new/page.tsx` simple form — bulk is Sprint 05.

## 5. Deliverables

- Operators can triage contacts, change list memberships, and honor manual unsubscribe requests.
- Public unsubscribe works end-to-end with a signed token.

## 6. Exit Criteria

- E2E: unsubscribe via token → contact lifecycle flips → suppression entry written.
- UI prevents setting a suppressed contact back to `active` (server rejects too; UI hides the action).
- a11y: drawer is reachable and dismissible via keyboard.

## 7. Risks to Watch

- Stale lifecycle badges after an optimistic action — prefer revalidation to optimistic writes for lifecycle changes.
- Forged tokens on the public page; never display anything sensitive pre-confirmation.
- Email PII in telemetry. Redact everywhere.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/contacts/**`
- Playwright: `tests/e2e/contact_lifecycle.spec.ts`, `tests/e2e/public_unsubscribe.spec.ts`
- axe on `/contacts`, `/contacts/[id]`, public unsubscribe route
