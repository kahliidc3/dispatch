# Sprint 02 — Auth, Users & API Keys

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `backend/sprint-02-auth`
**Depends on:** Sprint 01

---

## 1. Purpose

Deliver the authentication and authorization surface used by every other endpoint. This is the gate — no campaign, contact, or domain API can be exposed without it.

## 2. What Should Be Done

Build the `auth` and `users` domain modules plus the API routers that issue sessions, manage TOTP MFA, and create/rotate/revoke API keys. Deliver the `get_current_user` and `require_admin` dependencies other sprints depend on.

## 3. Docs to Follow

- [../14_security.md](../14_security.md) — Argon2id, TOTP MFA, API key format, IAM, KMS
- [../02_system_design.md](../02_system_design.md) — RBAC (admin/user only, no org scoping)
- [../21_domain_model.md](../21_domain_model.md) §2.5 Platform Governance
- [../17_fastapi_documentation.md](../17_fastapi_documentation.md) §4 Security Baseline

## 4. Tasks

### 4.1 Models & repositories
- [ ] `libs/core/auth/models.py`: `User`, `ApiKey`, `UserSession`, `AuditLog` (append-only).
- [ ] `libs/core/auth/repository.py`: CRUD, last-login update, API key lookup by prefix.

### 4.2 Services
- [ ] Password hashing via Argon2id.
- [ ] TOTP MFA enrollment + verification (pyotp).
- [ ] API key generation: `ak_live_<prefix>_<secret>`; store only hash + prefix + last-4.
- [ ] API key rotation + revocation; never reveal the secret after creation response.
- [ ] Session-based auth for the web UI (signed cookies); bearer token for API key auth.

### 4.3 Router & dependencies
- [ ] `apps/api/routers/auth.py`: `POST /auth/login`, `POST /auth/mfa/verify`, `POST /auth/logout`.
- [ ] `apps/api/routers/users.py`: admin-only user CRUD, self profile, API key CRUD.
- [ ] `apps/api/deps.py`: `get_current_user`, `require_admin`, `get_current_actor` (unified user + API key source).
- [ ] Audit log write on: login, MFA enroll, API key create, API key revoke, user create/disable.

### 4.4 Security hardening
- [ ] Brute-force protection: Redis-backed login attempt counter, lock account after N failures.
- [ ] Session invalidation on password change.
- [ ] Permission denied maps to 403 via the global handler.

## 5. Deliverables

- Admin can create users and API keys via API and receive a one-time plaintext secret.
- All subsequent routes can require `Depends(get_current_actor)`.
- Audit log entries for every auth-sensitive action.

## 6. Exit Criteria

- 95%+ coverage on `libs/core/auth/service.py`.
- End-to-end test: create user → login → MFA enroll → MFA login → create API key → use API key on a protected test endpoint → revoke → rejected.
- No path bypasses the actor dependency on protected routers (lint rule or test sweep).
- Argon2id parameters calibrated to ≥100 ms per hash on target hardware.

## 7. Risks to Watch

- Leaking API key secrets in logs. Add a log redactor and a test that fails if any log line contains the secret.
- Storing MFA secrets in plaintext. Encrypt with KMS data key per [../14_security.md](../14_security.md).
- Session fixation / CSRF on the web UI. Implement double-submit token or SameSite=strict cookies.

## 8. Tests to Run

- `pytest tests/unit/core/auth/`
- `pytest tests/integration/api/test_auth_router.py`
- `pytest tests/integration/api/test_api_keys.py`
- `pytest tests/e2e/auth_flow/`
