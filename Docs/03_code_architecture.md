# Acmemail — Code Architecture & Engineering Standards

**Version:** 1.0
**Audience:** Platform engineers building and maintaining the system
**Scope:** Monorepo structure, service boundaries, naming, testing, error handling, operational code patterns

---

## 1. Principles (Non-Negotiable)

These govern every engineering decision. If a proposal violates one, it is rejected.

1. **Boring technology by default.** Python/FastAPI, PostgreSQL, Redis, Celery. We do not adopt new databases, frameworks, or languages without a written ADR showing the existing stack cannot meet the requirement.
2. **The database is the source of truth.** No state lives only in memory, only in Redis, or only in logs. Redis holds caches and queues. Logs are observational. Postgres is canonical.
3. **Every write goes through a service.** Controllers (FastAPI routes) do not call the ORM directly. They call service functions that encapsulate business rules.
4. **Idempotency by default.** Any handler that can be retried (queue workers, webhooks, API calls with `Idempotency-Key`) must produce the same result when called twice with the same input.
5. **Fail closed, not open.** When a circuit breaker, rate limiter, or health check cannot determine status, the default is to pause sending — not to let traffic through.
6. **No silent catches.** Exceptions are either handled with explicit recovery logic or re-raised after logging. `try: ... except: pass` is forbidden outside of explicitly documented cleanup paths.
7. **Tests are part of the feature.** Pull requests without tests are not merged. Tests include unit, integration against a real Postgres, and contract tests against mocked SES/SNS.

---

## 2. Tech Stack

| Layer              | Choice                              | Rationale                                              |
|--------------------|-------------------------------------|--------------------------------------------------------|
| Language           | Python 3.12                         | Team familiarity, rich ML ecosystem                    |
| API framework      | FastAPI                             | Async-native, Pydantic integration, OpenAPI            |
| ORM                | SQLAlchemy 2.0 (async)              | Mature, works with async FastAPI                       |
| Migrations         | Alembic                             | Standard for SQLAlchemy                                |
| Queue              | Celery + Redis broker               | Known, mature, Khalid's existing stack                 |
| Task scheduling    | Celery Beat                         | Integrated with Celery                                 |
| Cache              | Redis                               | Same Redis instance as broker                          |
| Database           | PostgreSQL 15+                      | JSONB, generated columns, partitioning                 |
| Object storage     | S3                                  | Raw CSVs, inbound email MIME, event archive            |
| Event bus          | AWS SNS                             | SES-native event delivery                              |
| IaC                | Terraform                           | DNS, SES, SNS, VPC, IAM                                |
| Container runtime  | Docker + ECS Fargate                | Managed, scales per queue                              |
| Frontend           | Next.js 16 + TypeScript 5           | Team familiarity                                       |
| UI library         | shadcn/ui + Tailwind                | Unopinionated, fast to build                           |
| Auth               | Sessions (backend) + JWT (API)      | Sessions for UI, JWT for machine-to-machine           |
| Observability      | Datadog (metrics, logs, APM)        | Single pane                                            |
| Secrets            | AWS Secrets Manager                 | Rotating credentials                                   |

---

## 3. Monorepo Layout

```
acmemail/
├── apps/
│   ├── api/                    # FastAPI app (public + internal endpoints)
│   ├── workers/                # Celery workers (send, event, import, warmup)
│   ├── webhook/                # SNS webhook receiver (separate deploy)
│   ├── scheduler/              # Celery Beat + cron tasks
│   └── web/                    # Next.js UI
├── libs/
│   ├── core/                   # Shared domain models, services
│   ├── ses_client/             # Thin SES wrapper with idempotency + retries
│   ├── dns_provisioner/        # Cloudflare/Route53 adapters
│   ├── ml/                     # Feature store, scorers, classifiers
│   └── schemas/                # Pydantic models shared across apps
├── infra/
│   ├── terraform/              # All IaC
│   ├── docker/                 # Dockerfiles
│   └── k8s/                    # (future) Kubernetes manifests
├── migrations/                 # Alembic
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── adr/                    # Architecture Decision Records
│   ├── runbooks/               # On-call procedures
│   └── api/                    # OpenAPI specs
├── scripts/                    # Operational scripts (provision, seed, migrate)
├── pyproject.toml
├── docker-compose.yml          # Local dev
└── Makefile                    # Common commands
```

### 3.1 Import Discipline

