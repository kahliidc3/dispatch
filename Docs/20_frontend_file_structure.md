# Frontend File Structure (Exact Blueprint for dispatch)

This defines the exact frontend structure for our Next.js 16 App Router application, aligned with official Next.js conventions and the stack we selected (TypeScript, Tailwind, shadcn/ui).

---

## 1. Scope

- Frontend web app only (`apps/web`).
- Internal product UI for operators/admins (campaigns, contacts, domains, analytics, settings).
- App Router architecture with Server Components by default.

---

## 2. Exact Frontend Tree

```text
dispatch/
└── apps/
    └── web/
        ├── public/
        │   ├── images/
        │   └── icons/
        ├── src/
        │   ├── app/
        │   │   ├── layout.tsx
        │   │   ├── globals.css
        │   │   ├── not-found.tsx
        │   │   ├── global-error.tsx
        │   │   ├── (auth)/
        │   │   │   ├── layout.tsx
        │   │   │   ├── login/
        │   │   │   │   ├── page.tsx
        │   │   │   │   └── _components/
        │   │   │   │       └── login-form.tsx
        │   │   │   └── mfa/
        │   │   │       ├── page.tsx
        │   │   │       └── _components/
        │   │   │           └── mfa-form.tsx
        │   │   ├── (dashboard)/
        │   │   │   ├── layout.tsx
        │   │   │   ├── loading.tsx
        │   │   │   ├── error.tsx
        │   │   │   ├── page.tsx
        │   │   │   ├── campaigns/
        │   │   │   │   ├── page.tsx
        │   │   │   │   ├── loading.tsx
        │   │   │   │   ├── [campaignId]/
        │   │   │   │   │   ├── page.tsx
        │   │   │   │   │   └── _components/
        │   │   │   │   │       ├── campaign-header.tsx
        │   │   │   │   │       └── campaign-metrics.tsx
        │   │   │   │   ├── create/
        │   │   │   │   │   ├── page.tsx
        │   │   │   │   │   └── _components/
        │   │   │   │   │       ├── campaign-form.tsx
        │   │   │   │   │       └── launch-actions.tsx
        │   │   │   │   ├── _components/
        │   │   │   │   │   ├── campaigns-table.tsx
        │   │   │   │   │   └── campaigns-filters.tsx
        │   │   │   │   └── _lib/
        │   │   │   │       └── campaigns-queries.ts
        │   │   │   ├── contacts/
        │   │   │   │   ├── page.tsx
        │   │   │   │   ├── [contactId]/
        │   │   │   │   │   └── page.tsx
        │   │   │   │   ├── import/
        │   │   │   │   │   └── page.tsx
        │   │   │   │   ├── _components/
        │   │   │   │   │   ├── contacts-table.tsx
        │   │   │   │   │   └── contact-drawer.tsx
        │   │   │   │   └── _lib/
        │   │   │   │       └── contacts-queries.ts
        │   │   │   ├── domains/
        │   │   │   │   ├── page.tsx
        │   │   │   │   ├── [domainId]/
        │   │   │   │   │   └── page.tsx
        │   │   │   │   ├── _components/
        │   │   │   │   │   ├── domain-health-grid.tsx
        │   │   │   │   │   └── circuit-breaker-badges.tsx
        │   │   │   │   └── _lib/
        │   │   │   │       └── domains-queries.ts
        │   │   │   ├── templates/
        │   │   │   │   ├── page.tsx
        │   │   │   │   ├── [templateId]/
        │   │   │   │   │   └── page.tsx
        │   │   │   │   └── _components/
        │   │   │   │       ├── template-editor.tsx
        │   │   │   │       └── preview-pane.tsx
        │   │   │   ├── analytics/
        │   │   │   │   ├── page.tsx
        │   │   │   │   ├── reputation/
        │   │   │   │   │   └── page.tsx
        │   │   │   │   └── _components/
        │   │   │   │       ├── kpi-cards.tsx
        │   │   │   │       └── engagement-charts.tsx
        │   │   │   ├── suppression/
        │   │   │   │   ├── page.tsx
        │   │   │   │   └── _components/
        │   │   │   │       └── suppression-table.tsx
        │   │   │   ├── settings/
        │   │   │   │   ├── page.tsx
        │   │   │   │   ├── users/page.tsx
        │   │   │   │   └── api-keys/page.tsx
        │   │   │   └── _components/
        │   │   │       ├── sidebar.tsx
        │   │   │       ├── topbar.tsx
        │   │   │       └── command-palette.tsx
        │   │   └── api/
        │   │       ├── health/route.ts
        │   │       └── session/route.ts
        │   ├── components/
        │   │   ├── ui/                       # shadcn-generated primitives
        │   │   ├── shared/
        │   │   │   ├── data-table.tsx
        │   │   │   ├── empty-state.tsx
        │   │   │   └── confirm-dialog.tsx
        │   │   └── charts/
        │   │       ├── line-chart.tsx
        │   │       └── heatmap.tsx
        │   ├── lib/
        │   │   ├── api/
        │   │   │   ├── server.ts
        │   │   │   ├── client.ts
        │   │   │   ├── endpoints.ts
        │   │   │   └── errors.ts
        │   │   ├── auth/
        │   │   │   ├── session.ts
        │   │   │   └── guards.ts
        │   │   ├── env.ts
        │   │   ├── utils.ts
        │   │   ├── formatters.ts
        │   │   └── telemetry.ts
        │   ├── hooks/
        │   │   ├── use-debounce.ts
        │   │   ├── use-query-state.ts
        │   │   └── use-copy.ts
        │   ├── types/
        │   │   ├── api.ts
        │   │   ├── campaign.ts
        │   │   ├── contact.ts
        │   │   └── domain.ts
        │   └── styles/
        │       └── tokens.css
        ├── components.json               # shadcn/ui config
        ├── next.config.ts
        ├── tsconfig.json
        ├── postcss.config.mjs
        ├── eslint.config.mjs
        └── package.json
```

