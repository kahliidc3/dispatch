# Sprint 03 — Domains & Sender Profiles UI

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-03-domains-ui`
**Depends on:** frontend Sprint 01, backend Sprint 03

---

## 1. Purpose

Give admins the surface to add a sending domain, see the required DNS records, copy them into their DNS provider, trigger verification, and create sender profiles bound to verified domains.

## 2. What Should Be Done

Build `(dashboard)/domains/` with a list view, a detail view, a verify flow, and sender profile CRUD. DNS records must be copyable one-by-one and as a bundle. Unverified domains cannot be used for sender profile creation.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.1
- [../21_domain_model.md](../21_domain_model.md) §2.1, §3.4, §5.4
- [../20_frontend_file_structure.md](../20_frontend_file_structure.md) §`domains/`

## 4. Tasks

### 4.1 Domain list
- [ ] `domains/page.tsx` (Server Component) fetches domains via `src/lib/api/server.ts`.
- [ ] `_components/domains-table.tsx` with status badges: `pending`, `verifying`, `verified`, `cooling`, `burnt`, `retired`.
- [ ] Empty state with primary action "Add domain".

### 4.2 Add domain dialog
- [ ] New-domain form (domain name, choice of manual DNS for MVP).
- [ ] On create → redirect to domain detail.

### 4.3 Domain detail
- [ ] `domains/[domainId]/page.tsx`.
- [ ] `_components/dns-records.tsx` showing SPF, DKIM CNAMEs, DMARC, MAIL FROM CNAME, each with copy-to-clipboard.
- [ ] Per-record status (`pending`, `valid`, `invalid`) with last-checked timestamp.
- [ ] `_components/verify-button.tsx` triggers re-verification; polls while `verifying`.
- [ ] Retire flow using shared confirm dialog.

### 4.4 Sender profiles
- [ ] `(dashboard)/sender-profiles/page.tsx` (list) and `[senderProfileId]/page.tsx` (detail).
- [ ] Create form that only accepts verified domains (server-side check enforced too).
- [ ] Delete flow with confirm.

### 4.5 IP pools (read-only MVP)
- [ ] Display IP pool assignment on sender profile detail; editing is admin-only.

## 5. Deliverables

- Admin can add, verify, and retire domains end-to-end.
- Sender profiles cannot be created against unverified domains (both server and UI rejection).

## 6. Exit Criteria

- E2E: add domain → copy records → stub DNS → verify → create sender profile.
- Accessibility: every copy-to-clipboard control has a visible confirmation and screen-reader announcement.
- Polling stops when a domain moves out of `verifying`.

## 7. Risks to Watch

- Unbounded polling leaking memory. Cancel on unmount; cap total duration.
- Showing DKIM private keys in the UI — only public CNAMEs belong to the user.
- Browser clipboard permissions differing per browser; provide a fallback (manual select).

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/domains/**`
- Playwright: `tests/e2e/domain_verify_flow.spec.ts`
- axe on `/domains` and `/domains/[id]`
