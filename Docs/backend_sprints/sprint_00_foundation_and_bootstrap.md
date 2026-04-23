# Sprint 00 — Foundation & Monorepo Bootstrap

**Phase:** MVP
**Estimated duration:** 3–5 days
**Branch:** `backend/sprint-00-foundation`
**Depends on:** nothing (first sprint)

---

## 1. Purpose

Lay down the empty but runnable skeleton of the backend monorepo so every subsequent sprint has a home for its code, tests, and infrastructure. No business logic ships in this sprint.

## 2. What Should Be Done

Create the exact folder tree defined in [../19_backend_file_structure.md](../19_backend_file_structure.md), bring up a local dev environment with Docker Compose (Postgres + Redis + LocalStack), and prove that every app process starts cleanly with a trivial `/healthz` route.

## 3. Docs to Follow

- [../19_backend_file_structure.md](../19_backend_file_structure.md) — exact folder tree and file responsibilities
- [../17_fastapi_documentation.md](../17_fastapi_documentation.md) — app skeleton, lifespan, testing client
- [../13_deployment_infrastructure.md](../13_deployment_infrastructure.md) — environment topology and infra targets
- [../../CLAUDE.md](../../CLAUDE.md) — dev commands (`make dev`, pytest, alembic, celery)

## 4. Tasks

### 4.1 Repository layout
- [ ] Create all folders and empty `__init__.py` files per §2 of `19_backend_file_structure.md`.
- [ ] Add `pyproject.toml` with Python 3.12, FastAPI, SQLAlchemy 2.0, Celery, Alembic, Pydantic Settings, pytest, pytest-asyncio, httpx, ruff, mypy.
- [ ] Add `alembic.ini` wired to `libs/core/config.py` DB URL.
- [ ] Add `Makefile` with `dev`, `lint`, `typecheck`, `test` targets.
- [ ] Add `.python-version` pinning the interpreter.

### 4.2 Dev environment
- [ ] Write `docker-compose.yml` for Postgres 15, Redis 7, LocalStack (ses + sns), MailHog for webhook inspection.
- [ ] Write `infra/Dockerfile.api`, `Dockerfile.worker`, `Dockerfile.webhook`.
- [ ] Write `scripts/dev/seed_local_data.py` as an empty stub (filled later).
- [ ] Provide `.env.example` listing every variable used by `config.py`.

### 4.3 App skeletons
- [ ] `apps/api/main.py`: FastAPI app with lifespan + single `/healthz` route.
- [ ] `apps/webhook/main.py`: FastAPI app with `/healthz`.
- [ ] `apps/workers/celery_app.py`: Celery app wired to Redis broker/result backend.
- [ ] `apps/scheduler/beat.py`: Celery Beat entrypoint.

### 4.4 CI baseline
- [ ] GitHub Actions workflow running ruff + mypy + pytest on push.
- [ ] Coverage reporter set up; threshold is 0% initially (raised in Sprint 01).

## 5. Deliverables

- Runnable `make dev` that starts Postgres, Redis, LocalStack, API, webhook, worker, beat.
- `curl localhost:8000/healthz` and `curl localhost:8001/healthz` return `{"status": "ok"}`.
- CI green on an empty test suite.

## 6. Exit Criteria

- All folders from §2 of [../19_backend_file_structure.md](../19_backend_file_structure.md) exist on disk.
- Every app process starts without error under Docker Compose.
- Lint, typecheck, and test all pass in CI.
- `.env.example` documents every future environment variable touched by `config.py`.

## 7. Risks to Watch

- Windows path issues during local dev (forward slashes, long paths). Document WSL2 or Docker Desktop requirement in a `README_DEV.md`.
- LocalStack version drift from real SES behavior. Pin the LocalStack image version.
- Premature optimization of Dockerfiles — keep them plain multi-stage builds; tune later.

## 8. Tests to Run

- `pytest tests/` — trivial test that the health endpoints return 200.
- `make lint typecheck` — must pass.