- `apps/*` can import from `libs/*` but never from each other.
- `libs/core` is the only lib that imports from the schema. No other lib may.
- No circular imports. Enforced by `ruff` rule `E402` and `import-linter`.

---

## 4. Service Layer Pattern

Every domain has three files:

```
libs/core/campaigns/
├── models.py         # SQLAlchemy ORM models (one per table)
├── schemas.py        # Pydantic DTOs for API inputs/outputs
├── service.py        # Business logic — the only place rules live
└── repository.py     # DB queries — pure CRUD, no business logic
```

### Example — `libs/core/campaigns/service.py`

```python
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

from libs.core.campaigns.repository import CampaignRepository
from libs.core.sender_profiles.repository import SenderProfileRepository
from libs.core.domains.repository import DomainRepository
from libs.core.suppression.repository import SuppressionRepository
from libs.core.errors import (
    CampaignValidationError,
    DomainNotHealthyError,
    SenderProfilePausedError,
)


@dataclass
class LaunchCampaignCommand:
    campaign_id: UUID
    launched_by: UUID
    launched_at: datetime


class CampaignService:
    """All campaign-related business rules live here.
    Routes and workers call this — never the repository directly."""

    def __init__(
        self,
        campaigns: CampaignRepository,
        sender_profiles: SenderProfileRepository,
        domains: DomainRepository,
        suppression: SuppressionRepository,
    ) -> None:
        self.campaigns = campaigns
        self.sender_profiles = sender_profiles
        self.domains = domains
        self.suppression = suppression

    async def launch(self, cmd: LaunchCampaignCommand) -> None:
        campaign = await self.campaigns.get_or_raise(cmd.campaign_id)

        # Rule 1: campaign must be in draft or scheduled state
        if campaign.status not in ("draft", "scheduled"):
            raise CampaignValidationError(
                f"Cannot launch campaign in state: {campaign.status}"
            )

        # Rule 2: sender profile must be active and not paused
        profile = await self.sender_profiles.get_or_raise(campaign.sender_profile_id)
        if not profile.is_active or profile.paused_at is not None:
            raise SenderProfilePausedError(profile.id)

        # Rule 3: domain must be verified and not burnt
        domain = await self.domains.get_or_raise(profile.domain_id)
        if domain.verification_status != "verified":
            raise DomainNotHealthyError(f"Domain {domain.name} not verified")
        if domain.reputation_status in ("burnt", "retired"):
            raise DomainNotHealthyError(
                f"Domain {domain.name} reputation: {domain.reputation_status}"
            )

        # Rule 4: within daily send cap
        if profile.daily_send_count >= profile.daily_send_limit:
            raise CampaignValidationError("Sender profile daily limit reached")

        # All validations pass — transition state atomically
        await self.campaigns.mark_running(
            campaign_id=campaign.id,
            started_at=cmd.launched_at,
            launched_by=cmd.launched_by,
        )
```

### Why This Shape

- **Repositories** are boring CRUD. They can be swapped (e.g., a test fake) without changing business rules.
- **Services** are injectable. Routes construct them with repositories. Workers construct them the same way.
- **Commands** (dataclasses) are the unit of intent. They encode what was asked, not how to do it. Audit log, validation, retry — all operate on commands.
- **Errors** are typed. Routes map exceptions to HTTP status codes in one place.

---

## 5. FastAPI Route Conventions

Routes are thin. Their job is: (1) validate input, (2) resolve the actor, (3) call a service, (4) map the result to a response.

```python
# apps/api/routers/campaigns.py
from fastapi import APIRouter, Depends, status
from uuid import UUID

from apps.api.deps import get_current_user, get_campaign_service
from libs.core.campaigns.service import CampaignService, LaunchCampaignCommand
from libs.core.campaigns.schemas import CampaignResponse
from libs.core.users.models import User

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post(
    "/{campaign_id}/launch",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=CampaignResponse,
)
async def launch_campaign(
    campaign_id: UUID,
    user: User = Depends(get_current_user),
    service: CampaignService = Depends(get_campaign_service),
) -> CampaignResponse:
    cmd = LaunchCampaignCommand(
        campaign_id=campaign_id,
        launched_by=user.id,
        launched_at=datetime.now(UTC),
    )
    await service.launch(cmd)
    return await service.get_response(campaign_id)
```

### Error Mapping (Global)

```python
# apps/api/exception_handlers.py
@app.exception_handler(CampaignValidationError)
async def campaign_validation_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "campaign_validation", "message": str(exc)},
    )
```

Every typed error maps to one HTTP status in one place. Routes never catch domain exceptions.