---

## 3. Why This Structure

- Uses App Router conventions (`layout.tsx`, `page.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, `route.ts`).
- Uses route groups (`(auth)`, `(dashboard)`) to organize by product area without URL pollution.
- Uses private folders (`_components`, `_lib`) to colocate route-specific code that should not be routable.
- Keeps reusable primitives in `components/ui` (shadcn/ui), while feature-specific UI stays near routes.
- Keeps API/auth/env/utility code in `src/lib` for clean separation from presentation.

---

## 4. Best-Practice Rules for This Repo

1. Default to Server Components for pages/layouts; add `"use client"` only where interactivity is needed.
2. Keep providers as deep as possible (avoid wrapping the entire document when unnecessary).
3. Put loading and error boundaries at route-segment level (`loading.tsx`, `error.tsx`) for better UX.
4. Fetch sensitive or credentialed data in Server Components.
5. Use `route.ts` in `app/api/*` only for frontend-adjacent handlers (health/session/BFF needs), not to duplicate core backend APIs.
6. Keep route-level UI colocated in `_components`; move broadly reusable UI to `src/components/shared`.
7. Keep component render logic pure and side effects in handlers/effects.
8. Keep import aliases consistent (`@/*` -> `src/*`).

---

## 5. Mapping to dispatch Product Areas

- `(dashboard)/campaigns`: build, launch, monitor campaigns.
- `(dashboard)/contacts`: browse/import/manage contacts and suppression exposure.
- `(dashboard)/domains`: domain health, verification, warmup, breaker state.
- `(dashboard)/templates`: template versions and previews.
- `(dashboard)/analytics`: KPI + deliverability + reputation views.
- `(dashboard)/suppression`: suppression list operations and audits.
- `(dashboard)/settings`: users, API keys, and platform settings.

---

## 6. Optional Additions (When Needed)

- `src/app/@modal` parallel route for global modals (details drawer/edit forms).
- `src/app/(dashboard)/forbidden.tsx` for permission failures.
- `src/app/(dashboard)/unauthorized.tsx` for authz-denied segment UX.
- `src/lib/cache/` if explicit caching policies become complex.

---

## 7. Official Documentation References

- Next.js App Router:
  - https://nextjs.org/docs/app
- Next.js Project Structure:
  - https://nextjs.org/docs/app/getting-started/project-structure
- Next.js Server and Client Components:
  - https://nextjs.org/docs/app/getting-started/server-and-client-components
- Next.js Fetching Data:
  - https://nextjs.org/docs/app/getting-started/fetching-data
- Next.js Route Handlers:
  - https://nextjs.org/docs/app/getting-started/route-handlers
- Next.js loading.js:
  - https://nextjs.org/docs/app/api-reference/file-conventions/loading
- Next.js error.js:
  - https://nextjs.org/docs/app/api-reference/file-conventions/error
- Next.js Route Groups:
  - https://nextjs.org/docs/app/api-reference/file-conventions/route-groups
- Next.js file conventions index:
  - https://nextjs.org/docs/app/api-reference/file-conventions
- shadcn/ui Next.js setup:
  - https://ui.shadcn.com/docs/installation/next
- Tailwind + Next.js installation:
  - https://tailwindcss.com/docs/installation/framework-guides/nextjs
- React component purity:
  - https://react.dev/learn/keeping-components-pure
