# Next.js Documentation Notes (Project-Oriented)

This document summarizes official Next.js App Router guidance and maps it to Acmemail's frontend needs.

Last verified: **April 23, 2026**

## 1. Version Baseline (Updated)

- Baseline frontend framework: **Next.js 16** (latest major line).
- Use the App Router (`/app`) as the default architecture.
- Keep structure aligned with file conventions (`layout`, `page`, `loading`, `error`, `route`, etc.).

## 2. Upgrade Path to Latest

For repos already on modern Next.js:

- Run: `pnpm next upgrade` (or npm/yarn/bun equivalent).

For older repos that do not support this command:

- Run: `npx @next/codemod@canary upgrade latest`.

Manual fallback:

- `pnpm i next@latest react@latest react-dom@latest eslint-config-next@latest`

## 3. Install / Runtime Essentials

- Minimum Node.js version: `20.9`.
- Recommended project bootstrap:
  - `pnpm create next-app@latest my-app --yes`
- Production scripts:
  - `next dev`
  - `next build`
  - `next start`

## 4. Important Next.js 16 Behavior Notes

- Turbopack is the default bundler (`next dev`, `next build`).
- Starting with Next.js 16, `next build` no longer runs lint automatically.
- Use explicit lint scripts (`eslint` or `biome`) in `package.json`.

## 5. Server vs Client Components

- By default, pages and layouts are Server Components.
- Use Client Components only where interactivity is required (state, browser APIs, event handlers).
- Mark Client boundaries explicitly with `"use client"`.
- Keep `"use client"` as narrow as possible to reduce client bundle size.

## 6. Data Fetching

- Fetch in Server Components by default.
- Organize data access close to the component that needs it.
- Use streaming (`<Suspense>`, `loading.tsx`) for slow dependencies.
- Treat caching intentionally and configure directives based on route behavior.

## 7. Backend Endpoints (Route Handlers)

- Define API endpoints with `route.ts` in the `app` directory.
- Route Handlers use standard Web `Request`/`Response` APIs.
- Supported methods include `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`.
- Do not place `route.ts` and `page.tsx` at the same route segment level.

## 8. Authentication and Security

- Keep auth and authorization checks server-side when possible.
- Protect sensitive data in Server Components and Route Handlers.
- Avoid exposing secrets to client bundles.
- Only `NEXT_PUBLIC_*` env variables are browser-exposed.

## 9. Testing Strategy

Official ecosystem guidance supports:

- Jest or Vitest for unit tests
- Playwright or Cypress for E2E tests

For this project:

- keep component tests fast and isolated
- add E2E coverage for critical flows (auth, campaign launch, analytics views)

## 10. Deployment Patterns

- Node server deployment:
  - `next build`
  - `next start`
- Docker deployment is fully supported.
- Self-hosting supports App Router features, with caching/infra tuning considerations.

## 11. Acmemail Frontend Conventions

- Keep domain-heavy business logic in backend services, not client components.
- Use Route Handlers as BFF endpoints only when needed; avoid duplicating backend API logic.
- Prioritize server rendering for dashboard pages requiring secure data fetching.
- Keep UI state local and predictable; avoid global client state by default.

## 12. Suggested Initial Next.js Structure

```text
apps/web/
  app/
    (auth)/
      login/page.tsx
    (dashboard)/
      campaigns/page.tsx
      contacts/page.tsx
      analytics/page.tsx
    api/
      health/route.ts
    layout.tsx
    page.tsx
    loading.tsx
    error.tsx
  components/
  lib/
  styles/
```

## Official References

- Next.js 16 release: https://nextjs.org/blog/next-16
- Installation: https://nextjs.org/docs/app/getting-started/installation
- Upgrading: https://nextjs.org/docs/app/getting-started/upgrading
- Upgrade guides: https://nextjs.org/docs/app/guides/upgrading
- Version 16 guide: https://nextjs.org/docs/app/guides/upgrading/version-16
- App Router overview: https://nextjs.org/docs/app
- Project Structure: https://nextjs.org/docs/app/getting-started/project-structure
- Server and Client Components: https://nextjs.org/docs/app/getting-started/server-and-client-components
- Fetching Data: https://nextjs.org/docs/app/getting-started/fetching-data
- Route Handlers: https://nextjs.org/docs/app/getting-started/route-handlers
- `route.js` file convention: https://nextjs.org/docs/app/api-reference/file-conventions/route
- Authentication guide: https://nextjs.org/docs/app/guides/authentication
- Environment Variables: https://nextjs.org/docs/app/guides/environment-variables
- Testing guide: https://nextjs.org/docs/app/guides/testing
- Deploying (App Router): https://nextjs.org/docs/app/getting-started/deploying
- Self-hosting guide: https://nextjs.org/docs/app/guides/self-hosting