---

## 6. Celery Worker Patterns

### 6.1 One Queue Per Domain (for Sending)

```python
# apps/workers/send.py
from celery import Celery

celery_app = Celery("send", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.task_routes = {
    "send.outbound.*": lambda task, args, kwargs, options: {
        "queue": f"send.{kwargs['sender_domain']}"
    },
}

celery_app.conf.task_acks_late = True        # Don't ack until complete
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.worker_prefetch_multiplier = 1  # Fairness across domains


@celery_app.task(
    name="send.outbound.email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(SESThrottledError,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def send_email(self, message_id: str, sender_domain: str) -> None:
    # Idempotency: check current status first
    with session_scope() as session:
        message = session.get(Message, message_id)
        if message.status != "queued":
            logger.info("Skipping already-processed message", message_id=message_id)
            return
        message.status = "sending"

    try:
        ses_message_id = ses_client.send(message)
        with session_scope() as session:
            message = session.get(Message, message_id)
            message.ses_message_id = ses_message_id
            message.status = "sent"
            message.sent_at = datetime.now(UTC)
    except SESHardError as e:
        with session_scope() as session:
            message = session.get(Message, message_id)
            message.status = "failed"
            message.error_code = e.code
            message.error_message = str(e)
        raise
```

### 6.2 Idempotency Rules

- Every task accepts its target entity ID, not the full entity.
- First thing every task does: reload entity, check state, skip if already processed.
- Status transitions are one-way where possible: `queued → sending → sent|failed`.
- Tasks never mutate state they depend on in a loop — if state must transition, it happens in a single `UPDATE ... WHERE status = expected`.

### 6.3 Rate Limiting (Leaky Bucket)

Rate limits are enforced **inside the task**, not by Celery's native `rate_limit` (which doesn't support per-domain).

```python
# libs/core/throttle/token_bucket.py
import time
import redis

async def acquire_token(
    redis_client: redis.Redis,
    key: str,
    refill_per_second: float,
    capacity: int,
) -> bool:
    """Returns True if a token was acquired. Otherwise False — caller must wait/retry."""
    now = time.time()
    lua = """
    local tokens = tonumber(redis.call('HGET', KEYS[1], 'tokens') or ARGV[1])
    local last = tonumber(redis.call('HGET', KEYS[1], 'last') or ARGV[2])
    local elapsed = tonumber(ARGV[2]) - last
    tokens = math.min(tonumber(ARGV[1]), tokens + elapsed * tonumber(ARGV[3]))
    if tokens >= 1 then
        tokens = tokens - 1
        redis.call('HMSET', KEYS[1], 'tokens', tokens, 'last', ARGV[2])
        redis.call('EXPIRE', KEYS[1], 3600)
        return 1
    end
    redis.call('HMSET', KEYS[1], 'tokens', tokens, 'last', ARGV[2])
    return 0
    """
    result = await redis_client.eval(lua, 1, key, capacity, now, refill_per_second)
    return bool(result)
```

---

## 7. Database Access Patterns

### 7.1 Transactions Are Explicit

```python
async with session.begin():
    # Everything here is one transaction
    await repo.create_campaign(...)
    await repo.write_audit_log(...)
```

No implicit transactions. No "auto-commit." If a service method needs to write, it either accepts a session or creates one explicitly.

### 7.2 N+1 Prevention

Every query over a list of entities must either (a) eager-load relationships with `selectinload` or (b) be explicitly documented as per-item lookup. Linting enforces `.all()` on joined queries.

### 7.3 Pagination

All list endpoints use **cursor-based pagination** with `(created_at DESC, id DESC)`. Offset pagination is forbidden on tables > 100k rows.

```python
WHERE (created_at, id) < (:cursor_time, :cursor_id)
ORDER BY created_at DESC, id DESC
LIMIT 50
```

### 7.4 Soft Delete

Only specific tables soft-delete: `contacts`, `campaigns`, `users`. Events, messages, and audit rows are immutable — never deleted, only archived.

---

## 8. SES Client Wrapper

Direct `boto3.ses` calls are forbidden. All SES calls go through `libs/ses_client`. This centralizes:

- Idempotency token generation
- Retry policy (exponential backoff with jitter)
- Error classification (`SESHardError` vs `SESTransientError` vs `SESThrottledError`)
- Metrics emission
- Cost tracking

