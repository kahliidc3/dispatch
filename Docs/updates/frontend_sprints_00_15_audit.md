# Frontend Sprints 00-15 Compliance Audit

## Rubric
- `Pass`: sprint intent and checklist-critical criteria are met with production-viable wiring.
- `Partial`: substantial UI exists, but one or more checklist-critical integration or acceptance items are incomplete.
- `Fail`: checklist-critical behavior is largely mock-driven or blocked by missing API parity.

---

## Sprint 00 - Frontend Bootstrap

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 00 | Partial | Yes | N/A | Partial | Next.js 16 app scaffold, Dockerfile, vitest/playwright configs, dashboard/auth route groups, global/route error boundaries are present. | Sprint-00 checklist items for compose/CI are not fully satisfied: no frontend CI workflow exists and backend compose currently does not include a `web` service. | `C:\Users\khali\Desktop\Emailing Project\frontend\package.json:5`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\package.json:7`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\Dockerfile:1`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\playwright.config.ts:13`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\vitest.config.mts:4`<br>`C:\Users\khali\Desktop\Emailing Project\backend\docker-compose.yml:1`<br>`C:\Users\khali\Desktop\Emailing Project\.github\workflows\backend-ci.yml:1` |

Checklist mapping:
- [x] Core frontend scaffold and tooling files exist.
- [x] Route groups and error boundaries exist.
- [~] Compose + CI acceptance items are incomplete for frontend.

## Sprint 01 - Core Primitives, API Client & App Shell

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 01 | Pass | Yes | Yes | Yes | Typed env parsing, server/client API wrappers with error mapping, session/admin guards, protected dashboard shell, reusable data table with keyset support, and telemetry/error boundaries are implemented. | No checklist-critical blocker found in this pass. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\env.ts:1`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\server.ts:102`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\client.ts:100`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\errors.ts:126`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\auth\session.ts:36`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\auth\guards.ts:19`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\layout.tsx:11`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\components\shared\data-table.tsx:38`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\telemetry.ts:92`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\global-error.tsx:12` |

Checklist mapping:
- [x] Core API/auth primitives exist and are reusable.
- [x] Dashboard shell is session-gated.
- [x] Telemetry includes PII redaction flow.

## Sprint 02 - Auth UI: Login, MFA, Session Guards

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 02 | Partial | Yes | Partial | Partial | Login + MFA forms are implemented with validation, autosubmit, challenge-expiry routing, and BFF session route usage. Admin-gated API keys/users pages exist. | API keys and users management are still seeded from static local arrays and local state (not backend-wired). Frontend contract expects `/auth/api-keys` and `/users/{id}/reset-mfa`, while backend exposes `/users/me/api-keys` and no `/users/{id}/reset-mfa`. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(auth)\login\_components\login-form.tsx:49`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(auth)\mfa\_components\mfa-form.tsx:120`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\api\session\route.ts:122`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\settings\api-keys\page.tsx:5`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\settings\users\page.tsx:5`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\settings\users\_components\users-manager.tsx:156`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:10`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:17`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\users.py:136` |

Checklist mapping:
- [x] Login/MFA UX and session-guard behavior are implemented.
- [x] Admin-only surfaces are present.
- [~] Settings users/API-key operations are not production-wired to backend contracts.

## Sprint 03 - Domains & Sender Profiles UI

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 03 | Fail | Yes | Partial | No | Domains and sender-profile pages/components exist; create/verify/retire actions call backend endpoints. | Core list/detail data is mock-seeded (`domainList`, `getDomainDetail`, `senderProfiles`) instead of server-fetched via `serverJson`, which violates sprint acceptance for production wiring. | `C:\Users\khali\Desktop\Emailing Project\Docs\frontend_sprints\sprint_03_domains_and_sender_profiles_ui.md:27`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\page.tsx:5`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\page.tsx:23`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\[domainId]\page.tsx:41`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\sender-profiles\page.tsx:3`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\_components\verify-button.tsx:81` |

Checklist mapping:
- [x] Required UI surfaces exist.
- [~] Action buttons are partly wired.
- [ ] Checklist-critical data loading is still mock-driven.

