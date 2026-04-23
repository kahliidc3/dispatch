# Data Model

The complete schema is defined in `01_schema.sql` (33 tables). This section summarizes the table groups and calls out the invariants that must be preserved across all application code paths.

---

## 7.1 Schema Overview

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

---

## 7.2 Critical Invariants

These invariants are enforced by database constraints, application logic, or both. **Code review must verify no change violates them.**

- **Every message has a `domain_id` and `sender_profile_id`** — no anonymous sending. Enforced by `NOT NULL`.
- **`suppression_entries (email)` is `UNIQUE`** — duplicates impossible. Enforced by constraint.
- **A contact in `lifecycle_status = 'suppressed'` or `'unsubscribed'` cannot receive new messages** — enforced by segment evaluation AND pre-send check.
- **`segment_snapshots` is immutable once written** — enforced by lack of `UPDATE` code paths; only `INSERT`.
- **`circuit_breaker_state = 'open'` pauses all sends for the scope** — enforced by send worker checking state on every task.
- **`messages.status` transitions are one-way** — `'queued'` → `'sending'` → `'sent'` | `'failed'`. No state regression. Enforced by conditional `UPDATE` in code.
- **`audit_log` entries are never deleted** — enforced by IAM policy on the database user that serves the application (`INSERT` only, no `DELETE`/`UPDATE`).

---

## 7.3 Partitioning Strategy

Five tables will exceed 1 billion rows at scale and require partitioning:

- **`messages`:** monthly partition by `created_at`. Old partitions detached and archived to S3 Parquet after 90 days.
- **`delivery_events`, `bounce_events`, `complaint_events`, `open_events`, `click_events`:** same strategy as `messages`.
- **`audit_log`:** monthly partition by `occurred_at`. Kept forever in Postgres (7-year compliance).
- **`rolling_metrics`:** not partitioned (small table). TTL rows older than 90 days via nightly cleanup.

Partitioning is implemented using Postgres native declarative partitioning. Migration to partitioned tables happens at the end of Phase 1 when row counts exceed 100M.
