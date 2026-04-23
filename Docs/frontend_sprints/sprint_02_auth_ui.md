# Sprint 02 — Auth UI: Login, MFA, Session Guards

**Phase:** MVP
**Estimated duration:** 4–6 days
**Branch:** `frontend/sprint-02-auth-ui`
**Depends on:** frontend Sprint 01, backend Sprint 02

---

## 1. Purpose

Deliver the end-to-end authentication experience: login, TOTP MFA, session persistence, and the guard pattern that protects every dashboard route. Also deliver the user-facing API key management screen under Settings.

## 2. What Should Be Done

Build the `(auth)` route group with login and MFA pages, the session guard on `(dashboard)/layout.tsx`, account lockout messaging, and `settings/api-keys` for viewing / creating / revoking keys.

## 3. Docs to Follow

- [../14_security.md](../14_security.md) — Argon2id, MFA, API key UX (one-time reveal)
- [../18_nextjs_documentation.md](../18_nextjs_documentation.md) §8 Auth
- [../21_domain_model.md](../21_domain_model.md) §2.5 Platform Governance

## 4. Tasks

### 4.1 Login flow
- [ ] `(auth)/login/page.tsx` (Server Component) renders the login form.
- [ ] `_components/login-form.tsx` (Client Component) with zod validation.
- [ ] On success with MFA required → redirect to `/mfa`.
- [ ] On lockout → non-leaky error UX ("Sign-in unavailable — try again later").

### 4.2 MFA flow
- [ ] `(auth)/mfa/page.tsx` + `_components/mfa-form.tsx`.
- [ ] 6-digit input with autosubmit and paste support.
- [ ] Handle expired challenge → redirect back to login.

### 4.3 Session management
- [ ] `app/api/session/route.ts` BFF that proxies logout and session refresh.
- [ ] `requireSession()` used in `(dashboard)/layout.tsx` to redirect unauthenticated users.
- [ ] On 401 from any API call → redirect to login and preserve the destination URL.

### 4.4 Settings / API keys
- [ ] `settings/api-keys/page.tsx` with a table of keys (prefix + last-4 + created + last-used + revoked).
- [ ] Create-key modal displays the plaintext key **once** with copy button; dismissing the modal clears the secret from memory.
- [ ] Revoke flow uses the shared confirm dialog; show the reason input.

### 4.5 Settings / Users (admin only)
- [ ] `settings/users/page.tsx` with admin-only guard.
- [ ] Create user, disable, reset MFA.

## 5. Deliverables

- Full auth flow works against backend Sprint 02 APIs.
- Secrets (API keys, MFA codes) never leak to console, telemetry, or storage.
- Settings screens are usable via keyboard and screen reader.

## 6. Exit Criteria

- E2E: login → MFA → dashboard → logout round trip works.
- E2E: wrong MFA is rate-limited and displayed without exposing counts.
- Unit test asserts the plaintext API key is **not** serialized into any form state that survives the modal close.
- axe a11y: 0 violations on auth pages.

## 7. Risks to Watch

- Storing the session token in `localStorage`. Use httpOnly cookies only; never read the token client-side.
- CSRF on logout — use SameSite=strict and/or origin check.
- Paste-trimming on MFA input stripping a leading zero. Use raw string + length check.

## 8. Tests to Run

- `pnpm test src/app/(auth)/**`
- `pnpm test src/app/(dashboard)/settings/**`
- Playwright: `tests/e2e/auth_flow.spec.ts` covering happy + negative paths.
- axe on `/login`, `/mfa`, `/settings/api-keys`.
