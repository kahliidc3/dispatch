# Acmemail — Project Overview

## What This Is

You're building a high-volume email sending platform — your own internal ESP. Instead of paying Instantly, Smartlead, or Lemlist per lead, you own the full stack: you manage the sending domains, the contact lists, the campaigns, the deliverability guardrails, and the event pipeline. AWS SES handles the actual SMTP transport; you handle everything else.

The goal is to reach **1 million emails/day to inbox** — not spam folder — by treating deliverability as an operational discipline: rotating domain pools, warming up IPs, killing bad domains automatically before they burn your SES account, and processing every bounce/complaint in real time to protect reputation.

## What It Is Not

- Not a SaaS or multi-tenant product — single namespace, no organizations table, no plan tiers, no role hierarchy beyond your own team
- Not a replacement for transactional email (Postmark, SES direct) — optimized for outreach and newsletter-style campaigns
- Not a bring-your-own-domain setup — you provision and control every sending domain so you can enforce warmup and rotation

## How It Works

**Control plane (you build):**
- Domain provisioning and warmup scheduling — domains are created via API, DNS records published to Cloudflare, and send volume ramped automatically over 4–8 weeks
- Contact and list management — contacts imported from CSV or API, validated, deduplicated, and tracked with full provenance
- Campaign authoring and launch — select sender, template, list/segment, schedule, and rate limit; campaigns can be paused and resumed mid-send
- Suppression and compliance — every bounce, complaint, and unsubscribe writes to the suppression table in real time, and is cross-checked before every send
- Analytics and reputation — per-domain health metrics, circuit breaker state, Google Postmaster reputation, and seed inbox placement scores surfaced in dashboards
- ML layer — pre-send spam scoring, reply intent classification, anomaly detection, and send-time optimization (phased in after MVP)

**Delivery plane (you rent):**
- AWS SES is the sole SMTP backbone — you never touch raw SMTP
- SES fires events (bounces, complaints, opens, clicks) to SNS, which POSTs to your webhook receiver, which writes suppression and metrics in real time

## The Core Deliverability Thesis

Inbox placement at scale is not a configuration problem — it is an **operational discipline problem**. SPF/DKIM/DMARC and correct headers are table stakes. The decisive signals are:

- **Recipient behavior** — opens, clicks, replies, moves from spam = positive; ignores = neutral; complaints = reputation killer
- **Bounce rate** — kept below 1.5% per domain (SES warns at 5%, by which point damage is already done)
- **Complaint rate** — kept below 0.05% per domain (Gmail's hard enforcement threshold is 0.3%)
- **Rate pattern** — sudden volume spikes trigger spam filters; warmup and token-bucket throttling enforce a gradual ramp
- **List quality** — bad addresses burn domains; seven-gate pre-send validation catches problems before they reach SES

The system invests heavily in automated circuit breakers that pause sending at the domain, IP pool, or account level the moment health metrics exceed thresholds — before the problem escalates to SES account review.

## Tech Stack Summary

| Layer | Technology |
|---|---|
| API | Python 3.12 + FastAPI |
| Workers / queues | Celery + Redis |
| Database | PostgreSQL 15+ |
| Email transport | AWS SES (boto3) |
| DNS | Cloudflare API |
| Frontend | Next.js 14 + TypeScript |
| Infrastructure | AWS ECS Fargate + Terraform |
| Observability | Datadog |

## Companion Documents

- [02_system_design.md](02_system_design.md) — full architecture, data model, delivery pipeline, guardrails, ML, deployment, security
- [03_code_architecture.md](03_code_architecture.md) — engineering standards, service layer pattern, testing strategy, code conventions
- [04_operations_runbook.md](04_operations_runbook.md) — incident response, operational procedures, capacity planning
- `01_schema.sql` — complete database schema (39 tables)
