# Backend Sprints — Acmemail (`dispatch`)

This folder defines the full backend delivery plan for Acmemail, broken into sequenced sprints.

One backend engineer executes these sprints on a dedicated branch per sprint (`backend/sprint-NN-<slug>`). A sprint is not complete until its **exit criteria** are met *and* its tests pass on the branch. After review, the branch merges back into the backend integration branch, then eventually into `main` alongside the matching frontend work.

All sprints draw from the specifications in [../](../) (the `Docs/` folder). The domain model in [../21_domain_model.md](../21_domain_model.md) is the contract that keeps backend, frontend, and database aligned — every sprint must respect its aggregates, invariants, and lifecycle models.

---

## Sprint Map

### Phase 1 — MVP (10K–75K sends/day)

| # | Sprint | Focus |
|---|---|---|
| 00 | [Foundation & Monorepo Bootstrap](sprint_00_foundation_and_bootstrap.md) | Repo layout, Docker Compose, base app skeletons |
| 01 | [Core Infrastructure: Config, DB, Migrations, Errors, Logging](sprint_01_core_infrastructure.md) | Pydantic settings, async SQLAlchemy, Alembic, error taxonomy, structured logs |
| 02 | [Auth, Users & API Keys](sprint_02_auth_users_api_keys.md) | Argon2id, TOTP MFA, API key lifecycle, auth middleware |
| 03 | [Domains, Sender Profiles & IP Pools](sprint_03_domains_sender_profiles_ip_pools.md) | Sending identity infrastructure (manual DNS for MVP) |
| 04 | [Contacts, Lists & Preferences](sprint_04_contacts_lists_preferences.md) | Contact aggregate, lists, subscription status |
| 05 | [CSV Import Pipeline (Gates 1–3)](sprint_05_csv_import_pipeline.md) | Format, SMTP validation, role-account filter |
| 06 | [Templates & Template Versioning](sprint_06_templates_and_versioning.md) | Template authoring and immutable versions |
| 07 | [Segments & Segment Snapshots](sprint_07_segments_and_snapshots.md) | Query DSL, evaluation, append-only snapshots |
| 08 | [Suppression Service](sprint_08_suppression_service.md) | Platform-wide suppression, unsubscribe tokens |
| 09 | [SES Client & Send Pipeline (Gates 4–7)](sprint_09_ses_client_and_send_pipeline.md) | SES wrapper, idempotent send task, status machine |
| 10 | [Webhook Receiver & Event Worker](sprint_10_webhook_and_event_worker.md) | SNS verify, event ingestion, suppression writes |
| 11 | [Analytics & Dashboard APIs](sprint_11_analytics_and_dashboards.md) | Rolling metrics, dashboard endpoints |

### Phase 2 — Scale (75K–300K sends/day)

| # | Sprint | Focus |
|---|---|---|
| 12 | [Per-Domain Queues & Token Bucket Rate Limiting](sprint_12_per_domain_queues_and_throttle.md) | `send.<domain>` queues, Redis Lua bucket |
| 13 | [Circuit Breakers (4 Scopes) & Evaluator](sprint_13_circuit_breakers.md) | Domain / IP pool / sender / account, fail-closed |
| 14 | [Automated Domain Provisioning](sprint_14_automated_domain_provisioning.md) | Cloudflare + Route 53 DNS, SES identity, verification polling |
| 15 | [Warmup Engine & Postmaster Tools](sprint_15_warmup_engine_and_postmaster.md) | Ramp schedules, Google Postmaster integration |
| 16 | [Full Observability Stack](sprint_16_full_observability_stack.md) | OpenTelemetry tracing, RED metrics, four-tier alerts |

### Phase 3 — ML (300K–600K sends/day)

| # | Sprint | Focus |
|---|---|---|
| 17 | [ML: Pre-Send Spam Scorer (Model 1)](sprint_17_ml_spam_scorer.md) | Heuristic → sklearn LogReg → XGBoost |
| 18 | [ML: Reply Intent Classifier (Model 2)](sprint_18_ml_reply_intent_classifier.md) | TF-IDF LinearSVC → DistilBERT, 7 intents |
| 19 | [ML: Anomaly Detection & Send-Time Optimization](sprint_19_ml_anomaly_and_send_time_optimization.md) | EMA 3σ, gradient-boosted STO |

### Phase 4 — 1M/Day (600K–1M+ sends/day)

| # | Sprint | Focus |
|---|---|---|
| 20 | [Partitioning, Archival & Performance Hardening](sprint_20_partitioning_and_performance.md) | Monthly partitions for `messages` + event tables |
| 21 | [DR, SOC 2 Readiness & Security Hardening](sprint_21_dr_soc2_and_security_hardening.md) | Cross-region DR, SOC 2 Type I, final audit |

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

- One branch per sprint: `backend/sprint-NN-<slug>`.
- Open a PR against `backend/integration` when exit criteria are met.
- Never merge with failing tests or coverage regressions.
- Coverage thresholds defined in [../CLAUDE.md](../../CLAUDE.md) (95%+ on critical modules) are enforced by CI from Sprint 01 onward.
- Never widen a sprint's scope to "finish something nearby." File a follow-up sprint.
- Cross-reference the [domain model](../21_domain_model.md) before designing new tables or services.
