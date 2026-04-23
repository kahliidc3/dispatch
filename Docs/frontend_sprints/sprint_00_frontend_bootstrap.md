# Sprint 00 — Frontend Bootstrap

**Phase:** MVP
**Estimated duration:** 3–5 days
**Branch:** `frontend/sprint-00-bootstrap`
**Depends on:** backend Sprint 00 (shared Docker Compose only)

---

## 1. Purpose

Stand up the `apps/web` Next.js 16 application with the exact folder tree from [../20_frontend_file_structure.md](../20_frontend_file_structure.md), wired to lint, type-check, unit, and E2E test pipelines. No product UI ships in this sprint.

## 2. What Should Be Done

Bootstrap a Next.js 16 App Router app with TypeScript, Tailwind, and shadcn/ui. Create all route groups and placeholder pages from the file-structure spec. Wire Vitest + React Testing Library, Playwright, ESLint, and a CI pipeline.

## 3. Docs to Follow

- [../20_frontend_file_structure.md](../20_frontend_file_structure.md) — exact folder tree
- [../18_nextjs_documentation.md](../18_nextjs_documentation.md) — version baseline, install, conventions
- [../13_deployment_infrastructure.md](../13_deployment_infrastructure.md) — environment targets

## 4. Tasks

### 4.1 Scaffold
- [ ] `pnpm create next-app@latest apps/web --ts --app --tailwind --eslint --src-dir --import-alias "@/*"`.
- [ ] Pin Node `20.9+` in `.nvmrc`; pin `pnpm` version.
- [ ] Set up `components.json` and install shadcn/ui base primitives (`button`, `input`, `dialog`, `table`, `toast`, `dropdown-menu`, `tabs`, `badge`).

### 4.2 Folder tree
- [ ] Create every folder and placeholder file from §2 of `20_frontend_file_structure.md`.
- [ ] `app/layout.tsx`, `app/globals.css`, `app/not-found.tsx`, `app/global-error.tsx`.
- [ ] Route groups `(auth)` and `(dashboard)` with empty `layout.tsx`, `page.tsx`, `loading.tsx`, `error.tsx`.
- [ ] Stub pages for every dashboard route (campaigns, contacts, domains, templates, analytics, suppression, settings).

### 4.3 Tooling
- [ ] ESLint config (Next.js preset + project rules).
- [ ] Prettier + `eslint-config-prettier`.
- [ ] `vitest.config.ts` with React Testing Library + `@testing-library/jest-dom`.
- [ ] `playwright.config.ts` targeting `http://localhost:3000`.
- [ ] `@axe-core/playwright` for a11y checks.

### 4.4 Dev environment
- [ ] `apps/web/Dockerfile` (Node 20 alpine, multi-stage).
- [ ] Add `web` service to the repo-root `docker-compose.yml`.
- [ ] `make dev` brings up web alongside backend services.

### 4.5 CI
- [ ] GitHub Actions workflow: install → typecheck → lint → vitest → build → playwright smoke.
- [ ] Coverage reporter scaffolding (threshold raised in Sprint 01).

## 5. Deliverables

- `pnpm dev` serves `/` (empty dashboard shell) and `/login` (empty form page).
- `pnpm test`, `pnpm test:e2e`, `pnpm lint`, `pnpm typecheck` all pass on the empty scaffold.
- CI green on the initial PR.

## 6. Exit Criteria

- Every folder and placeholder file from [../20_frontend_file_structure.md](../20_frontend_file_structure.md) exists.
- Every test runner executes successfully on an empty test suite.
- Docker image builds and runs under Compose.
- No TypeScript `any`, no ESLint warnings, no unused `"use client"` directives.

## 7. Risks to Watch

- Next.js 16 / Turbopack incompatibilities with a Tailwind or shadcn plugin. Pin all versions; document workarounds.
- Accidentally introducing a client boundary at the root layout. Keep `layout.tsx` server-only.
- Playwright flakes on CI due to missing browsers. Cache Playwright browsers in CI.

## 8. Tests to Run

- `pnpm typecheck`
- `pnpm lint`
- `pnpm test` (trivial smoke)
- `pnpm test:e2e` (load `/` and `/login`, assert status)
