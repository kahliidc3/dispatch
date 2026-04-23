# Backend File Structure (Exact Blueprint for dispatch)

This file defines the backend directory and file layout we should implement for dispatch, aligned with FastAPI, SQLAlchemy async, Celery, Alembic, and Pydantic settings best practices.

---

## 1. Scope

- Backend only (API + workers + webhook + scheduler + shared backend libs + migrations + tests + scripts).
- Single-tenant internal platform (no org/tenant foldering).
- Designed for high-volume async processing and strict deliverability controls.

---

## 2. Exact Backend Tree

```text
dispatch/
├── apps/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── lifespan.py
│   │   ├── deps.py
│   │   ├── exception_handlers.py
│   │   ├── middleware.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── domains.py
│   │   │   ├── sender_profiles.py
│   │   │   ├── contacts.py
│   │   │   ├── lists.py
│   │   │   ├── segments.py
│   │   │   ├── templates.py
│   │   │   ├── campaigns.py
│   │   │   ├── suppression.py
│   │   │   ├── analytics.py
│   │   │   └── health.py
│   │   └── internal/
│   │       ├── __init__.py
│   │       ├── admin.py
│   │       └── maintenance.py
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── bootstrap.py
│   │   ├── queues.py
│   │   ├── send_tasks.py
│   │   ├── event_tasks.py
│   │   ├── import_tasks.py
│   │   ├── warmup_tasks.py
│   │   ├── metrics_tasks.py
│   │   └── task_base.py
│   │
│   ├── webhook/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── sns_verify.py
│   │   ├── handlers.py
│   │   └── schemas.py
│   │
│   └── scheduler/
│       ├── __init__.py
│       ├── beat.py
│       └── schedules.py
│
├── libs/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── errors.py
│   │   ├── logging.py
│   │   ├── idempotency.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── uow.py
│   │   │   └── pagination.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── domains/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── sender_profiles/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── contacts/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── lists/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── segments/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── imports/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── templates/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── campaigns/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── suppression/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── circuit_breaker/
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── models.py
│   │   ├── throttle/
│   │   │   ├── __init__.py
│   │   │   └── token_bucket.py
│   │   └── analytics/
│   │       ├── __init__.py
│   │       ├── service.py
│   │       ├── repository.py
│   │       └── schemas.py
│   │
│   ├── ses_client/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── errors.py
│   │   ├── retries.py
│   │   └── metrics.py
│   │
│   ├── dns_provisioner/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── cloudflare.py
│   │   └── route53.py
│   │
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── spam_scorer.py
│   │   ├── reply_intent.py
│   │   ├── anomaly.py
│   │   └── send_time_optimization.py
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── common.py
│       ├── pagination.py
│       └── events.py
│
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── tests/
│   ├── unit/
│   │   ├── core/
│   │   ├── ses_client/
│   │   └── ml/
│   ├── integration/
│   │   ├── api/
│   │   ├── workers/
│   │   ├── webhook/
│   │   └── db/
│   ├── e2e/
│   │   ├── campaign_launch_flow/
│   │   └── event_ingestion_flow/
│   ├── fixtures/
│   │   ├── factories.py
│   │   ├── db.py
│   │   ├── redis.py
│   │   └── ses_fake.py
│   └── conftest.py
│
├── scripts/
│   ├── dev/
│   │   ├── seed_local_data.py
│   │   └── create_admin_user.py
│   ├── ops/
│   │   ├── pause_account.py
│   │   ├── pause_campaign.py
│   │   ├── retire_domain.py
│   │   └── provision_domains.py
│   └── data/
│       ├── archive_events.py
│       └── backfill_metrics.py
│
├── alembic.ini
├── pyproject.toml
└── docker-compose.yml
```

---

## 3. File-Level Responsibilities