```python
# libs/ses_client/client.py
class SESClient:
    async def send(self, message: Message) -> str:
        """Returns SES message id. Raises typed errors on failure."""
        idempotency_key = self._make_idempotency_key(message)
        try:
            response = await self._send_with_retry(message, idempotency_key)
        except ClientError as e:
            raise self._classify_error(e) from e

        self._emit_metrics(message, response)
        return response["MessageId"]
```

---

## 9. Testing Strategy

### 9.1 Test Pyramid

- **Unit tests (70%):** pure functions, validators, serializers, spam scorer features. No DB, no network.
- **Integration tests (25%):** services against a real Postgres in a Docker container, real Redis. SES is mocked with a contract-level fake.
- **End-to-end tests (5%):** full request through FastAPI → Celery → fake SES → webhook. Uses LocalStack for SES/SNS/S3.

### 9.2 Test Data

- Fixtures are Python functions (`@pytest.fixture`), not JSON files.
- Every test creates exactly the data it needs; no shared state between tests.
- The test database is wiped between each test via transaction rollback.

### 9.3 Critical Path Coverage

These code paths require 95%+ line coverage (enforced in CI):

- `libs/core/suppression/*`
- `libs/core/circuit_breaker/*`
- `libs/core/campaigns/service.py` (launch, pause)
- `apps/webhook/handlers.py`
- `libs/ses_client/client.py`

---

## 10. Error Handling

### 10.1 Error Taxonomy

```python
# libs/core/errors.py
class AcmemailError(Exception):
    """Base — all custom errors inherit from this."""

class ValidationError(AcmemailError):
    """400-class. User input issue."""

class AuthorizationError(AcmemailError):
    """403. Actor not allowed."""

class NotFoundError(AcmemailError):
    """404. Resource does not exist."""

class ConflictError(AcmemailError):
    """409. State machine violation."""

class ExternalServiceError(AcmemailError):
    """502. Downstream (SES, DNS provider) failed."""

class RateLimitedError(AcmemailError):
    """429. Throttled by limiter."""
```

### 10.2 Logging

Every log line is **structured JSON** with these required fields: `timestamp`, `level`, `trace_id`, `event`. Use `structlog`.

```python
logger.info(
    "campaign.launched",
    campaign_id=campaign.id,
    segment_size=eligible_count,
    sender_profile_id=profile.id,
    domain=profile.from_email.split("@")[1],
)
```

Never log: passwords, API keys, full email addresses of contacts (log hashes), full bodies.

---

## 11. Configuration Management

All configuration comes from environment variables, loaded once at startup via Pydantic `BaseSettings`:

```python
# libs/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str

    # SES
    ses_region: str = "us-east-1"
    ses_sns_topic_arn: str

    # Thresholds (tunable per-env)
    bounce_rate_alarm: float = 0.015
    complaint_rate_alarm: float = 0.0005

    # Feature flags
    ml_scorer_enabled: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

No `os.getenv()` scattered through code. No config singletons accessed at import time (breaks testing).

---

## 12. Deployment Contract

Every service exposes three HTTP endpoints:

- `GET /healthz` — process is alive
- `GET /readyz` — can serve traffic (DB, Redis, SES reachable)
- `GET /metrics` — Prometheus format

Every service emits the same structured logs. Every service has the same Dockerfile pattern. Every service is deployed via the same Terraform module — only parameters differ.

---

## 13. Code Review Checklist

Before approving a PR, every reviewer confirms:

- [ ] Business rules live in `libs/core/*/service.py`, not in routes or workers
- [ ] Database writes happen inside an explicit transaction
- [ ] Any new task is idempotent and has a status check on entry
- [ ] No `print`, `logging.info` without structured context, or `time.sleep` in production code
- [ ] Errors are typed and mapped to HTTP codes in the global handler
- [ ] Tests cover the happy path and at least one failure mode
- [ ] No new environment variable without a default and a doc comment
- [ ] Migrations have both `upgrade` and `downgrade` (where possible)
- [ ] No secrets, API keys, or contact PII in logs

---

## 14. Architecture Decision Records (ADRs)

Every significant technical decision requires a written ADR in `docs/adr/`. Template:

```
# ADR-XXX: Title

## Status
Proposed | Accepted | Superseded by ADR-YYY

## Context
What problem are we solving? What constraints matter?

## Decision
What did we decide?

## Consequences
What do we gain? What do we lose? What becomes harder?

## Alternatives Considered
What did we reject and why?
```

ADRs are immutable once accepted. Changing a decision means writing a new ADR that supersedes the old one.

---

*End of Code Architecture Guide*
