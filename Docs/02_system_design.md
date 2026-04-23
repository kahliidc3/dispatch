# System Design Document
## dispatch · High-Volume Email Platform

> Architecture, data model, delivery pipeline, operational guardrails, and ML services for a platform targeting 1M+ sends/day.

**Version:** 1.0  
**Team:** Platform Engineering  
**Date:** April 2026  
**Classification:** Confidential — Internal Platform Documentation

---

## Contents

1. [Executive Summary](#1-executive-summary)
2. [Goals & Non-Goals](#2-goals--non-goals)
   - 2.1 [Functional Goals](#21-functional-goals)
   - 2.2 [Non-Functional Goals (SLOs)](#22-non-functional-goals-slos)
   - 2.3 [Non-Goals](#23-non-goals)
3. [System Context](#3-system-context)
   - 3.1 [Actors](#31-actors)
   - 3.2 [External Systems](#32-external-systems)
   - 3.3 [Data Flows Overview](#33-data-flows-overview)
4. [High-Level Architecture](#4-high-level-architecture)
   - 4.1 [Component Map](#41-component-map)
   - 4.2 [Request Lifecycle — Campaign Launch](#42-request-lifecycle--campaign-launch)
   - 4.3 [Event Lifecycle — Bounce Processing](#43-event-lifecycle--bounce-processing)
5. [Functional Requirements](#5-functional-requirements)
   - 5.1 [Domain & Sender Management](#51-domain--sender-management)
   - 5.2 [Contact & List Management](#52-contact--list-management)
   - 5.3 [Campaign Authoring & Launch](#53-campaign-authoring--launch)
   - 5.4 [Suppression & Compliance](#54-suppression--compliance)
   - 5.5 [Analytics](#55-analytics)
6. [Non-Functional Requirements](#6-non-functional-requirements)
   - 6.1 [Performance Targets](#61-performance-targets)
   - 6.2 [Availability](#62-availability)
   - 6.3 [Durability](#63-durability)
   - 6.4 [Security](#64-security)
   - 6.5 [Compliance](#65-compliance)
7. [Data Model](#7-data-model)
   - 7.1 [Schema Overview](#71-schema-overview)
   - 7.2 [Critical Invariants](#72-critical-invariants)
   - 7.3 [Partitioning Strategy](#73-partitioning-strategy)
8. [Delivery Pipeline](#8-delivery-pipeline)
   - 8.1 [Pre-Send Validation](#81-pre-send-validation)
   - 8.2 [Queue & Throttle](#82-queue--throttle)
   - 8.3 [Send Execution](#83-send-execution)
   - 8.4 [Event Ingestion](#84-event-ingestion)
9. [Operational Guardrails](#9-operational-guardrails)
   - 9.1 [Circuit Breakers](#91-circuit-breakers)
   - 9.2 [Rate Limiting](#92-rate-limiting)
10. [ML Services](#10-ml-services)
    - 10.1 [Pre-Send Spam Scorer (Model 1)](#101-pre-send-spam-scorer-model-1)
    - 10.2 [Reply Intent Classifier (Model 2)](#102-reply-intent-classifier-model-2)
    - 10.3 [Anomaly Detection](#103-anomaly-detection)
    - 10.4 [Send-Time Optimization](#104-send-time-optimization)
11. [Deployment & Infrastructure](#11-deployment--infrastructure)
    - 11.1 [AWS Topology](#111-aws-topology)
    - 11.2 [Environments](#112-environments)
    - 11.3 [Infrastructure as Code](#113-infrastructure-as-code)
12. [Security](#12-security)
    - 12.1 [Authentication & Authorization](#121-authentication--authorization)
    - 12.2 [Secrets Management](#122-secrets-management)
    - 12.3 [Data Protection](#123-data-protection)
13. [Observability](#13-observability)
    - 13.1 [Metrics](#131-metrics)
    - 13.2 [Logging](#132-logging)
    - 13.3 [Tracing](#133-tracing)
    - 13.4 [Alerting](#134-alerting)
14. [Rollout Plan](#14-rollout-plan)
    - 14.1 [Phase 1 — MVP](#141-phase-1--mvp-months-13)
    - 14.2 [Phase 2 — Scale](#142-phase-2--scale-months-35)
    - 14.3 [Phase 3 — ML](#143-phase-3--ml-months-58)
    - 14.4 [Phase 4 — 1M/Day](#144-phase-4--1mday-months-812)
15. [Open Questions & Future Work](#15-open-questions--future-work)
- [Appendix A — API Surface Overview](#appendix-a--api-surface-overview)
- [Appendix B — Glossary](#appendix-b--glossary)

---

## 1. Executive Summary

dispatch is an internal email platform designed to send one million or more emails per day while maintaining inbox placement rates comparable to best-in-class ESPs. The platform is composed of two halves: a **control plane we build** (contacts, imports, segmentation, sender profiles, templates, campaigns, suppression, analytics, ML) and a **delivery plane we rent** (AWS SES as the sole sending backbone).

The architectural thesis is that inbox placement at scale is not a configuration problem — it is an **operational discipline problem**. Authentication, clean infrastructure, and correct SMTP headers are necessary but insufficient. The decisive signals are recipient behavior, complaint rate, bounce rate, unsubscribe friction, rate pattern, and list quality. The system therefore invests heavily in automated throttling, immediate suppression, event-driven circuit breakers, and stop conditions that pause sending before account health degrades.

This document covers:

- The end-to-end system architecture and component responsibilities
- The complete data model (39 tables, covered in detail in the companion SQL file)
- The delivery pipeline from lead ingestion to SES send to event processing
- Operational guardrails that make the system self-protecting
- ML services that improve decisions over time
- Deployment architecture, security, and observability
- A phased rollout plan from MVP to 1M sends/day

> **Note:** This document is paired with three companion documents: the SQL schema (`01_schema.sql`), the code architecture guide (`03_code_architecture.md`), and the operations runbook (`04_operations_runbook.md`). Together they form the complete platform specification.

---

## 2. Goals & Non-Goals

Scope discipline is a deliverability control in itself. A system that tries to do everything does each thing poorly. The scope below is deliberately narrow.

### 2.1 Functional Goals

- Manage sending domains, quotas, and domain pools for internal high-volume use
- Provision, warm up, and rotate a large pool of sending domains automatically
- Ingest contact lists from CSV, API, or direct integration with provenance preserved
- Author, schedule, launch, pause, and resume campaigns from a web UI
- Validate each sender profile before every send against domain and policy state
- Route sends through a per-domain queue with leaky-bucket throttling
- Capture every SES event and update suppression + reputation state in real time
- Automatically pause sending at the domain, IP pool, or account level when health degrades
- Provide dashboards and reporting on campaign performance and deliverability health
- Score outbound content with a pre-send spam risk model
- Classify inbound replies by intent and act on them automatically

### 2.2 Non-Functional Goals (SLOs)

| Category | Target | Measurement window |
|---|---|---|
| API p99 latency | < 400 ms | 5-minute rolling |
| API availability | 99.95% | Monthly |
| Send queue lag (enqueue→send) | < 30 seconds | p95 over 1h |
| Event processing lag (SES→DB) | < 5 seconds | p95 over 1h |
| Suppression list update latency | < 10 seconds after event | p99 |
| Durability (once accepted by SES) | 99.999999999% | Always |
| Data loss RPO | ≤ 1 hour | Always |
| Recovery RTO | ≤ 4 hours | Always |

### 2.3 Non-Goals

- **Multi-region active-active** — single region (`us-east-1`) with DR to `us-west-2`
- **Inline email builder** — plain text primary, HTML imported not authored
- **Transactional email use case** — platform optimized for outreach/newsletter
- **BYOD (Bring Your Own Domain that we did not provision)** — removes control
- **SMTP relay API** — the public API is HTTPS/JSON only
- **Delivery to unauthenticated recipients** — every send requires a resolved contact record

---

## 3. System Context

### 3.1 Actors

| Actor | Role | Primary interaction |
|---|---|---|
| Operator | Internal user managing campaigns | Web UI |
| Recipient | Email recipient | Receives email, clicks link, replies, unsubscribes |
| On-call engineer | Platform SRE | Runbooks, dashboards, alerts |
| Admin | Platform owner | Platform management, global controls |

### 3.2 External Systems

| System | Purpose | Integration |
|---|---|---|
| AWS SES | Primary (and sole) sending backbone | boto3 API + SNS events |
| Cloudflare DNS | DNS provisioning for sending domains | Cloudflare API |
| AWS Route 53 | DNS for root company domain | boto3 |
| Google Postmaster Tools | Gmail reputation monitoring | Postmaster API |
| Microsoft SNDS | Outlook IP reputation monitoring | Scraped + manual |
| ZeroBounce / SES Validation | Email address verification | HTTP API |
| S3 | CSV storage, inbound MIME, event archive | boto3 |
| Datadog | Metrics, logs, APM, alerting | Agent + API |
| PagerDuty | On-call routing | Webhook |

### 3.3 Data Flows Overview

Five primary data flows carry the bulk of system activity:

- **Provisioning flow:** Operator adds domain → Cloudflare DNS records created → SES identity verified → warmup rotation enrolled.
- **Ingestion flow:** CSV upload → S3 → import worker parses, validates, deduplicates → contacts upserted with provenance → suppression check → list membership applied.
- **Campaign flow:** Operator authors campaign → launch validates sender profile + domain health → segment evaluated → snapshot frozen → batches enqueued → workers drain per-domain.
- **Event flow:** SES fires event → SNS delivers to webhook → event queued → event worker parses → message updated → suppression written → rolling metrics updated → circuit breakers evaluated.
- **Reply flow:** Inbound email → SES inbound → S3 → Lambda → reply classifier → action taken (suppress, route to CRM, re-queue).

---

## 4. High-Level Architecture

### 4.1 Component Map

The platform decomposes into six logical layers. Each layer has a single primary responsibility and a defined contract with adjacent layers.

| Layer | Components | Primary responsibility | Tech |
|---|---|---|---|
| Presentation | Web UI, docs site | Operator-facing control surface | Next.js, Tailwind |
| API | REST endpoints, webhook receiver | Input validation, auth, request routing | FastAPI |
| Domain (core) | Services: identity, contacts, campaigns, suppression, analytics | Business rules and orchestration | Python |
| Execution | Send workers, event workers, import workers, scheduler | Async processing, retries, throttling | Celery + Redis |
| Delivery | SES (via abstraction layer) | Message acceptance, SMTP transport, event emission | boto3 |
| Data | Postgres, S3, Redis | State, blob storage, cache | RDS, S3, ElastiCache |

### 4.2 Request Lifecycle — Campaign Launch

```
1.  Operator hits POST /api/v1/campaigns/:id/launch from the web UI
2.  API validates session, loads CampaignService
3.  Service checks: campaign state, sender profile state, domain health,
    suppression list freshness, daily quota not exceeded
4.  Service transitions campaign to 'running' (atomic SQL UPDATE)
5.  Service enqueues 'campaign.evaluate_segment' task to Celery
6.  API returns 202 with campaign_id and run_id

Asynchronously:
7.  Segment worker resolves eligible contacts via segments engine
8.  Worker writes segment_snapshots rows (included=true for eligible,
    included=false with exclusion_reason for skipped)
9.  Worker creates send_batches in chunks of 500 contacts each
10. Worker fans out 'send.outbound.email' tasks to per-domain queues
11. Send workers drain per-domain queues at rate-limited pace
12. Each task: re-reads message row, checks status, acquires token
    from leaky bucket, calls SES, updates message with ses_message_id
```

### 4.3 Event Lifecycle — Bounce Processing

```
1. SES attempts delivery, receives 550 hard bounce from receiving MTA
2. SES emits Bounce event to configuration-set event destination (SNS)
3. SNS POSTs signed payload to /webhook/ses/bounce
4. Webhook receiver: verifies SNS signature, acks within 100ms,
   pushes raw payload to 'events.ses.incoming' Celery queue
5. Event worker dequeues, identifies event type = Bounce
6. Worker: upserts bounce_events row, updates messages.status='bounced',
   writes suppression_entry (reason='hard_bounce'), publishes metric
7. Rolling metrics worker (separate task) updates rolling_metrics
   for domain + ip_pool + account, window = 1h/6h/24h
8. Circuit breaker evaluator (runs every 60s) reads rolling_metrics,
   trips breaker if thresholds exceeded, pauses affected queues
```

---

## 5. Functional Requirements

### 5.1 Domain & Sender Management

- **Automated domain provisioning:** operator requests N domains, system creates DNS records in Cloudflare, initializes SES identity, enrolls in warmup schedule
- **Continuous warmup:** every active domain has its send count ramped over 4–8 weeks per the warmup schedule (defined in operations runbook)
- **Domain retirement:** when reputation drops below thresholds, domain is marked burnt and removed from rotation automatically
- **Sender profile management:** each domain hosts multiple sender profiles (From address + display name + reply-to) tied to a configuration set
- **Per-profile daily limits:** enforced by rate limiter, reset nightly
- **Sender validation:** every send runs the pre-flight check listed in §8.1

### 5.2 Contact & List Management

- Contacts are keyed by `email` with case-insensitive matching
- Every contact has provenance: at least one `contact_sources` row identifying how they entered the system
- CSV import preserves the raw row (`import_rows.raw_data`) indefinitely for audit
- Contact validation runs asynchronously, updating `validation_status` and `validation_score`
- Lifecycle status (`active`, `bounced`, `complained`, `unsubscribed`, `suppressed`, `deleted`) is the authoritative enrollment state
- Lists are explicit memberships; segments are query-based and evaluated at campaign launch
- Custom attributes live in `contacts.custom_attributes` (JSONB) — no schema migration for new fields

### 5.3 Campaign Authoring & Launch

- Operator selects: sender profile, template version, list or segment, schedule, rate limit
- Launch is a two-phase operation: validation gate → segment snapshot → batch enqueue
- Segment snapshots are frozen at launch — subsequent contact changes do not affect in-flight campaigns
- Campaigns can be paused at any point; pause is immediate (workers check status before each send)
- Resuming a paused campaign continues from the last unsent batch
- Campaign-level rate limit (`send_rate_per_hour`) is enforced per-campaign AND per-domain
- Every campaign send is recorded in `messages` with a stable `campaign_id` reference

### 5.4 Suppression & Compliance

- Suppression is platform-wide. An unsubscribe from any campaign blocks all future sends to that address
- Hard bounces trigger immediate suppression with `reason='hard_bounce'`
- Soft bounces increment a counter; at threshold (3 in 30 days), suppression is applied with `reason='soft_bounce_limit'`
- Complaints trigger immediate suppression with `reason='complaint'`
- One-click unsubscribe (RFC 8058) headers are added to every outbound email
- Unsubscribe endpoint processes POST and returns 200 within 200ms; no user interaction required
- Suppression lookups happen twice: at segment evaluation (batch filter) and at send time (per-message final check)
- Suppression list is also synced to AWS SES account-level suppression as a secondary safety layer

### 5.5 Analytics

- Real-time campaign dashboards: sends, deliveries, bounces, complaints, opens, clicks, replies, unsubscribes
- Rolling health metrics per domain, IP pool, sender profile, and account
- Google Postmaster reputation ingested daily via API and surfaced alongside internal metrics
- Seed test results (Glockapps / MailReach) integrated into the health dashboard
- Export: all raw event data available via a read-only BI-friendly view (for Metabase, Looker, etc.)

---

## 6. Non-Functional Requirements

### 6.1 Performance Targets

| Dimension | Target | Notes |
|---|---|---|
| API read p99 | < 200 ms | Single-entity lookups |
| API list p99 | < 400 ms | Paginated lists, ≤ 50 items |
| API write p99 | < 500 ms | Exclude async work |
| Send throughput (per domain) | ≤ 2,500/day, ≤ 150/hour | Enforced by rate limiter |
| Aggregate send throughput | 1,000,000/day target | Across all domains |
| Event ingestion throughput | ≥ 5,000 events/sec | Peak, during campaign send |
| Webhook ack time | < 100 ms | SNS requires fast ack |
| Circuit breaker evaluation interval | 60 seconds | Acceptable lag before pause |

### 6.2 Availability

The system is designed for **99.95% availability** on the control plane (API, UI, admin). The send path has a higher bar: loss of send capability has direct business impact.

- **API:** stateless, horizontally scaled behind ALB, multi-AZ. Single instance failure is invisible to users.
- **Workers:** stateless, scale per queue depth. Broker (Redis) is HA-replicated.
- **Database:** Postgres with Multi-AZ failover. RTO < 120 seconds for automatic failover.
- **Webhook receiver:** scaled separately from API so campaign traffic cannot starve event ingestion.

### 6.3 Durability

- **Postgres:** point-in-time recovery, daily automated snapshots (30 day retention), cross-region replica (read-only, DR)
- **S3:** versioning enabled on imports, inbound mail, and event archive buckets
- Once SES accepts a message (returns a `MessageId`), we consider the send durable — SES guarantees 11 9s on its own
- **Event archive:** all raw SES event payloads written to S3 (Kinesis Firehose) within 1 minute of receipt

### 6.4 Security

- **Authentication:** Argon2id for passwords; mandatory TOTP MFA for admin roles; session cookies with `Secure+HttpOnly+SameSite=strict`
- **Authorization:** role-based access (admin/user) enforced at the route level
- **API access:** API keys for internal integrations, hashed at rest (sha256)
- **Transport:** TLS 1.2+ everywhere, HSTS preload on public domains
- **Secrets:** AWS Secrets Manager with automatic rotation (90 days DB, 90 days SMTP, 180 days DNS API tokens)
- **Data at rest:** RDS encryption with KMS customer-managed keys; S3 SSE-KMS
- **PII handling:** email addresses hashed in logs; full addresses never logged
- **Audit log:** 7-year retention, immutable, covers every state-changing operation

### 6.5 Compliance

- **CAN-SPAM:** physical postal address in every outbound email (configured platform-wide); one-click unsubscribe; suppression honored immediately
- **GDPR:** contact-level right to erasure via API; data export in JSON; data processing agreements with sub-processors
- **CCPA:** opt-out and delete requests honored within statutory windows
- **Gmail/Yahoo 2024 bulk sender requirements:** SPF, DKIM, DMARC mandatory; RFC 8058 unsubscribe mandatory; complaint rate < 0.3% hard ceiling enforced
- **SOC 2 Type II:** targeted for year 2 — current architecture designed to meet controls

---

## 7. Data Model

The complete schema is defined in `01_schema.sql` (33 tables). This section summarizes the table groups and calls out the invariants that must be preserved across all application code paths.

### 7.1 Schema Overview

| Group | Representative tables | Purpose |
|---|---|---|
| Auth | `users`, `api_keys` | Authentication & access control |
| Identity | `domains`, `domain_dns_records`, `sender_profiles`, `ses_configuration_sets`, `ip_pools` | Sending infrastructure |
| Contacts | `contacts`, `contact_sources`, `subscription_statuses`, `preferences`, `suppression_entries` | Recipient records and state |
| Lists & segments | `lists`, `list_members`, `segments` | Explicit and query-based audiences |
| Imports | `import_jobs`, `import_rows` | CSV ingestion with full provenance |
| Templates | `templates`, `template_versions` | Versioned content |
| Campaigns | `campaigns`, `campaign_runs`, `segment_snapshots` | Campaign definition and frozen audiences |
| Execution | `send_batches`, `messages`, `message_tags` | Per-message send records |
| Events | `delivery_events`, `bounce_events`, `complaint_events`, `open_events`, `click_events`, `unsubscribe_events`, `reply_events` | Event trail from SES |
| Operational | `circuit_breaker_state`, `rolling_metrics`, `audit_log` | Runtime state and audit |
| ML | `contact_ml_features`, `template_ml_scores`, `anomaly_alerts` | Scores and alerts |

### 7.2 Critical Invariants

These invariants are enforced by database constraints, application logic, or both. **Code review must verify no change violates them.**

- **Every message has a `domain_id` and `sender_profile_id`** — no anonymous sending. Enforced by `NOT NULL`.
- **`suppression_entries (email)` is `UNIQUE`** — duplicates impossible. Enforced by constraint.
- **A contact in `lifecycle_status = 'suppressed'` or `'unsubscribed'` cannot receive new messages** — enforced by segment evaluation AND pre-send check.
- **`segment_snapshots` is immutable once written** — enforced by lack of `UPDATE` code paths; only `INSERT`.
- **`circuit_breaker_state = 'open'` pauses all sends for the scope** — enforced by send worker checking state on every task.
- **`messages.status` transitions are one-way** — `'queued'` → `'sending'` → `'sent'`|`'failed'`. No state regression. Enforced by conditional `UPDATE` in code.
- **`audit_log` entries are never deleted** — enforced by IAM policy on the database user that serves the application (`INSERT` only, no `DELETE`/`UPDATE`).

### 7.3 Partitioning Strategy

Five tables will exceed 1 billion rows at scale and require partitioning:

- **`messages`:** monthly partition by `created_at`. Old partitions detached and archived to S3 Parquet after 90 days.
- **`delivery_events`, `bounce_events`, `complaint_events`, `open_events`, `click_events`:** same strategy as `messages`.
- **`audit_log`:** monthly partition by `occurred_at`. Kept forever in Postgres (7-year compliance).
- **`rolling_metrics`:** not partitioned (small table). TTL rows older than 90 days via nightly cleanup.

Partitioning is implemented using Postgres native declarative partitioning. Migration to partitioned tables happens at the end of Phase 1 when row counts exceed 100M.

---

## 8. Delivery Pipeline

### 8.1 Pre-Send Validation

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

Gates 1–3 run at **contact ingestion** (import time). Gates 4–7 run at **send time**. This split is intentional: ingestion-time gates can be fixed with a better list; send-time gates reflect current state (a contact may have unsubscribed since import).

### 8.2 Queue & Throttle

The queue architecture uses **one Celery queue per sending domain**. This is the key decision that enables per-domain circuit breaking — a global queue would make per-domain pausing impossible without complex filtering.

```
Broker:          Redis (single cluster, HA replicated)
Queue naming:    send.{domain_name}
Rate enforcement: Redis-backed token bucket per domain
Worker pool:     scaled per queue depth (autoscaling)
Prefetch:        1 task per worker (task_acks_late=True)
Retry policy:    exponential backoff with jitter, max 3 retries
```

### 8.3 Send Execution

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

### 8.4 Event Ingestion

SES emits events to the configuration-set event destination (SNS topic). The webhook receiver is a **dedicated service** — deployed separately from the API so that campaign-related API traffic cannot starve event ingestion.

- **Webhook receiver:** verifies SNS signature in < 20ms, enqueues raw payload, returns 200
- **Event worker:** parses payload, looks up message by `ses_message_id`, writes typed event row, writes suppression if needed
- **Rolling metrics worker:** updates `rolling_metrics` every 5 minutes per scope
- **Circuit breaker evaluator:** reads `rolling_metrics` every 60 seconds, trips/resets breakers
- All raw SNS payloads archived to S3 via Kinesis Firehose for compliance and replay

---

## 9. Operational Guardrails

### 9.1 Circuit Breakers

Circuit breakers exist at four scopes. Each scope has its own thresholds. Breakers operate independently — a tripped domain breaker does not trip the account breaker.

| Scope | Trip threshold (24h) | Response | Auto-reset |
|---|---|---|---|
| Domain | Bounce > 1.5% OR Complaint > 0.05% | Pause domain queue | After 24h of clean metrics |
| IP pool | Bounce > 2% OR Complaint > 0.07% | Pause pool | Manual after investigation |
| Sender profile | Bounce > 1.5% OR Complaint > 0.05% | Pause profile | Manual |
| Account | Bounce > 2.5% OR Complaint > 0.08% | Pause all sending, alert on-call | Manual only |

> **Why half the ESP's warning level?** AWS SES warns at 5% bounce / 0.1% complaint. We trip our breakers at 1.5% / 0.05%. By the time AWS issues a warning, domain-level reputation damage has already accumulated at Gmail and Outlook — damage that persists for weeks.

### 9.2 Rate Limiting

- **Per-domain:** Redis token bucket, enforced inside send task. Default 150/hour, ramps during warmup.
- **Per-IP-pool:** aggregate rate limit, prevents any single campaign from dominating a pool.
- **Platform-wide:** daily send cap configurable in settings. Blocks enqueue (not send) when exceeded.

---

## 10. ML Services

ML does not deliver messages. It improves decisions **before** the send (what to send, when to send, whom to send to) and **after** the send (what the reply means, whether the system should pause). Every model starts simple and improves with data.

### 10.1 Pre-Send Spam Scorer (Model 1)

Scores content + context. Returns probability 0–1. **Send only if score < 0.2.**

- **Features:** subject length, spam word count, all-caps ratio, link count, body length, punctuation density, personalization score, domain age, warmup age, recipient engagement history, recent complaint rate
- **Label:** `did_complain` OR `did_hard_bounce` within 48h of send
- **Weeks 1–2:** heuristic rules only (no ML)
- **Week 3+:** sklearn LogisticRegression, retrained weekly
- **Week 12+:** evaluate XGBoost if logistic regression's AUC plateaus
- **Serving:** in-process Python at send time, p99 < 5ms

### 10.2 Reply Intent Classifier (Model 2)

Classifies every inbound reply into an intent class. Action depends on class.

- **Classes:** `interested`, `not_now`, `unsubscribe`, `out_of_office`, `angry`, `objection`, `question`
- **Seed training:** 200 Claude-generated synthetic examples per class (1,400 total)
- **Initial model:** TF-IDF + sklearn LinearSVC. Fast, interpretable, strong on short text.
- **Evolution:** at 5K+ labeled real replies, evaluate fine-tuned DistilBERT
- **Serving:** called from reply processing worker, p99 < 100ms
- **Actions:** `unsubscribe`/`angry` → instant suppression; `interested` → CRM webhook; `not_now` → re-queue in 90 days

### 10.3 Anomaly Detection

Monitors rolling metrics for statistical anomalies — sudden changes not caught by static thresholds. Alerts on-call before a circuit breaker trips.

- **Metrics monitored:** bounce rate, complaint rate, open rate, click rate, reply rate, unsubscribe rate
- **Algorithm v1:** exponential moving average with 3σ threshold (simple, robust)
- **Algorithm v2 (future):** Prophet-based forecasting for seasonal campaigns
- **Output:** `anomaly_alerts` table entries with severity and probable cause

### 10.4 Send-Time Optimization

Predicts the best hour/day to send each campaign-to-contact combination. Improves open and reply rates, which are the dominant deliverability signals.

- **Features:** recipient timezone, prior open history, prior click history, day-of-week patterns, campaign type
- **Model:** gradient boosting per recipient, predicting probability of open per `(hour, day-of-week)` slot
- **Output:** `best_send_hour_utc` and `best_send_day_of_week`, stored in `contact_ml_features`
- **Used by:** orchestrator when `schedule_type = 'optimized'`

---

## 11. Deployment & Infrastructure

### 11.1 AWS Topology

Single region (`us-east-1`) in v1. All components in a dedicated VPC with public and private subnets across three availability zones.

```
VPC: 10.0.0.0/16
  Public subnets:  10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24   (ALB)
  Private subnets: 10.0.10.0/24, 10.0.20.0/24, 10.0.30.0/24 (ECS, RDS)
  DB subnets:      10.0.40.0/24, 10.0.50.0/24, 10.0.60.0/24 (RDS Multi-AZ)

ECS clusters:
  dispatch-api         (6 replicas)
  dispatch-webhook     (4 replicas, scales with event volume)
  dispatch-send        (20–60 replicas, scales with queue depth)
  dispatch-events      (10 replicas)
  dispatch-scheduler   (1 replica — Celery Beat)

RDS:         dispatch-prod-db      (db.r6g.2xlarge, Multi-AZ, 1 read replica)
ElastiCache: dispatch-prod-redis   (cache.r6g.large, replicated)
S3:          dispatch-prod-imports, dispatch-prod-inbound, dispatch-prod-events-archive
SNS:         dispatch-prod-ses-events (topic, multiple subscriptions)
SES:         production access, dedicated IP pool x3
```

### 11.2 Environments

| Environment | Purpose | Data | Deployed via |
|---|---|---|---|
| `local` | Developer machine | Docker Compose, ephemeral | `make dev` |
| `ci` | Automated testing | Ephemeral per test run | GitHub Actions |
| `staging` | Pre-production validation | Anonymized copy of prod | Auto on merge to `main` |
| `production` | Live traffic | Production | Manual approval, canary |

### 11.3 Infrastructure as Code

- All infrastructure defined in Terraform (AWS provider)
- Modules: `vpc`, `rds`, `ecs-service`, `ses-identity`, `cloudflare-domain`
- State stored in S3 with DynamoDB locking
- Changes go through `plan` → PR review → `apply` (no direct apply)
- Environment-specific variables in `envs/staging.tfvars` and `envs/prod.tfvars`
- Domain provisioning runs outside Terraform — it's operational, not infrastructural

---

## 12. Security

### 12.1 Authentication & Authorization

- **UI auth:** email + password (Argon2id) + TOTP MFA. Sessions via server-side store.
- **API auth:** scoped API keys (sha256 hashed). Public key prefix visible in UI; secret shown once at creation.
- **Service-to-service:** IAM roles (ECS task roles). No long-lived credentials in containers.
- **Authorization:** role-based (admin / user). No cross-user data scoping required.
- **Audit:** every authentication event and permission change logged to `audit_log`.

### 12.2 Secrets Management

- AWS Secrets Manager for: database credentials, SES SMTP credentials, third-party API keys
- Automatic rotation: 90 days for DB, 90 days for SES SMTP, 180 days for DNS API tokens
- Secrets injected at container start via IAM role — never baked into images, never in env vars passed via CLI
- `.env` files in local development only; not committed
- Pre-commit hook scans for leaked secrets (truffleHog)

### 12.3 Data Protection

- **At rest:** RDS with KMS CMK encryption; S3 SSE-KMS; EBS volumes encrypted
- **In transit:** TLS 1.2+ enforced; internal services use service mesh mTLS (future)
- **In logs:** email addresses hashed; no passwords/tokens; PII scrubbed via structlog processor
- **Right to erasure (GDPR):** contact deletion propagates to messages (soft nullify `contact_id`), events (retained, `contact_id` set to `NULL`)

---

## 13. Observability

### 13.1 Metrics

Every service exports Prometheus-compatible metrics. Datadog agent scrapes and ships.

- **RED metrics per service:** Rate, Errors, Duration (p50, p95, p99)
- **Business metrics:** `sends_total`, `deliveries_total`, `bounces_total`, `complaints_total` (per domain, per campaign)
- **Queue metrics:** `queue_depth`, `task_latency`, `retry_count`
- **DB metrics:** `connection_pool_usage`, `replication_lag`, `slow_query_count`
- **Reputation metrics:** `postmaster_reputation` (per domain), `seed_inbox_placement`

### 13.2 Logging

- **Format:** structured JSON (structlog)
- **Required fields:** `timestamp`, `level`, `service`, `trace_id`, `event`
- **Retention:** 30 days hot in Datadog; 1 year in S3 (Parquet, queryable via Athena)
- **PII policy:** no email addresses, no message bodies, no API keys. Hashes only.

### 13.3 Tracing

- OpenTelemetry instrumentation on FastAPI, Celery, SQLAlchemy, boto3
- Trace context propagated through Celery tasks (via task headers)
- Traces ingested into Datadog APM
- Sampling: 100% in staging; 10% in production (with 100% on errors)

### 13.4 Alerting

Alerts are tiered by severity. Runbooks link from each alert to `04_operations_runbook.md`.

| Severity | Routing | Response time | Examples |
|---|---|---|---|
| SEV-1 | PagerDuty, wake on-call | < 5 min | Sending stopped, complaint spike > 0.08% |
| SEV-2 | PagerDuty, business hours | < 15 min | Webhook lag, domain burn, DB replication lag |
| SEV-3 | Slack `#alerts` | < 1 hour | Single worker failure, elevated 4xx |
| SEV-4 | Ticket queue | Next day | Metric drift, minor lag |

---

## 14. Rollout Plan

Phased rollout over 6–12 months. Each phase has explicit entry and exit criteria. **A phase is not complete until exit criteria are measurably met** — not until the work is "done".

### 14.1 Phase 1 — MVP (Months 1–3)

**Target:** 10K–75K sends/day. Single org. Manual domain setup.

- Core data model (all 39 tables)
- Auth, org, user management
- Single domain setup flow (manual DNS)
- CSV import with validation
- Template editor (plain text)
- Campaign builder + launch
- SES send via single configuration set
- SNS webhook receiver
- Event processing → suppression
- Basic dashboards (sends, bounces, complaints)

**Exit criteria:** 10 real campaigns launched, bounce < 2%, complaint < 0.05%, no data loss incidents

### 14.2 Phase 2 — Scale (Months 3–5)

**Target:** 75K–300K sends/day. Multi-domain. Automated provisioning.

- Automated domain provisioning (Cloudflare + SES API)
- Per-domain Celery queues
- Token-bucket rate limiting
- Circuit breakers (all four scopes)
- Warmup scheduling engine
- Google Postmaster Tools integration
- Advanced segmentation engine

**Exit criteria:** 50 active domains, bounce < 1.5%, complaint < 0.05%, zero SES warnings

### 14.3 Phase 3 — ML (Months 5–8)

**Target:** 300K–600K sends/day. Self-improving.

- Pre-send spam scorer (Model 1): heuristic → sklearn
- Reply intent classifier (Model 2): seed → production
- Anomaly detection on rolling metrics
- Send-time optimization
- Seed inbox placement testing integration

**Exit criteria:** Both ML models deployed, AUC > 0.85, seed placement > 85% across 3 major providers

### 14.4 Phase 4 — 1M/Day (Months 8–12)

**Target:** 600K → 1M+ sends/day. Production-hardened.

- Message & event table partitioning
- Cross-region DR
- SOC 2 Type I readiness
- Advanced analytics & BI export
- Deliverability consulting dashboard

**Exit criteria:** 1M sends/day sustained, 99.95% API availability, 4 SEV-2+ incidents or fewer per quarter

---

## 15. Open Questions & Future Work

- Should we support BYOD (bring-your-own-domain)? Currently no — reduces control. Revisit in Phase 4.
- Should inbound reply processing run fully automated, or require human-in-the-loop? Currently automated with alert routing for ambiguous cases.
- Does Phase 4 need Kubernetes, or does ECS remain sufficient? Benchmark at Phase 3 exit.
- Should template personalization use a sandboxed Jinja or a custom safer subset? Security review required.

---

## Appendix A — API Surface Overview

REST over HTTPS. JSON request and response bodies. Cursor-based pagination. Full OpenAPI spec auto-generated from FastAPI at `/api/docs`.

**Auth**
```
POST   /auth/login
POST   /auth/logout
POST   /auth/mfa/verify
POST   /auth/api-keys
DELETE /auth/api-keys/:id
```

**Domains**
```
GET    /domains
POST   /domains                       # triggers provisioning
GET    /domains/:id
GET    /domains/:id/health
POST   /domains/:id/retire
```

**Contacts**
```
GET    /contacts
POST   /contacts
GET    /contacts/:id
PATCH  /contacts/:id
DELETE /contacts/:id
POST   /contacts/bulk-import          # returns import_job_id
```

**Lists & Segments**
```
GET    /lists
POST   /lists
POST   /lists/:id/members
GET    /segments
POST   /segments
POST   /segments/:id/evaluate         # returns count, not records
```

**Templates**
```
GET    /templates
POST   /templates
GET    /templates/:id/versions
POST   /templates/:id/versions
POST   /templates/:id/versions/:v/publish
```

**Campaigns**
```
GET    /campaigns
POST   /campaigns
GET    /campaigns/:id
POST   /campaigns/:id/launch
POST   /campaigns/:id/pause
POST   /campaigns/:id/resume
GET    /campaigns/:id/analytics
```

**Suppression**
```
GET    /suppression
POST   /suppression                   # single or bulk
DELETE /suppression/:email
```

**Events (webhooks — not public API)**
```
POST   /webhook/ses                   # SNS signed
POST   /webhook/inbound               # inbound email processing
```

**Analytics**
```
GET    /analytics/overview
GET    /analytics/domains
GET    /analytics/reputation
```

---

## Appendix B — Glossary

**Bounce.** Mail server could not deliver. Hard bounce = permanent (bad address). Soft = transient (full mailbox).

**Burn / Burnt domain.** A sending domain whose reputation has degraded to the point where emails from it go to spam or are rejected. Not recoverable at any practical timeline.

**Circuit breaker.** Automated control that pauses sending when a health metric crosses a threshold. Resets automatically or manually depending on scope.

**Complaint.** Recipient clicked 'mark as spam'. Reported to sender via Feedback Loop (FBL).

**Configuration set.** An SES construct that groups sending behavior (event destinations, IP pool, tracking).

**DKIM.** DomainKeys Identified Mail. Cryptographic signature proving the message came from the claimed domain and was not altered.

**DMARC.** Policy layer on top of SPF and DKIM. Tells receivers what to do when authentication fails.

**Engagement.** Opens, clicks, replies, moves from spam to inbox. Strongest positive signal in modern filtering.

**Feedback Loop (FBL).** Mechanism by which mailbox providers report spam complaints back to senders.

**Leaky bucket.** Rate-limiting algorithm that drains tokens at a fixed rate. Prevents bursts.

**List hygiene.** Practice of maintaining only valid, engaged addresses on a sending list.

**One-click unsubscribe (RFC 8058).** Headers that let a recipient unsubscribe with a single action, no follow-up required. Mandatory for bulk senders since 2024.

**PTR record.** Reverse DNS. Maps an IP back to a hostname. Required by Outlook for trust.

**Reputation.** A trust score mailbox providers maintain per domain and per IP. Built over weeks, burned in hours.

**Seed testing.** Sending test emails to a panel of known addresses across providers to measure inbox placement.

**SES (Simple Email Service).** AWS's managed email sending service.

**SNS (Simple Notification Service).** AWS's managed pub/sub. Delivers SES events to our webhooks.

**Spam trap.** An address created by anti-spam organizations or mailbox providers to catch senders with poor list hygiene.

**SPF.** Sender Policy Framework. DNS record listing which servers may send for a domain.

**Suppression list.** Authoritative list of addresses that must never be sent to (bounces, complaints, unsubscribes, manual).

**Warmup.** Gradually increasing send volume from a new domain or IP to build reputation without triggering spam filters.

---

*End of System Design Document.*  
*Paired files: `01_schema.sql` (database), `03_code_architecture.md` (code guide), `04_operations_runbook.md` (runbooks).*
