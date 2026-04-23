# Acmemail — Operations Runbook

**Version:** 1.0
**Audience:** On-call engineers, platform SRE
**Scope:** Production operations, incident response, common failures

---

## 1. Service Topology

```
┌────────────────────────────────────────────────────────────────┐
│                       CloudFront / ALB                          │
└──────────────┬─────────────────────────┬───────────────────────┘
               │                         │
      ┌────────▼───────┐         ┌───────▼────────┐
      │   api (6x)     │         │   webhook (4x) │
      │  FastAPI       │         │  SNS receiver  │
      └────────┬───────┘         └────────┬───────┘
               │                          │
     ┌─────────┴──────────────────────────┴─────────┐
     │                Redis (ElastiCache)             │
     │           broker + cache + rate limits          │
     └───────────┬─────────────────────────────────┬──┘
                 │                                 │
       ┌─────────▼────────┐              ┌─────────▼────────┐
       │  send workers    │              │ event workers    │
       │  (per-domain Q)  │              │ (event pipeline) │
       └─────────┬────────┘              └─────────┬────────┘
                 │                                 │
                 └───────────┬─────────────────────┘
                             │
                   ┌─────────▼──────────┐
                   │  PostgreSQL (RDS)  │
                   │  primary + replica │
                   └────────────────────┘
```

**Key AWS resources (us-east-1):**

- RDS Postgres cluster: `acmemail-prod-db` (primary + async replica for reads)
- ElastiCache Redis: `acmemail-prod-redis`
- ECS services: `api`, `webhook`, `send-workers`, `event-workers`, `scheduler`
- SES configuration sets: `acmemail-prod-outreach`, `acmemail-prod-transactional`
- SNS topic: `acmemail-prod-ses-events`
- S3 buckets: `acmemail-prod-imports`, `acmemail-prod-inbound-mail`, `acmemail-prod-event-archive`

---

## 2. On-Call Escalation

| Severity | Definition | Response | Escalation |
|----------|-----------|----------|------------|
| SEV-1 | Sending stopped, data loss, security breach | Immediate | Page on-call + second pager |
| SEV-2 | Circuit breaker tripped for > 30% of domains, elevated complaint rate | < 15 min | Page on-call |
| SEV-3 | Single domain burnt, one worker pool failing, elevated latency | < 1 hour | Slack alert, triage in business hours |
| SEV-4 | Minor metric drift, single job failure | Next business day | Ticket |

**Escalation contacts** live in `docs/runbooks/contacts.md` and PagerDuty, not in this file.

---

## 3. Dashboards & Alerts

### 3.1 Primary Dashboards (Datadog)

- **Platform Health** — all services green/yellow/red
- **SES Reputation** — per-account bounce + complaint rates, rolling 1h/6h/24h
- **Domain Matrix** — heatmap of every sending domain × health metric
- **Queue Depth** — SQS + Celery per-queue depth, trending
- **Event Pipeline** — webhook receipt latency, processing lag, DLQ depth
- **API Latency** — p50/p95/p99 per endpoint
- **DB Health** — connection pool usage, slow queries, replication lag

### 3.2 Critical Alerts (page)

- `complaint_rate_24h > 0.08%` (any account)  → **SEV-1**
- `bounce_rate_24h > 2.5%` (any account) → **SEV-1**
- `webhook_processing_lag > 5 min` → **SEV-2**
- `api_5xx_rate > 1% for 5 min` → **SEV-2**
- `db_replication_lag > 60s` → **SEV-2**
- `celery_dlq_depth > 1000` → **SEV-2**
- `domain_burn_rate > 2 domains/day` → **SEV-2**

### 3.3 Warning Alerts (Slack)

- `complaint_rate_24h > 0.05%` → warn
- `queue_depth > 50,000` sustained → warn
- `postmaster_reputation = Low` for any domain → warn
- `seed_inbox_placement < 85%` → warn

---

## 4. Runbooks — Incident Response

### 4.1 RUNBOOK: Complaint Rate Spike

**Trigger:** account-level complaint rate > 0.08% in 24h window
**SEV:** 1

