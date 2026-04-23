# Rollout Plan

Phased rollout over 6–12 months. Each phase has explicit entry and exit criteria. **A phase is not complete until exit criteria are measurably met** — not until the work is "done".

---

## 14.1 Phase 1 — MVP (Months 1–3)

**Target:** 10K–75K sends/day. Manual domain setup.

- Core data model (33 tables)
- Auth and user management
- Single domain setup flow (manual DNS)
- CSV import with validation
- Template editor (plain text)
- Campaign builder + launch
- SES send via single configuration set
- SNS webhook receiver
- Event processing → suppression
- Basic dashboards (sends, bounces, complaints)

**Exit criteria:** 10 real campaigns launched, bounce < 2%, complaint < 0.05%, no data loss incidents

---

## 14.2 Phase 2 — Scale (Months 3–5)

**Target:** 75K–300K sends/day. Multi-domain. Automated provisioning.

- Automated domain provisioning (Cloudflare + SES API)
- Per-domain Celery queues
- Token-bucket rate limiting
- Circuit breakers (all four scopes)
- Warmup scheduling engine
- Google Postmaster Tools integration
- Advanced segmentation engine

**Exit criteria:** 50 active domains, bounce < 1.5%, complaint < 0.05%, zero SES warnings

---

## 14.3 Phase 3 — ML (Months 5–8)

**Target:** 300K–600K sends/day. Self-improving.

- Pre-send spam scorer (Model 1): heuristic → sklearn
- Reply intent classifier (Model 2): seed → production
- Anomaly detection on rolling metrics
- Send-time optimization
- Seed inbox placement testing integration

**Exit criteria:** Both ML models deployed, AUC > 0.85, seed placement > 85% across 3 major providers

---

## 14.4 Phase 4 — 1M/Day (Months 8–12)

**Target:** 600K → 1M+ sends/day. Production-hardened.

- Message & event table partitioning
- Cross-region DR
- SOC 2 Type I readiness
- Advanced analytics & BI export
- Deliverability consulting dashboard

**Exit criteria:** 1M sends/day sustained, 99.95% API availability, 4 SEV-2+ incidents or fewer per quarter
