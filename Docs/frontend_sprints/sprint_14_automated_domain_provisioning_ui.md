# Sprint 14 — Automated Domain Provisioning UI

**Phase:** Scale
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-14-domain-provisioning-ui`
**Depends on:** frontend Sprint 03, backend Sprint 14

---

## 1. Purpose

Turn the automated provisioning backend flow into a guided, low-friction UX. Admin picks a provider, authorizes, clicks "Provision," and watches steps complete — or recovers from a typed failure.

## 2. What Should Be Done

Rework the "Add domain" flow to offer "Manual" (existing MVP flow) or "Automated" (new). On automated, walk through provider selection, authorization, zone selection, and live step status. Expose an "ops" page that audits provisioning attempts.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.1
- [../14_security.md](../14_security.md) — OAuth/API key storage on the server only
- [../18_nextjs_documentation.md](../18_nextjs_documentation.md) §8 Auth (never expose secrets)

## 4. Tasks

### 4.1 Provider picker
- [ ] Step in the add-domain flow: Manual vs. Cloudflare vs. Route 53.
- [ ] Persist provider choice with the domain record.

### 4.2 Authorization
- [ ] Cloudflare: redirect to backend OAuth/API-token setup.
- [ ] Route 53: ensure the backend IAM role is assumable; show green check if so.
- [ ] Never store provider secrets client-side.

### 4.3 Zone / hosted zone selection
- [ ] Fetch zones from the backend (server-side proxies provider API).
- [ ] Let the admin pick which zone owns the domain.

### 4.4 Provision & watch
- [ ] Trigger provisioning; navigate to step-log view.
- [ ] Live step status: Create SES identity → Fetch DKIM → Write DNS → Verify SES → Verify DKIM → Done.
- [ ] Each step shows elapsed time, result, and an expand for error details.

### 4.5 Failure recovery
- [ ] On `provisioning_failed`, surface a typed reason + suggested remediation.
- [ ] "Retry" button re-enqueues idempotently.
- [ ] "Abandon" deletes the domain record and rolls back via backend.

## 5. Deliverables

- New domain onboarding measured in minutes rather than hours, with no manual DNS edits.

## 6. Exit Criteria

- E2E (with recorded backend fixtures): Cloudflare and Route 53 happy paths complete end-to-end.
- Failure injection: each step's failure surfaces a usable error UX.
- No provider secret appears in network tab, console, or client bundle.

## 7. Risks to Watch

- Long-polling step view leaking connections. Cancel on unmount; cap total wait.
- Showing DNS record internals that aren't needed (e.g., SES return-path host). Show only what's useful.
- Treating partial success as success. Require all verification steps to pass before marking `verified`.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/domains/new/**`
- Playwright: `tests/e2e/domain_auto_provision.spec.ts`
- Network test: no provider secret in any client-visible response