## Sprint 04 - Contacts & Lists UI

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 04 | Fail | Yes | Partial | No | Contacts/lists pages, contact drawer, bulk-action UX, and public unsubscribe page exist. Some actions call backend (delete, bulk unsubscribe, list add/remove). | Primary contacts/lists data is still mock-seeded. Public unsubscribe UI posts to `/unsubscribe` body-token contract, but backend public routes are `/u/{token}` and `/contacts/unsubscribe/public`, causing parity mismatch. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\contacts\page.tsx:4`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\contacts\page.tsx:25`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\lists\page.tsx:2`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\contacts\_components\contacts-table.tsx:115`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\unsubscribe\_components\unsubscribe-form.tsx:42`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\unsubscribe.py:12`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\contacts.py:160` |

Checklist mapping:
- [x] Contact/list UI components are present.
- [~] Several write actions call APIs.
- [ ] Read/data and unsubscribe-contract parity do not match acceptance.

## Sprint 05 - CSV Import Wizard

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 05 | Fail | Yes | No | No | Upload/mapping/progress/review wizard flow is implemented with polling UX and error review UI. | Frontend targets `/contacts/bulk-import*` endpoints, but backend import APIs are under `/imports`; required endpoint parity is missing, so production flow is blocked. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\contacts\import\page.tsx:95`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\contacts\import\_components\progress-step.tsx:31`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\contacts\import\_components\review-step.tsx:56`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:50`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\imports.py:24`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\imports.py:54` |

Checklist mapping:
- [x] Wizard UI and progress/error UX exist.
- [ ] Backend route parity for import contract is missing.

## Sprint 06 - Template Editor & Versions

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 06 | Fail | Yes | Partial | No | Template manager/editor/preview/version-history UI exists; version create/update calls are present in workspace components. | Listing/detail/merge-tags are mock-backed (`mockTemplates`, `mockMergeTags`). Frontend expects `/templates/merge-tags` and publish-version route not present in backend router; acceptance remains unmet. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\templates\page.tsx:3`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\templates\[templateId]\page.tsx:7`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\templates\_components\template-workspace.tsx:54`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:83`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:85`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\templates.py:21` |

Checklist mapping:
- [x] Editor/version UI is implemented.
- [~] Some mutation calls are wired.
- [ ] Critical read-path and merge-tag/publish API parity is missing.

## Sprint 07 - Segment Builder

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 07 | Fail | Yes | Partial | No | Segment builder UI, condition groups, preview panel, and create/update/delete actions exist. | Segment list/source-of-truth is mock-backed; frontend expects duplicate/evaluate routes, while backend exposes preview only (no evaluate endpoint), so acceptance is not met. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\segments\page.tsx:2`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\segments\_components\segments-manager.tsx:43`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\segments\_components\segments-manager.tsx:67`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\segments\_components\preview-panel.tsx:34`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:75`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\segments.py:118` |

Checklist mapping:
- [x] Visual builder surfaces exist.
- [~] Partial API calls exist.
- [ ] Checklist parity for evaluate/fully wired data is missing.

## Sprint 08 - Suppression UI

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 08 | Fail | Yes | Partial | No | Suppression manager UI, add/remove/reveal flows, reason filtering, and admin-gated actions are implemented. | List and sync status are mock-seeded; frontend contract expects `/suppression/export` and `/suppression/{id}/reveal`, but backend router currently exposes list/get/create/delete/bulk-import only. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\suppression\page.tsx:5`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\suppression\page.tsx:26`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\suppression\_components\suppression-manager.tsx:138`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:109`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:112`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\suppression.py:22` |

Checklist mapping:
- [x] UI workflows and safety affordances exist.
- [~] Some mutation calls are wired.
- [ ] Production list/read + reveal/export endpoint parity is incomplete.

## Sprint 09 - Campaign Authoring & Launch UI

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 09 | Fail | Yes | No | No | Multi-step campaign authoring wizard is implemented with review/confirmation UX and launch intent flow. | Wizard depends on mock templates/senders/segments/lists/preflight checks; create/list/update/preflight backend routes expected by frontend are absent (backend campaigns router only has lifecycle actions). | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\campaigns\create\_components\step-review.tsx:18`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\campaigns\create\_components\step-review.tsx:65`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\campaigns\create\_components\step-review.tsx:74`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:89`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:93`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\campaigns.py:24` |

Checklist mapping:
- [x] Wizard UI/UX exists.
- [ ] Core authoring API parity is missing.

## Sprint 10 - Campaign Monitoring & Message Inspector

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 10 | Fail | Yes | Partial | No | Monitoring page, metrics, message drawer, pause/resume/cancel controls, and requeue UX are present. | Core monitoring data and polling are mock-driven (explicit code comment); backend lacks campaign message/requeue endpoints expected by frontend for production monitoring. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\campaigns\[campaignId]\page.tsx:22`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\campaigns\[campaignId]\_components\campaign-monitor.tsx:67`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\campaigns\[campaignId]\_components\campaign-monitor.tsx:132`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:98`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:101`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\campaigns.py:17` |

Checklist mapping:
- [x] Monitoring UI surfaces exist.
- [~] Lifecycle action buttons are wired.
- [ ] Data plane and message-inspector backend parity are incomplete.

## Sprint 11 - Analytics Dashboards

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 11 | Fail | Yes | No | No | KPI/reputation/engagement dashboard UI components and freshness banner UX are implemented. | Analytics pages are fed by local query modules instead of backend rollup endpoints, so this remains test-covered UI but not production-wired behavior. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\analytics\page.tsx:2`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\analytics\page.tsx:9`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\analytics\reputation\page.tsx:6`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\analytics\_lib\analytics-queries.ts:1`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\analytics.py:132` |

Checklist mapping:
- [x] Dashboard presentation layer exists.
- [ ] Real rollup API integration is not complete.