**Immediate actions (first 5 minutes):**

1. Confirm the alert is real:
   ```bash
   # Datadog query
   avg:acmemail.ses.complaint_rate{env:prod} by {account}
   ```
2. Check the Circuit Breaker dashboard — has it auto-paused? If not, it's a bug.
3. **Manual pause** if needed:
   ```bash
   ./ops/scripts/pause_account.sh --account acmemail-prod --reason "SEV1 complaint spike"
   ```
4. Alert stakeholders in `#incidents` channel.

**Investigation (next 15 minutes):**

1. Identify the source campaign:
   ```sql
   SELECT campaign_id, COUNT(*) AS complaints
   FROM complaint_events
   WHERE occurred_at > now() - interval '1 hour'
   GROUP BY campaign_id ORDER BY complaints DESC LIMIT 10;
   ```
2. Pause that campaign and all others using the same template/list.
3. Check if the list came from a recent import — review `import_jobs` for the last 24h.
4. If a specific sender profile is responsible, pause it.

**Recovery:**

1. Do not unpause until complaint rate drops below 0.02% for 6 consecutive hours.
2. Before resuming, verify:
   - The offending list has been removed from active campaigns
   - All recipients from that list are added to suppression
   - The root cause is documented in the incident writeup

**Post-incident:**

- Full writeup in `docs/incidents/` within 48 hours
- Identify whether the pre-send spam scorer should have caught this
- Review whether circuit breaker thresholds need adjustment

---

### 4.2 RUNBOOK: Domain Burned (Reputation Red)

**Trigger:** Postmaster Tools reports Bad reputation OR > 2 domains burning per day
**SEV:** 2

**Immediate actions:**

1. Mark the domain as retired in the DB (do NOT delete):
   ```bash
   ./ops/scripts/retire_domain.sh --domain m47.sendbrand.com --reason "postmaster_bad"
   ```
2. Drain pending sends for that domain's queue:
   ```bash
   ./ops/scripts/drain_queue.sh --queue send.m47.sendbrand.com
   ```
3. Remove DNS records to avoid continued SMTP attempts:
   ```bash
   ./ops/scripts/remove_dns.sh --domain m47.sendbrand.com
   ```

**Investigation:**

1. Pull recent sending history:
   ```sql
   SELECT campaign_id, COUNT(*), SUM(CASE WHEN status = 'bounced' THEN 1 ELSE 0 END) AS bounces
   FROM messages
   WHERE domain_id = (SELECT id FROM domains WHERE name = 'm47.sendbrand.com')
     AND created_at > now() - interval '7 days'
   GROUP BY campaign_id ORDER BY bounces DESC;
   ```
2. Was this domain pushed above its daily cap? Check `sender_profiles.daily_send_count` history.
3. Did the warmup complete properly? Check `warmup_completed_at`.

**Recovery:**

- Provision replacement domain(s): `./ops/scripts/provision_domains.sh --count 5`
- Add to warmup rotation. Do NOT accelerate warmup to compensate.

---

### 4.3 RUNBOOK: SES Account Suspended

**Trigger:** SES API returns `AccountSuspendedException` OR AWS email notification
**SEV:** 1

**Immediate actions:**

1. Open support case with AWS:
   - Severity: Production system down
   - Subject: "SES sending account suspended — request reinstatement"
2. Alert leadership — SES suspensions can take 24-72 hours to reverse.

**Investigation while waiting on AWS:**

1. Pull complaint/bounce history for the last 30 days — identify the incident pattern.
2. Prepare a written plan for AWS including:
   - What happened
   - Why it happened
   - What's been changed to prevent recurrence
   - List hygiene improvements made

**Recovery:**

- AWS will request a plan. Send the prepared one.
- Once reinstated, ramp traffic back to SES at 10%/hour. Do not return to 100% in a single step.
- All domains on the suspended account need reputation re-validation via seed testing before full volume resumes.

---

### 4.4 RUNBOOK: Webhook Processing Lag

**Trigger:** `webhook_processing_lag > 5 min`
**SEV:** 2

