# FastAPI Documentation Notes (Project-Oriented)

This document summarizes the official FastAPI docs with a focus on how we should implement the API layer for dispatch.

## 1. Installation and Local Run

- Create and activate a Python virtual environment.
- Install FastAPI with standard extras:
  - `pip install "fastapi[standard]"`
- For local development, run the app with:
  - `fastapi dev`

## 2. Core API Patterns

- Use typed path parameters for strict validation and clear docs.
- Use query parameters for filtering, pagination, and optional flags.
- Use Pydantic models (`BaseModel`) for request bodies and response schemas.
- Prefer explicit response models for stable API contracts.

These patterns generate OpenAPI docs automatically and keep validation close to the route contract.

## 3. Dependency Injection

- Use `Depends(...)` for reusable cross-cutting concerns:
  - auth context
  - DB session/session factory
  - permission checks
  - shared pagination/sorting params
- Prefer `Annotated[..., Depends(...)]` style where possible.
- Use dependency layers (sub-dependencies) to keep routes thin.
- For setup/cleanup behavior around dependencies, use dependencies with `yield`.

## 4. Security Baseline

- Implement API auth using FastAPI security utilities and OpenAPI security schemes.
- Keep OAuth2/JWT flows in dedicated security modules, not inline in routes.
- Enforce HTTPS in deployed environments (required for secure OAuth2 usage).
- Separate user-facing session auth (web UI) from machine-to-machine API key/JWT flows.

## 5. Lifecycle and Startup

- Use lifespan handlers (`FastAPI(lifespan=...)`) for startup/shutdown resources:
  - DB pool initialization
  - Redis connections
  - ML model loading/unloading
  - warm caches
- Keep expensive initialization out of request handlers.

## 6. Error Handling

- Raise typed domain errors in services.
- Map errors centrally in global exception handlers.
- Avoid route-level try/except for business errors unless transforming external failures.
- Ensure all errors return stable machine-readable payloads for frontend and worker consumers.

## 7. Testing

- Use `fastapi.testclient.TestClient` for API tests.
- Use `pytest` as the standard runner.
- Start with:
  - route contract tests (status codes + payloads)
  - service tests for business rules
  - integration tests for DB-backed flows
- Keep test names explicit and endpoint-focused.

## 8. Deployment Guidance

- For VM-style deployments, use Uvicorn/FastAPI workers via `--workers`.
- In container orchestrators (e.g., Kubernetes/ECS patterns with one process/container), typically run one Uvicorn process per container and scale at the orchestrator level.
- For Docker images, prefer building your own image from scratch for the app.
- Do not rely on deprecated legacy base images.

## 9. dispatch-Specific Conventions

- Routes should only orchestrate:
  1. input validation
  2. actor resolution
  3. service call
  4. response mapping
- Business rules stay in service layer modules.
- Repositories stay CRUD-oriented and side-effect free.
- Maintain idempotency on endpoints that can be retried from UI, workers, or webhooks.

## 10. Suggested Initial FastAPI Module Skeleton

```text
apps/api/
  main.py
  deps.py
  exception_handlers.py
  routers/
    auth.py
    campaigns.py
    contacts.py
    suppression.py
libs/core/
  <domain>/
    models.py
    schemas.py
    repository.py
    service.py
```

## Official References

- FastAPI Tutorial (User Guide): https://fastapi.tiangolo.com/tutorial/
- Path Parameters: https://fastapi.tiangolo.com/tutorial/path-params/
- Query Parameters: https://fastapi.tiangolo.com/tutorial/query-params/
- Request Body (Pydantic models): https://fastapi.tiangolo.com/tutorial/body/
- Dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
- Security: https://fastapi.tiangolo.com/tutorial/security/
- Testing: https://fastapi.tiangolo.com/tutorial/testing/
- Lifespan Events: https://fastapi.tiangolo.com/advanced/events/
- Deployment Workers: https://fastapi.tiangolo.com/deployment/server-workers/
- Deployment with Docker: https://fastapi.tiangolo.com/deployment/docker/

