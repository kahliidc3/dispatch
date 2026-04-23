# Non-Functional Requirements

---

## 6.1 Performance Targets

| Dimension | Target | Notes |
|---|---|---|
| API read p99 | < 200 ms | Single-entity lookups |
| API list p99 | < 400 ms | Paginated lists, ≤ 50 items |
| API write p99 | < 500 ms | Excludes async work |
| Send throughput (per domain) | ≤ 2,500/day, ≤ 150/hour | Enforced by rate limiter |
| Aggregate send throughput | 1,000,000/day target | Across all domains |
| Event ingestion throughput | ≥ 5,000 events/sec | Peak, during campaign send |
| Webhook ack time | < 100 ms | SNS requires fast ack |
| Circuit breaker evaluation interval | 60 seconds | Acceptable lag before pause |

---

## 6.2 Availability

The system is designed for **99.95% availability** on the control plane (API, UI, admin). The send path has a higher bar: loss of send capability has direct business impact.

- **API:** stateless, horizontally scaled behind ALB, multi-AZ. Single instance failure is invisible to users.
- **Workers:** stateless, scale per queue depth. Broker (Redis) is HA-replicated.
- **Database:** Postgres with Multi-AZ failover. RTO < 120 seconds for automatic failover.
- **Webhook receiver:** scaled separately from the API so campaign traffic cannot starve event ingestion.

---

## 6.3 Durability

- **Postgres:** point-in-time recovery, daily automated snapshots (30-day retention), cross-region replica (read-only, DR)
- **S3:** versioning enabled on imports, inbound mail, and event archive buckets
- Once SES accepts a message (returns a `MessageId`), we consider the send durable — SES guarantees 11 9s on its own
- **Event archive:** all raw SES event payloads written to S3 via Kinesis Firehose within 1 minute of receipt

---

## 6.4 Security

- **Authentication:** Argon2id for passwords; mandatory TOTP MFA for admin roles; session cookies with `Secure+HttpOnly+SameSite=strict`
- **Authorization:** role-based access (admin/user) enforced at the route level
- **API access:** API keys for internal integrations, hashed at rest (sha256)
- **Transport:** TLS 1.2+ everywhere, HSTS preload on public domains
- **Secrets:** AWS Secrets Manager with automatic rotation (90 days DB, 90 days SMTP, 180 days DNS API tokens)
- **Data at rest:** RDS encryption with KMS customer-managed keys; S3 SSE-KMS
- **PII handling:** email addresses hashed in logs; full addresses never logged
- **Audit log:** 7-year retention, immutable, covers every state-changing operation

---

## 6.5 Compliance

- **CAN-SPAM:** physical postal address in every outbound email (configured platform-wide); one-click unsubscribe; suppression honored immediately
- **GDPR:** contact-level right to erasure via API; data export in JSON; data processing agreements with sub-processors
- **CCPA:** opt-out and delete requests honored within statutory windows
- **Gmail/Yahoo 2024 bulk sender requirements:** SPF, DKIM, DMARC mandatory; RFC 8058 unsubscribe mandatory; complaint rate < 0.3% hard ceiling enforced
- **SOC 2 Type II:** targeted for year 2 — current architecture designed to meet controls