**Why this matters:** Lagged event processing means suppression lists are stale. Sends continue to addresses that have already bounced or complained.

**Immediate actions:**

1. Check webhook receiver health:
   ```bash
   curl https://webhook.acmemail.internal/healthz
   ```
2. Check event worker queue depth:
   ```bash
   celery -A apps.workers.events inspect active_queues
   ```
3. If event queue is backed up > 10k messages:
   - Scale event workers: `./ops/scripts/scale.sh --service event-workers --replicas 20`
   - Consider pausing non-critical outbound sending until caught up (stops feeding more events in)

**Investigation:**

- Check for DB slow queries blocking event writes (Datadog APM, DB slow query log)
- Check for SNS delivery failures in CloudWatch
- Check webhook 5xx rate

**Recovery:**

- Once lag drops below 30 seconds, scale workers back to normal count
- If any suppression was delayed during this time, run:
  ```bash
  ./ops/scripts/audit_delayed_suppressions.sh --since "2 hours ago"
  ```

---

### 4.5 RUNBOOK: Database Failover

**Trigger:** Primary RDS instance unreachable
**SEV:** 1

**Immediate actions:**

1. RDS Multi-AZ should auto-failover in 60-120 seconds. Verify:
   ```bash
   aws rds describe-db-instances --db-instance-identifier acmemail-prod-db
   ```
2. Watch for the endpoint update. Applications using the RDS DNS name will reconnect automatically.
3. If auto-failover fails:
   ```bash
   aws rds failover-db-cluster --db-cluster-identifier acmemail-prod-db-cluster
   ```

**During failover (services will error):**

- API will return 503 for ~90 seconds (acceptable — users will retry)
- Workers will retry — Celery handles this with `acks_late=True`
- Webhook will queue events; no data loss expected

**After failover:**

- Verify replication is re-established on the new replica
- Check for any stuck transactions
- Review slow query log for the hour after failover (warm cache issue)

---

### 4.6 RUNBOOK: Runaway Sending Campaign

**Trigger:** A campaign is sending faster than expected, or past its target
**SEV:** 2

```bash
# Immediate pause
./ops/scripts/pause_campaign.sh --campaign-id <uuid>

# Verify no more messages are being enqueued
redis-cli LLEN send.<domain>
```

Investigate why the rate limiter did not hold. Common causes:
- Redis flushed (token bucket reset)
- Rate limit config drift — check `send_rate_per_hour` on campaign
- Multiple worker instances (horizontal scale) sharing the same bucket without atomic operations

---

## 5. Standard Operational Procedures

### 5.1 Deploying a New Release

```bash
# 1. Tag release
git tag -a v1.42.0 -m "Release 1.42.0"
git push --tags

# 2. CI runs full test suite, builds images
# 3. Deploy to staging automatically, smoke test
# 4. Manual approval gate in CI

# 5. Production deploy (canary)
./ops/scripts/deploy.sh --env prod --canary 10  # 10% of traffic
# Wait 15 min, watch metrics

# 6. Full rollout if clean
./ops/scripts/deploy.sh --env prod --canary 100
```

**Rollback:**
```bash
./ops/scripts/rollback.sh --env prod --to v1.41.0
```
Rollback is automatic if error rate > 2x baseline for 5 minutes.

### 5.2 Provisioning New Sending Domains

```bash
# Provision 10 new subdomains under sendbrand.com
./ops/scripts/provision_domains.sh \
    --parent sendbrand.com \
    --count 10 \
    --pattern "m{i}" \
    --region us-east-1

# Output: 10 subdomains created, DNS records published,
# SES identities verifying, warmup schedules initialized.
# Check status in the Domain Health dashboard.
```

### 5.3 Adding a Suppression

```bash
# Bulk suppression from a file
./ops/scripts/add_suppressions.sh \
    --file /tmp/to_suppress.csv \
    --reason manual \
    --notes "Client request — account #12345"
```

### 5.4 Database Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "add_ml_scores_table"

# Review the generated file MANUALLY — never trust auto-generation blindly
# for: index names, constraint names, data migrations

# Apply to staging
alembic upgrade head

