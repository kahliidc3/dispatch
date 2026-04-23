# Sprint 01 — Core Infrastructure: Config, DB, Migrations, Errors, Logging

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `backend/sprint-01-core-infrastructure`
**Depends on:** Sprint 00

---

## 1. Purpose

Deliver the cross-cutting foundations every future sprint relies on: typed configuration, an async database stack, the first migration, a typed error hierarchy, and structured logging. After this sprint, any domain module can be added without redesign.

## 2. What Should Be Done

Implement `libs/core/config.py`, `libs/core/db/`, `libs/core/errors.py`, `libs/core/logging.py`, the Alembic environment, and the initial migration that creates the full schema from [../01_schema.sql](../01_schema.sql). Wire FastAPI exception handlers and the request `request_id` middleware.

## 3. Docs to Follow

- [../01_schema.sql](../01_schema.sql) — canonical DDL; initial migration must reproduce it
- [../03_code_architecture.md](../03_code_architecture.md) — service layer pattern, structured logging rules
- [../09_data_model.md](../09_data_model.md) — invariants and constraints
- [../15_observability.md](../15_observability.md) — structured JSON log fields
- [../17_fastapi_documentation.md](../17_fastapi_documentation.md) — dependency injection, lifespan
- [../19_backend_file_structure.md](../19_backend_file_structure.md) — where everything lives

## 4. Tasks

### 4.1 Configuration
- [ ] `libs/core/config.py`: single `Settings(BaseSettings)` class covering DB URL, Redis URL, AWS creds, SES region, default rate limits, feature flags.
- [ ] Environment-driven loading; `.env` supported locally only.
- [ ] `get_settings()` dependency usable from routes, tasks, and scripts.

### 4.2 Database layer
- [ ] `libs/core/db/base.py`: declarative base, naming convention for constraints.
- [ ] `libs/core/db/session.py`: async engine + `async_sessionmaker`, lifespan hook on `apps/api`.
- [ ] `libs/core/db/uow.py`: explicit `UnitOfWork` context manager.
- [ ] `libs/core/db/pagination.py`: cursor + offset paginator helpers (keyset-first).

### 4.3 Migrations
- [ ] Wire `migrations/env.py` to `Settings` and metadata from `libs/core/db/base.py`.
- [ ] Generate migration `0001_initial_schema` that produces the schema in `01_schema.sql` — verify structural equality.
- [ ] Document migration workflow in `README_DEV.md`.

### 4.4 Error taxonomy
- [ ] `libs/core/errors.py`: `AcmemailError` root + typed subclasses (`ValidationError`, `NotFoundError`, `ConflictError`, `PermissionDeniedError`, `RateLimitedError`, `CircuitOpenError`, etc.).
- [ ] `apps/api/exception_handlers.py`: one handler mapping each typed error to a stable HTTP status + machine-readable payload.

### 4.5 Logging & request context
- [ ] `libs/core/logging.py`: `structlog`-based JSON logger with required fields (`timestamp`, `level`, `trace_id`, `request_id`, `event`).
- [ ] `apps/api/middleware.py`: request-id middleware; propagate to logs and downstream tasks.

## 5. Deliverables

- A working migration applies `01_schema.sql` byte-equivalent (up to ordering) to a fresh Postgres.
- Typed settings object with >95% attribute coverage for everything planned in later sprints.
- Global exception handler returns consistent JSON error envelopes.
- Every log line is valid JSON and includes `request_id`.

## 6. Exit Criteria

- `alembic upgrade head` on an empty DB reproduces every table from `01_schema.sql`.
- Unit tests cover every error subclass → HTTP mapping.
- Coverage threshold raised in CI: 80% overall, placeholders for future 95% modules.
- One round-trip integration test from API route → service → repo → DB passes.

## 7. Risks to Watch

- Alembic autogenerate drift from `01_schema.sql`. Use manual review; do not blindly trust autogenerate.
- Silent async misuse (implicit IO on attribute access). Enforce `AsyncSession` patterns from day one.
- `Settings` sprawl — keep it as *one* class; no nested per-module settings classes.

## 8. Tests to Run

- `pytest tests/unit/core/test_config.py`
- `pytest tests/unit/core/test_errors.py`
- `pytest tests/integration/db/test_migrations.py`
- `pytest tests/integration/api/test_exception_handlers.py`
