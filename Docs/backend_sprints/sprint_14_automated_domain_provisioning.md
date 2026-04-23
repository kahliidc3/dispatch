# Sprint 14 — Automated Domain Provisioning

**Phase:** Scale
**Estimated duration:** 1.5 weeks
**Branch:** `backend/sprint-14-domain-provisioning`
**Depends on:** Sprint 03

---

## 1. Purpose

Replace manual DNS setup with end-to-end automation. Admin clicks "Provision" → the platform creates SES identities, writes the required DNS records via Cloudflare/Route 53 APIs, and verifies them. This is the unlock for getting to 50 active domains.

## 2. What Should Be Done

Build `libs/dns_provisioner/` with Cloudflare and Route 53 drivers sharing a common interface. Add SES identity creation, DKIM enabling, MAIL FROM domain setup, and a provisioning Celery task that orchestrates the full flow with retries and rollback.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.1 Domain & Sender Management (automation)
- [../16_rollout_plan.md](../16_rollout_plan.md) §14.2 Phase 2
- [../13_deployment_infrastructure.md](../13_deployment_infrastructure.md) — secrets management for provider API keys
- [../14_security.md](../14_security.md) — API key storage, KMS encryption

## 4. Tasks

### 4.1 Provisioner abstraction
- [ ] `libs/dns_provisioner/base.py`: `DNSProvisioner` protocol with `create_record`, `update_record`, `delete_record`, `verify_record`, `list_zones`.
- [ ] Error taxonomy: `AuthenticationError`, `RateLimitedError`, `ZoneNotFoundError`, `RecordExistsError`.

### 4.2 Cloudflare driver
- [ ] API client using Cloudflare's REST API with token-based auth stored in AWS Secrets Manager.
- [ ] Idempotent upserts (look up by name+type first).

### 4.3 Route 53 driver
- [ ] boto3-based client that accepts a hosted zone ID.
- [ ] Batch changes via `ChangeResourceRecordSets`.

### 4.4 SES identity automation
- [ ] `create_email_identity` + DKIM signing attributes.
- [ ] Create dedicated `ConfigurationSet` per domain with SNS event destination pre-wired.
- [ ] Configure MAIL FROM domain for bounce handling.

### 4.5 Provisioning workflow
- [ ] `provision_domain` Celery task with steps: create SES identity → fetch DKIM tokens → create DNS records → poll SES `IdentityVerificationStatus` → poll DKIM `SigningEnabled` → update domain state to `verified`.
- [ ] Idempotent re-runs safe; partial failures leave the domain in `provisioning_failed` with a typed reason.
- [ ] Rollback helper: `retire_domain` deletes DNS records and SES identity.

### 4.6 API
- [ ] `POST /domains/{id}/provision` enqueues the workflow.
- [ ] `GET /domains/{id}/provisioning-status` returns the step log.

## 5. Deliverables

- End-to-end: admin adds domain → selects DNS provider → clicks provision → 3–5 minutes later the domain is `verified` with no human DNS edit.
- Works against a real sandbox Cloudflare zone and a real SES sandbox identity.

## 6. Exit Criteria

- Integration test (recorded HTTP fixtures) covers both Cloudflare and Route 53 happy paths.
- Chaos test: inject a failure at every step; the workflow either recovers or surfaces a typed failure state.
- Secrets for provider APIs are only read from Secrets Manager, never logged, never returned in responses.
- Provisioning throughput: 10 domains in parallel without API key throttling.

## 7. Risks to Watch

- Cloudflare/AWS API rate limits — respect `Retry-After` and cap concurrency.
- Zone misconfiguration (wrong CNAME target) that passes SES verification but fails DMARC in production. Run a post-verify DMARC alignment check.
- Secret leakage — add a log scrub for known secret patterns and a test that fails if any secret is logged.

## 8. Tests to Run

- `pytest tests/unit/dns_provisioner/`
- `pytest tests/integration/dns_provisioner/test_cloudflare.py`
- `pytest tests/integration/dns_provisioner/test_route53.py`
- `pytest tests/integration/workers/test_provision_domain_flow.py`