# Apply to production (requires approval)
./ops/scripts/migrate_prod.sh
```

**Migration safety rules:**
- Always additive first (add column nullable, backfill, make non-null in separate migration)
- No `DROP COLUMN` or `DROP TABLE` in the same deploy as the code that stops using it
- All migrations tested on a production-sized staging DB before production

### 5.5 Adding a New Sending IP

```bash
# Request dedicated IP from SES
aws sesv2 create-dedicated-ip-pool --pool-name acmemail-prod-pool-3
aws sesv2 put-dedicated-ip-pool --ip-address NEW_IP --destination-pool acmemail-prod-pool-3

# Register in our DB
./ops/scripts/register_ip.sh --ip NEW_IP --pool acmemail-prod-pool-3

# Initiate warmup (7-day ramp)
./ops/scripts/start_ip_warmup.sh --ip NEW_IP
```

---

## 6. Data Retention & Archival

| Data | Retention | Storage |
|------|-----------|---------|
| `messages` | 90 days hot, 2 years archive | Postgres → S3 parquet |
| Event tables | 90 days hot, 2 years archive | Postgres → S3 parquet |
| `audit_log` | 7 years | Postgres → S3 (compliance) |
| Raw CSV imports | 90 days | S3 with lifecycle rule |
| Inbound email MIME | 30 days | S3 with lifecycle rule |
| `suppression_entries` | Forever | Postgres |

Archival runs nightly via Celery Beat → Kinesis Firehose → S3 Parquet partitioned by org/date.

---

## 7. Security Hygiene

### Credentials & Rotation

| Credential | Rotation | Mechanism |
|------------|----------|-----------|
| AWS IAM access keys | None (use roles) | — |
| SES SMTP credentials | 90 days | AWS Secrets Manager auto-rotation |
| Database passwords | 90 days | AWS Secrets Manager auto-rotation |
| DNS provider API tokens | 180 days | Manual, calendar reminder |
| User session secrets | Per deploy | Environment var |

### Access Control

- Production access: 2FA required, time-limited via AWS SSO
- DB read access: granted to on-call engineers, audited
- DB write access: only via application or approved DBA runbook
- Secrets: never in logs, never in code, never in CI config

### Audit Requirements

- All `audit_log` entries retained 7 years
- Suppression additions/removals logged with actor
- Campaign launches logged with full command payload
- DNS changes logged with before/after state

---

## 8. Capacity Planning

### Current Limits (update quarterly)

- API: 6 instances × 4 workers = ~2,400 req/s sustained
- Send workers: 40 replicas × 10 tasks = 400 concurrent sends
- Event workers: 10 replicas × 20 tasks = 200 concurrent events
- DB: 500 connection pool, ~60% utilization typical
- Redis: 8GB, ~40% utilization

### Scale-Up Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| API CPU > 70% (15 min) | Add 2 instances |
| Queue depth > 50k (10 min) | Double worker count |
| DB connections > 80% | Investigate query plan before scaling |
| Redis memory > 75% | Scale up next instance size |

### Pre-Planned Events

Before a known volume spike (e.g., client onboarding, major campaign):

1. Pre-warm worker capacity 24h in advance
2. Verify domain pool has 20% headroom
3. Notify on-call — increase staffing during window

---

## 9. Disaster Recovery

### RPO / RTO Targets

- **RPO** (data loss): ≤ 1 hour
- **RTO** (recovery time): ≤ 4 hours for critical path, ≤ 24 hours for full restore

### Backup Strategy

- RDS automated snapshots: daily, 30 day retention
- RDS point-in-time recovery: enabled, 7 day window
- S3 cross-region replication: enabled for critical buckets
- Manual snapshot before every production migration

### Regional Failover

Currently single-region (`us-east-1`). Cross-region DR is ADR-017 (planned Q3).

---

## 10. Contacts & Escalation

See `docs/runbooks/contacts.md` and PagerDuty for current on-call rotation.

**AWS Support:** Enterprise support contract. Open cases via console.
**Cloudflare Support:** Business plan — 24/7 chat.

---

*End of Operations Runbook*
