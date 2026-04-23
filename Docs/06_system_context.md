# System Context

---

## 3.1 Actors

| Actor | Role | Primary interaction |
|---|---|---|
| Operator | Internal user managing campaigns | Web UI |
| Recipient | Email recipient | Receives email, clicks link, replies, unsubscribes |
| On-call engineer | Platform SRE | Runbooks, dashboards, alerts |
| Admin | Platform owner | Platform management, global controls |

---

## 3.2 External Systems

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

---

## 3.3 Data Flows Overview

Five primary data flows carry the bulk of system activity:

- **Provisioning flow:** Operator adds domain → Cloudflare DNS records created → SES identity verified → warmup rotation enrolled.
- **Ingestion flow:** CSV upload → S3 → import worker parses, validates, deduplicates → contacts upserted with provenance → suppression check → list membership applied.
- **Campaign flow:** Operator authors campaign → launch validates sender profile + domain health → segment evaluated → snapshot frozen → batches enqueued → workers drain per-domain.
- **Event flow:** SES fires event → SNS delivers to webhook → event queued → event worker parses → message updated → suppression written → rolling metrics updated → circuit breakers evaluated.
- **Reply flow:** Inbound email → SES inbound → S3 → Lambda → reply classifier → action taken (suppress, route to CRM, re-queue).
