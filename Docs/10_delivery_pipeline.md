# Delivery Pipeline

---

## 8.1 Pre-Send Validation

Every send — whether from a campaign launch, an API call, or a drip step — passes through the same **seven-gate validation**. Failure at any gate routes the lead to a rejection record and does not consume send quota.

```
Gate 1: Format validation (regex + disposable domain blocklist)
Gate 2: SMTP validation (SES Email Validation API or ZeroBounce)
Gate 3: Role-account filter (info@, admin@, sales@, noreply@, etc.)
Gate 4: Suppression list check (Postgres suppression table)
Gate 5: SES account-level suppression cross-check
Gate 6: Spam trap heuristics (domain age, MX presence, historical patterns)
Gate 7: Pre-send ML spam scorer (reject if score > 0.2)
```

Gates 1–3 run at **contact ingestion** (import time). Gates 4–7 run at **send time**. This split is intentional: ingestion-time gates can be fixed with a better list; send-time gates reflect current state — a contact may have unsubscribed since import.

---

## 8.2 Queue & Throttle

The queue architecture uses **one Celery queue per sending domain**. This is the key decision that enables per-domain circuit breaking — a global queue would make per-domain pausing impossible without complex filtering.

```
Broker:           Redis (single cluster, HA replicated)
Queue naming:     send.{domain_name}
Rate enforcement: Redis-backed token bucket per domain
Worker pool:      scaled per queue depth (autoscaling)
Prefetch:         1 task per worker (task_acks_late=True)
Retry policy:     exponential backoff with jitter, max 3 retries
```

---

## 8.3 Send Execution

Each send task is **idempotent**. The task receives a `message_id` only — it reloads the full message from the database, checks its status, skips if already processed, and otherwise proceeds. This guarantees that retries and redeliveries never cause duplicate sends.

```python
def send_email(message_id, sender_domain):
    message = db.get(Message, message_id)
    if message.status != 'queued':
        return  # idempotency: already processed

    if not token_bucket.acquire(f'send:{sender_domain}'):
        raise SelfRetry()  # Celery will requeue with backoff

    if not circuit_breaker.is_closed(domain_id=message.domain_id):
        message.status = 'skipped'
        db.commit()
        return

    message.status = 'sending'
    db.commit()

    ses_message_id = ses_client.send(message)
    message.ses_message_id = ses_message_id
    message.status = 'sent'
    message.sent_at = now()
    db.commit()
```

---

## 8.4 Event Ingestion

SES emits events to the configuration-set event destination (SNS topic). The webhook receiver is a **dedicated service** — deployed separately from the API so that campaign-related API traffic cannot starve event ingestion.

- **Webhook receiver:** verifies SNS signature in < 20ms, enqueues raw payload, returns 200
- **Event worker:** parses payload, looks up message by `ses_message_id`, writes typed event row, writes suppression if needed
- **Rolling metrics worker:** updates `rolling_metrics` every 5 minutes per scope
- **Circuit breaker evaluator:** reads `rolling_metrics` every 60 seconds, trips/resets breakers
- All raw SNS payloads archived to S3 via Kinesis Firehose for compliance and replay