## Sprint 12 - Per-Domain Throttle & Queue Viewer

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 12 | Partial | Yes | Partial | Partial | Throughput tab UX exists (token bucket cards, deny events, admin edit controls). Ops queues page and viewer exist. | Throughput save uses internal `/api/domains/{id}/throttle` route that is not implemented in app/api or backend API. Queue viewer data is mock-seeded from ops queries. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\[domainId]\_components\throughput-tab.tsx:44`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\ops\queues\page.tsx:2`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\ops\_lib\ops-queries.ts:1`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\api\health\route.ts:1`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\api\session\route.ts:1` |

Checklist mapping:
- [x] UI for throttle/queues is implemented.
- [~] Write path exists in UI intent.
- [ ] Backend/internal API wiring for throttle + live queues is incomplete.

## Sprint 13 - Circuit Breaker Console

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 13 | Partial | Yes | Partial | Partial | Breaker console matrix, filters, reset dialog with typed justification, and badge usage on feature pages are implemented. | Console source is mock (`getBreakerMatrix`) and reset posts to internal `/api/circuit-breakers/{id}/reset` route not implemented. Backend also lacks dedicated breaker admin router endpoints expected by console operations. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\ops\circuit-breakers\page.tsx:2`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\ops\circuit-breakers\_components\reset-dialog.tsx:52`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\_components\circuit-breaker-badges.tsx:1`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\ops\_lib\ops-queries.ts:1`<br>`C:\Users\khali\Desktop\Emailing Project\backend\libs\core\circuit_breaker\service.py:91` |

Checklist mapping:
- [x] UI controls and safety dialogs exist.
- [~] UI performs reset call intent.
- [ ] Required API/data source wiring is not complete.

## Sprint 14 - Automated Domain Provisioning UI

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 14 | Fail | Yes | No | No | Provider picker/wizard, provisioning status view, and ops provisioning audit UI are implemented. | Provisioning auth/zones/audit are mock-driven (`getMockZones`, `getMockProvisioningAttempt`, `getMockProvisioningAudit`). Frontend expects `/domains/zones` and `/ops/provisioning`; backend router does not expose these routes. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\new\_components\provisioning-wizard.tsx:11`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\new\_components\provisioning-wizard.tsx:133`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\[domainId]\provision\page.tsx:5`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\ops\provisioning\page.tsx:2`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:28`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:35`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\domains.py:123` |

Checklist mapping:
- [x] UX flow exists for automated provisioning.
- [ ] Critical provider/zone/audit API parity is not implemented.

## Sprint 15 - Warmup Schedule & Postmaster Metrics

| Sprint | Status | UI Complete | Real API Integration | Acceptance Match | What's Implemented | Gaps | Evidence |
|---|---|---|---|---|---|---|---|
| 15 | Fail | Yes | No | No | Warmup tab, schedule safety UX (5x guardrails), extension action, and Postmaster tab UI are implemented. | Domain detail seeds warmup/postmaster data from local query modules; frontend calls warmup/postmaster endpoints not present in backend routers. Backend Postmaster is still noop-adapter based and not fully production-integrated. | `C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\[domainId]\page.tsx:11`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\[domainId]\page.tsx:46`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\[domainId]\_components\warmup-tab.tsx:82`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\[domainId]\_components\warmup-tab.tsx:99`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\app\(dashboard)\domains\[domainId]\_components\reputation-tab.tsx:54`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:29`<br>`C:\Users\khali\Desktop\Emailing Project\frontend\src\lib\api\endpoints.ts:32`<br>`C:\Users\khali\Desktop\Emailing Project\backend\apps\api\routers\domains.py:25`<br>`C:\Users\khali\Desktop\Emailing Project\backend\libs\core\postmaster\schemas.py:33` |

Checklist mapping:
- [x] Warmup/Postmaster UI surfaces are present.
- [ ] Backend parity for warmup/postmaster controls is missing.
- [ ] Production Postmaster integration remains incomplete.

---

## Cross-Sprint Frontend Blockers
- Endpoint parity blockers across sprints 02-15 remain high impact (missing backend routes for several frontend contracts).
- Mock/static query modules still feed many dashboard-critical routes, so "test-covered UI" is not equivalent to production-wired behavior.
- E2E runner currently fails startup in this environment due Playwright webServer command using `pnpm` directly:
  - `C:\Users\khali\Desktop\Emailing Project\frontend\playwright.config.ts:14`
  - `C:\Users\khali\Desktop\Emailing Project\frontend\scripts\run-e2e.mjs:6`

## Runtime Evidence Snapshot Used In This Audit
- `backend\\.venv\\Scripts\\python -m pytest -q` -> `225 passed, 5 failed, 1 skipped`.
- `corepack pnpm test` -> `393 passed`.
- `corepack pnpm test:e2e` -> failed at webServer startup (`pnpm` command resolution issue).

## Status Distribution (Frontend 00-15)
- `Pass`: 1
- `Partial`: 4
- `Fail`: 11
