# Goals & Non-Goals

> Scope discipline is a deliverability control in itself. A system that tries to do everything does each thing poorly. The scope below is deliberately narrow.

---

## 2.1 Functional Goals

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

---

## 2.2 Non-Functional Goals (SLOs)

| Category | Target | Measurement window |
|---|---|---|
| API p99 latency | < 400 ms | 5-minute rolling |
| API availability | 99.95% | Monthly |
| Send queue lag (enqueue → send) | < 30 seconds | p95 over 1h |
| Event processing lag (SES → DB) | < 5 seconds | p95 over 1h |
| Suppression list update latency | < 10 seconds after event | p99 |
| Durability (once accepted by SES) | 99.999999999% | Always |
| Data loss RPO | ≤ 1 hour | Always |
| Recovery RTO | ≤ 4 hours | Always |

---

## 2.3 Non-Goals

- **Multi-region active-active** — single region (`us-east-1`) with DR to `us-west-2`
- **Inline email builder** — plain text primary, HTML imported not authored
- **Transactional email use case** — platform optimized for outreach and newsletter-style campaigns
- **BYOD (Bring Your Own Domain that we did not provision)** — removes control over warmup and rotation
- **SMTP relay API** — the public API is HTTPS/JSON only
- **Delivery to unauthenticated recipients** — every send requires a resolved contact record
- **Multi-tenancy** — single internal platform, no org isolation, no plan tiers, no external customer access
