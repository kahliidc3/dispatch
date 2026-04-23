# Frontend Sprints — Acmemail (`dispatch`)

This folder defines the full frontend delivery plan for Acmemail, broken into sequenced sprints that mirror the [backend sprints](../backend_sprints/README.md) one-for-one.

One frontend engineer executes these sprints on a dedicated branch per sprint (`frontend/sprint-NN-<slug>`). A sprint is not complete until its **exit criteria** are met *and* its tests pass on the branch. After review, the branch merges back into the frontend integration branch, then eventually into `main` alongside the matching backend sprint.

The stack is **Next.js 16 (App Router) + TypeScript + Tailwind + shadcn/ui**, per [../18_nextjs_documentation.md](../18_nextjs_documentation.md) and [../20_frontend_file_structure.md](../20_frontend_file_structure.md). The domain model in [../21_domain_model.md](../21_domain_model.md) is the contract that keeps backend, frontend, and database aligned — every sprint must respect its aggregates, invariants, and lifecycle models.

---

## Sprint Map

Each frontend sprint number matches the backend sprint that unblocks it. Frontend SNN depends on backend SNN (and sometimes earlier ones).

### Phase 1 — MVP (10K–75K sends/day)

| # | Sprint | Focus |
|---|---|---|
| 00 | [Frontend Bootstrap](sprint_00_frontend_bootstrap.md) | Next.js 16 scaffold, Tailwind, shadcn/ui, linting, testing |
| 01 | [Core Primitives, API Client & App Shell](sprint_01_core_primitives_and_app_shell.md) | Env, API client, session, data-table, shell layout |
| 02 | [Auth UI: Login, MFA, Session Guards](sprint_02_auth_ui.md) | `(auth)` route group, login + MFA forms, session refresh |
| 03 | [Domains & Sender Profiles UI](sprint_03_domains_and_sender_profiles_ui.md) | Domain list, DNS record viewer, verify flow, sender profiles |
| 04 | [Contacts & Lists UI](sprint_04_contacts_and_lists_ui.md) | Contact browser, lifecycle badges, list memberships |
| 05 | [CSV Import Wizard](sprint_05_csv_import_wizard.md) | Upload → progress → error review |
| 06 | [Template Editor & Versions](sprint_06_template_editor_and_versions.md) | Authoring surface, version history, preview pane |
| 07 | [Segment Builder](sprint_07_segment_builder.md) | Visual DSL builder + live preview |
| 08 | [Suppression UI](sprint_08_suppression_ui.md) | List, reasons, bulk add, audited removal |
| 09 | [Campaign Authoring & Launch UI](sprint_09_campaign_authoring_and_launch_ui.md) | Step-by-step builder, review screen, launch dialog |
| 10 | [Campaign Monitoring & Message Inspector](sprint_10_campaign_monitoring_and_message_inspector.md) | Live run view, message drilldown, event timeline |
| 11 | [Analytics Dashboards](sprint_11_analytics_dashboards.md) | Overview, campaign, domain reputation views |

### Phase 2 — Scale (75K–300K sends/day)

| # | Sprint | Focus |
|---|---|---|
| 12 | [Per-Domain Throttle & Queue Viewer](sprint_12_throttle_and_queue_viewer.md) | Token-bucket telemetry, queue depth |
| 13 | [Circuit Breaker Console](sprint_13_circuit_breaker_console.md) | State matrix across 4 scopes, reset dialog |
| 14 | [Automated Domain Provisioning UI](sprint_14_automated_domain_provisioning_ui.md) | Guided flow, step log, failure recovery |
| 15 | [Warmup Schedule & Postmaster Metrics](sprint_15_warmup_schedule_and_postmaster_metrics.md) | Schedule editor, external reputation view |
| 16 | [Observability Surfaces](sprint_16_observability_surfaces.md) | Pipeline health, alert state, deep-link to traces |

### Phase 3 — ML (300K–600K sends/day)

| # | Sprint | Focus |
|---|---|---|
| 17 | [Spam Scorer UI: Shadow Mode & Rejection Review](sprint_17_spam_scorer_ui.md) | Shadow toggle, rejection drilldown, override |
| 18 | [Reply Intent Inbox](sprint_18_reply_intent_inbox.md) | Triaged reply stream, intent labels, actions |
| 19 | [Anomaly Alerts & STO Opt-in](sprint_19_anomaly_alerts_and_sto_optin.md) | Anomaly feed, per-campaign STO toggle |

### Phase 4 — 1M/Day (600K–1M+ sends/day)

| # | Sprint | Focus |
|---|---|---|
| 20 | [Platform Ops Console](sprint_20_platform_ops_console.md) | Partitions, archival, backpressure controls |
| 21 | [Security & SOC 2 Review UI](sprint_21_security_and_soc2_review_ui.md) | Audit log explorer, access reviews |

---

## Sprint Template

Every sprint file uses the same sections:

1. Purpose
2. What Should Be Done
3. Docs to Follow
4. Tasks
5. Deliverables
6. Exit Criteria
7. Risks to Watch
8. Tests to Run

## Working Conventions

- One branch per sprint: `frontend/sprint-NN-<slug>`.
- Open a PR against `frontend/integration` when exit criteria are met.
- Server Components by default; `"use client"` only where needed.
- Never merge with failing tests or a11y regressions.
- Never widen a sprint's scope. File a follow-up sprint.
- Re-use `components/ui/` (shadcn) primitives; new primitives ship only when proven reusable.
- Frontend sprint NN merges to main only after backend sprint NN is merged (or behind a feature flag).

## Test Tiers

- **Unit / component:** Vitest + React Testing Library.
- **E2E:** Playwright against a local backend stack (`make dev`).
- **Accessibility:** `@axe-core/playwright` on every public page.
- **Visual regression (optional):** Playwright screenshots on stable primitives.
