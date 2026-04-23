# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Acmemail** is an internal high-volume email platform targeting 1M+ sends/day, built on AWS SES as the sole sending backbone. The platform is split into a **control plane we build** (contacts, campaigns, suppression, analytics, ML) and a **delivery plane we rent** (AWS SES). Single namespace — no multi-tenancy, no org scoping, no plan tiers.

## Development Commands

```bash
make dev                          # Start full local environment (Docker Compose)
alembic upgrade head              # Apply DB migrations
alembic revision --autogenerate -m "<description>"  # Generate migration

pytest tests/unit/                # Run unit tests only
pytest tests/integration/         # Run integration tests (requires Postgres + Redis)
pytest tests/e2e/                 # Run e2e tests (requires LocalStack)
pytest tests/unit/path/test_file.py::test_name  # Run a single test

celery -A apps.workers.send worker -Q send.<domain>   # Start a send worker
celery -A apps.workers.events worker                  # Start event worker
```

Coverage thresholds (95%+ enforced in CI) apply to: `libs/core/suppression/*`, `libs/core/circuit_breaker/*`, `libs/core/campaigns/service.py`, `apps/webhook/handlers.py`, `libs/ses_client/client.py`.

## Architecture

### Monorepo Structure

```
apps/       — Deployable services (api, workers, webhook, scheduler, web)
libs/       — Shared libraries (core, ses_client, dns_provisioner, ml, schemas)
migrations/ — Alembic migration files
infra/      — Terraform IaC, Dockerfiles
tests/      — unit / integration / e2e
```

**Import rule:** `apps/*` may import from `libs/*` but never from each other. `libs/core` is the only lib that imports from the schema.

### Service Layer Pattern

Every domain in `libs/core/<domain>/` has exactly four files:

- `models.py` — SQLAlchemy ORM models
- `schemas.py` — Pydantic DTOs
- `service.py` — **All business rules live here exclusively**
- `repository.py` — Pure CRUD; no business logic

FastAPI routes call service methods only — never the ORM directly. Workers follow the same pattern and construct services the same way routes do.

### Celery Queue Architecture

One Celery queue per sending domain (`send.<domain_name>`). This is the key design decision enabling per-domain circuit breaking. Workers use `task_acks_late=True` and `worker_prefetch_multiplier=1`.

Every send task is **idempotent**: it accepts a `message_id`, reloads the entity, and returns early if `status != 'queued'`. Status transitions are one-way: `queued → sending → sent|failed`.

### Rate Limiting

Enforced **inside the task** via a Redis Lua token bucket (`libs/core/throttle/token_bucket.py`), not by Celery's native `rate_limit`. Default: 150 sends/hour per domain.

### Circuit Breakers

Four scopes: domain, IP pool, sender profile, account. Thresholds are intentionally **half** of SES's warning levels (1.5% bounce / 0.05% complaint at domain level) because by the time AWS warns, reputation damage has already occurred. Evaluated every 60 seconds. Fail-closed: unknown state → pause sending.

### Event Pipeline

SES → SNS → webhook receiver (separate deploy, so campaign API traffic can't starve it) → `events.ses.incoming` Celery queue → event worker → suppression write + metrics update → circuit breaker evaluator.

Suppression is written twice: at segment evaluation (batch filter) and at send time (per-message final check).

### Pre-Send Validation

Seven gates split across two phases:
- **At import time (Gates 1–3):** format, SMTP validation, role-account filter
- **At send time (Gates 4–7):** suppression check, SES account-level suppression, spam trap heuristics, ML spam scorer (reject if score > 0.2)

### Error Taxonomy

All errors inherit from `AcmemailError` (`libs/core/errors.py`). Routes map typed domain exceptions to HTTP codes in a single global handler (`apps/api/exception_handlers.py`) — routes never catch domain exceptions themselves.

### Configuration

All config via environment variables through a single `Settings` class (`libs/core/config.py`, Pydantic `BaseSettings`). No `os.getenv()` scattered through the codebase.

## Critical Data Invariants

These must hold across all code paths (enforced by DB constraints and application logic):

- Every message has a non-null `domain_id` and `sender_profile_id`
- `suppression_entries (email)` is UNIQUE — no duplicates
- Contacts with `lifecycle_status = 'suppressed'` or `'unsubscribed'` cannot receive messages
- `segment_snapshots` is **append-only** — no UPDATE paths
- `circuit_breaker_state = 'open'` pauses all sends in its scope
- `audit_log` entries are never deleted (DB user has INSERT-only permission)

## Testing Approach

- Unit tests (70%): pure functions, validators, no DB/network
- Integration tests (25%): real Postgres in Docker, real Redis; SES mocked at contract level
- E2E tests (5%): full request through FastAPI → Celery → fake SES → webhook via LocalStack
- Test DB wiped between each test via transaction rollback; no shared state
