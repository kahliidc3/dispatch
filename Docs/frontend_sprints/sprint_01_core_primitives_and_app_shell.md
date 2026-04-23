# Sprint 01 — Core Primitives, API Client & App Shell

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-01-primitives-shell`
**Depends on:** frontend Sprint 00, backend Sprint 01

---

## 1. Purpose

Ship the cross-cutting foundations every feature sprint relies on: a typed API client for both Server and Client Components, the app shell (sidebar, topbar, command palette), shared primitives (data table, empty state, confirm dialog), and the error/auth boundary pattern.

## 2. What Should Be Done

Implement `src/lib/api/` (server + client variants), `src/lib/auth/session.ts`, the dashboard shell under `app/(dashboard)/layout.tsx`, and shared primitives under `src/components/shared/` and `src/components/charts/`.

## 3. Docs to Follow

- [../18_nextjs_documentation.md](../18_nextjs_documentation.md) §5 Server vs Client, §8 Auth, §6 Fetching
- [../20_frontend_file_structure.md](../20_frontend_file_structure.md) §4 Best-Practice Rules
- [../14_security.md](../14_security.md) — cookie + session handling rules
- [../15_observability.md](../15_observability.md) — client telemetry expectations

## 4. Tasks

### 4.1 Environment
- [ ] `src/lib/env.ts`: typed env parser (zod), separate server and `NEXT_PUBLIC_*` schemas.
- [ ] Fail-fast if a required env var is missing.

### 4.2 API client
- [ ] `src/lib/api/endpoints.ts`: constants for every backend route planned through Phase 1.
- [ ] `src/lib/api/server.ts`: server-side fetcher that forwards the session cookie and adds a request id.
- [ ] `src/lib/api/client.ts`: browser fetcher for interactive flows, same error envelope handling.
- [ ] `src/lib/api/errors.ts`: map backend error envelopes → typed errors (`UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `ConflictError`, `RateLimitedError`).

### 4.3 Auth helpers
- [ ] `src/lib/auth/session.ts`: `getSession()` for Server Components, `requireSession()` throws → redirect.
- [ ] `src/lib/auth/guards.ts`: `requireAdmin()`, `requireUser()` guards usable in layouts and routes.
- [ ] `app/api/session/route.ts`: BFF refresh endpoint used by the client only when needed.

### 4.4 App shell
- [ ] `app/(dashboard)/layout.tsx`: Server Component that gates on session, renders sidebar + topbar.
- [ ] `_components/sidebar.tsx`, `_components/topbar.tsx`.
- [ ] `_components/command-palette.tsx` (Client Component) with keyboard shortcut (⌘K / Ctrl+K).

### 4.5 Shared primitives
- [ ] `components/shared/data-table.tsx`: headless table with sort + paginate + keyset cursor support.
- [ ] `components/shared/empty-state.tsx`, `components/shared/confirm-dialog.tsx`.
- [ ] `components/charts/line-chart.tsx`, `components/charts/heatmap.tsx` (chosen charting lib wrapped once).

### 4.6 Telemetry & errors
- [ ] `src/lib/telemetry.ts`: `track(event, props)` hook emitting to the observability backend.
- [ ] `app/global-error.tsx` and route-level `error.tsx` boundaries render a friendly fallback and send an error report.
- [ ] Redact any PII (emails) before sending telemetry.

## 5. Deliverables

- Logged-in user sees an empty but navigable dashboard shell.
- Any feature sprint can add `ColumnDef[]` + `fetcher` and get a production-grade table.
- Every API call routes through the typed client and returns typed results.

## 6. Exit Criteria

- Lighthouse a11y score ≥ 95 on the shell.
- Unit tests ≥ 80% on `src/lib/api/*` and `src/lib/auth/*`.
- Visual smoke: shell renders with keyboard-only navigation.
- No `any` in new code; no unused `"use client"` directives.

## 7. Risks to Watch

- Leaking session cookies into client bundles. Keep session access strictly in Server Components / Route Handlers.
- Over-centralized providers slowing first paint. Scope providers tightly.
- Chart library bloat (e.g., Recharts + Chart.js both). Pick one and stick with it.

## 8. Tests to Run

- `pnpm test src/lib/**`
- `pnpm test src/components/shared/**`
- Playwright smoke: open shell, navigate via keyboard only.
- `@axe-core/playwright` on the shell layout.
