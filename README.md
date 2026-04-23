# dispatch

dispatch is an internal high-volume email platform built to handle 1M+ sends per day. It is not a SaaS product and has no multi-tenancy — it is a single-namespace system built exclusively for internal use.

## What it is

dispatch is a purpose-built email delivery platform split into two planes:

- **Control plane** — everything we build: contact management, campaign authoring, list segmentation, suppression, analytics, and an ML layer for spam scoring and send-time optimization.
- **Delivery plane** — everything we rent: AWS SES as the sole SMTP backbone.

The platform is designed around the assumption that deliverability is the product. Every architectural decision — from per-domain Celery queues to circuit breakers set at half of SES's warning thresholds — exists to protect sender reputation.

## What it is not

- Not a SaaS platform. There are no organizations, tenants, or plan tiers.
- Not a transactional email system. It is campaign/bulk email only.
- Not a multi-ESP system. AWS SES is the only delivery provider.

## Core capabilities

- **Campaign management** — author, schedule, and launch email campaigns against segmented contact lists.
- **Contact & list management** — import contacts, build dynamic segments with snapshot isolation at send time.
- **Suppression & compliance** — platform-wide suppression list, synced to SES account suppression; unsubscribe handling; GDPR erasure.
- **Deliverability guardrails** — circuit breakers across four scopes (domain, IP pool, sender profile, account), token-bucket rate limiting per domain, seven-gate pre-send validation.
- **Event pipeline** — SES bounce/complaint/delivery events flow through SNS → webhook receiver → Celery → suppression writes and circuit breaker re-evaluation.
- **ML services** — pre-send spam scorer, reply intent classifier, anomaly detection on engagement metrics, send-time optimization.
- **Observability** — structured JSON logging, OpenTelemetry tracing, RED metrics, four-tier alerting.

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI + SQLAlchemy 2.0 async |
| Background workers | Celery + Redis |
| Database | PostgreSQL 15+ |
| Email delivery | AWS SES |
| Event bus | AWS SNS |
| ML | scikit-learn, XGBoost, DistilBERT |
| Infrastructure | AWS ECS (Fargate), RDS, ElastiCache, Terraform |
| Frontend | Next.js 16 (App Router) |

## Scale targets

| Phase | Volume |
|---|---|
| MVP | 10K–75K sends/day |
| Scale | 75K–300K sends/day |
| ML | 300K–600K sends/day |
| Full | 1M+ sends/day |

## Documentation

Detailed design documentation lives in [Docs/](Docs/).

| File | Contents |
|---|---|
| [00_project_overview.md](Docs/00_project_overview.md) | Plain-English project description |
| [01_schema.sql](Docs/01_schema.sql) | Full PostgreSQL schema |
| [02_system_design.md](Docs/02_system_design.md) | Master system design document |
| [05_goals_and_non_goals.md](Docs/05_goals_and_non_goals.md) | Goals, non-goals, and success metrics |
| [06_system_context.md](Docs/06_system_context.md) | Actors, external systems, data flows |
| [07_functional_requirements.md](Docs/07_functional_requirements.md) | Functional requirements |
| [08_non_functional_requirements.md](Docs/08_non_functional_requirements.md) | Performance, availability, security requirements |
| [09_data_model.md](Docs/09_data_model.md) | Schema groups, invariants, partitioning |
| [10_delivery_pipeline.md](Docs/10_delivery_pipeline.md) | Send task flow and seven-gate validation |
| [11_operational_guardrails.md](Docs/11_operational_guardrails.md) | Circuit breakers and rate limiting |
| [12_ml_services.md](Docs/12_ml_services.md) | ML models and inference pipeline |
| [13_deployment_infrastructure.md](Docs/13_deployment_infrastructure.md) | VPC topology, environments, IaC |
| [14_security.md](Docs/14_security.md) | Auth, encryption, secrets, compliance |
| [15_observability.md](Docs/15_observability.md) | Metrics, logging, tracing, alerting |
| [16_rollout_plan.md](Docs/16_rollout_plan.md) | Phase-by-phase rollout plan |
| [17_fastapi_documentation.md](Docs/17_fastapi_documentation.md) | FastAPI implementation guidance with official references |
| [18_nextjs_documentation.md](Docs/18_nextjs_documentation.md) | Next.js App Router implementation guidance with official references |
| [19_backend_file_structure.md](Docs/19_backend_file_structure.md) | Exact backend folder/file blueprint for dispatch (best-practice aligned) |
| [20_frontend_file_structure.md](Docs/20_frontend_file_structure.md) | Exact frontend folder/file blueprint for dispatch (App Router best-practice aligned) |
| [21_domain_model.md](Docs/21_domain_model.md) | Business domain model to align frontend, backend, and database design |
