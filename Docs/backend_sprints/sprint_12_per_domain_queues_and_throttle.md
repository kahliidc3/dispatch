# Sprint 12 — Per-Domain Queues & Token Bucket Rate Limiting

**Phase:** Scale
**Estimated duration:** 1 week
**Branch:** `backend/sprint-12-per-domain-queues`
**Depends on:** Sprint 09

---

## 1. Purpose

Enable per-domain isolation of the send pipeline. One misbehaving domain must never starve or slow the rest of the platform — this is the structural foundation for per-domain circuit breakers in Sprint 13.

## 2. What Should Be Done

Introduce dynamic Celery queues named `send.<domain_name>`, route `send_message` tasks based on their domain, and enforce a Redis Lua token bucket *inside the task* to cap sends per domain per hour.

## 3. Docs to Follow

- [../11_operational_guardrails.md](../11_operational_guardrails.md) §9.2 Rate Limiting
- [../../CLAUDE.md](../../CLAUDE.md) — "Celery Queue Architecture" and "Rate Limiting"
- [../19_backend_file_structure.md](../19_backend_file_structure.md) — `libs/core/throttle/token_bucket.py`
- [../16_rollout_plan.md](../16_rollout_plan.md) §14.2 Phase 2

## 4. Tasks

### 4.1 Per-domain routing
- [ ] Replace the single `send` queue with dynamic `send.<domain_name>` routing via a custom `task_routes` callable that reads the message's `domain_id`.
- [ ] Scheduler or ops script spawns one worker per domain (or a worker pool consuming a dynamic set of queues).
- [ ] `scripts/ops/provision_domains.py`: spin up Celery worker config for each active domain.

### 4.2 Token bucket
- [ ] `libs/core/throttle/token_bucket.py`: Redis Lua script implementing a token bucket keyed by domain.
- [ ] Default: 150 sends/hour/domain; configurable per domain via `domains.rate_limit_per_hour`.
- [ ] Atomic `try_take(n=1)`; returns `(allowed, retry_after_seconds)`.

### 4.3 Integration with send task
- [ ] Call the bucket at the very start of `send_message` after idempotency check.
- [ ] If denied, re-enqueue with `countdown=retry_after` and exit.
- [ ] Do NOT use Celery's built-in `rate_limit` — it is per-worker, not per-domain.

### 4.4 Tuning
- [ ] `celery_app.conf.task_acks_late = True` (already set).
- [ ] `worker_prefetch_multiplier = 1`.
- [ ] Expose bucket metrics (tokens available, denials) via the metrics module.

## 5. Deliverables

- A burst of 10K sends against domain A does not delay sends on domain B.
- Per-domain rate limit changes take effect without a deploy.

## 6. Exit Criteria

- Load test: two domains at 10× and 1× their limits; denial pattern matches expected; no cross-contamination.
- Chaos test: restart the Redis container mid-run; bucket behavior degrades gracefully (fail-closed for affected domain).
- Integration test: changing a domain's `rate_limit_per_hour` is reflected in the next 60s.

## 7. Risks to Watch

- Bucket Lua script race conditions — keep the script tiny and tested against a reference implementation.
- Redis as a SPOF for sending. Fail-closed on Redis errors (pause sending) rather than fail-open.
- Queue explosion if domains churn. Garbage-collect idle queues nightly.

## 8. Tests to Run

- `pytest tests/unit/core/throttle/test_token_bucket.py`
- `pytest tests/integration/core/throttle/test_token_bucket_redis.py`
- `pytest tests/integration/workers/test_per_domain_routing.py`