### `apps/api`
- `main.py`: create FastAPI app, include routers, register handlers/middleware.
- `deps.py`: request-scoped dependencies (DB session, actor, permissions).
- `exception_handlers.py`: central mapping from typed domain errors to HTTP responses.
- `routers/*.py`: endpoint declarations only; no business rules.

### `apps/workers`
- `celery_app.py`: Celery app creation + global config (`task_routes`, ack/prefetch policy).
- `*_tasks.py`: thin task entrypoints that call domain services and enforce idempotency checks.
- `task_base.py`: shared task behavior (structured logging, trace propagation, retry helpers).

### `apps/webhook`
- `main.py`: webhook FastAPI app.
- `sns_verify.py`: SNS signature verification and subscription confirmation flow.
- `handlers.py`: map webhook events to queue tasks quickly (ack fast, process async).

### `libs/core`
- Domain-centric layout (`models.py`, `schemas.py`, `repository.py`, `service.py`) per bounded area.
- `db/session.py`: async engine + async sessionmaker factory.
- `db/uow.py`: explicit transaction boundaries.
- `config.py`: single typed settings object (Pydantic Settings).
- `errors.py`: typed domain error hierarchy used everywhere.

### `migrations`
- `env.py`: migration runtime wiring to metadata and DB URL source.
- `versions/`: immutable revision scripts.

---

## 4. Import and Boundary Rules (Must Enforce)

- `apps/*` may import from `libs/*`, never from sibling `apps/*`.
- Routers may call services only (not repositories/ORM directly).
- Repositories may not call external APIs.
- Task modules may not hold business rules; they orchestrate service calls.
- `libs/schemas` holds shared transport schemas only (no DB side effects).

---

## 5. Async and DB Patterns This Structure Supports

- One `AsyncSession` per request/task unit of work.
- Do not share one `AsyncSession` across concurrent tasks.
- Prefer explicit transaction scopes (`async with session.begin(): ...`).
- Use async-friendly ORM patterns to avoid implicit IO on attribute access.

---

## 6. Celery Patterns This Structure Supports

- Namespaced task names by module path.
- Domain/per-purpose routing via `task_routes`.
- Idempotent task handlers + explicit retry strategy.
- `task_acks_late=True` only when task logic is idempotent.
- `worker_prefetch_multiplier=1` for fairer distribution of long-running send tasks.

---

## 7. Migration and Config Best Practices

- Keep Alembic migration environment in-repo and versioned with app code.
- Use Alembic autogenerate as an assistant, then review migrations manually.
- Centralize environment-based config in `libs/core/config.py`.
- Support `.env` locally, environment variables in deployed environments.

---

## 8. Why This Matches What We Are Building

- Mirrors dispatch architecture docs: thin routes, service-layer business logic, idempotent workers, explicit guardrails.
- Supports per-domain send pipeline and high-volume event ingestion.
- Keeps domain logic reusable between API, workers, and webhook services.
- Scales from MVP to 1M+/day without changing top-level backend layout.

---

## 9. Official Documentation References

- FastAPI, bigger applications and file structure:
  - https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI dependencies:
  - https://fastapi.tiangolo.com/tutorial/dependencies/
- FastAPI async/concurrency behavior:
  - https://fastapi.tiangolo.com/async/
- SQLAlchemy async ORM:
  - https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- SQLAlchemy session basics:
  - https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- Alembic migration environment/tutorial:
  - https://alembic.sqlalchemy.org/en/latest/tutorial.html
- Celery tasks:
  - https://docs.celeryq.dev/en/stable/userguide/tasks.html
- Celery routing:
  - https://docs.celeryq.dev/en/stable/userguide/routing.html
- Celery configuration:
  - https://docs.celeryq.dev/en/stable/userguide/configuration.html
- Celery workers:
  - https://docs.celeryq.dev/en/stable/userguide/workers.html
- Pydantic settings management:
  - https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/
- Pytest good integration practices:
  - https://docs.pytest.org/en/stable/explanation/goodpractices.html

