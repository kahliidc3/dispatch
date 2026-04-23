# Sprint 03 — Domains, Sender Profiles & IP Pools

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `backend/sprint-03-sending-identity`
**Depends on:** Sprint 02

---

## 1. Purpose

Deliver the sending identity infrastructure: the domains we send from, the sender profiles (from-address + display name + config set), and the IP pools that group them. MVP uses manual DNS — automation ships in Sprint 14.

## 2. What Should Be Done

Build `libs/core/domains/`, `libs/core/sender_profiles/`, and the IP pool tables. Wire `POST /domains` to create a pending domain, store expected DNS records (SPF, DKIM, DMARC, MX, return-path CNAME), and expose a `/domains/{id}/verify` endpoint that checks current DNS state against expected.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.1 Domain & Sender Management
- [../21_domain_model.md](../21_domain_model.md) §2.1 Identity & Sending Infrastructure
- [../09_data_model.md](../09_data_model.md) — tables `domains`, `domain_dns_records`, `sender_profiles`, `ses_configuration_sets`, `ip_pools`
- [../01_schema.sql](../01_schema.sql) — exact columns and constraints

## 4. Tasks

### 4.1 Domains
- [ ] Models + schemas + repo + service for `Domain` and `DomainDnsRecord`.
- [ ] State machine: `pending → verifying → verified → cooling → burnt → retired`.
- [ ] Expected DNS record generator (SPF, DKIM CNAMEs, DMARC, MAIL FROM).
- [ ] `POST /domains`, `GET /domains`, `GET /domains/{id}`, `POST /domains/{id}/verify`, `POST /domains/{id}/retire`.

### 4.2 SES configuration sets
- [ ] Model + service for `SESConfigurationSet`.
- [ ] Link each domain to at least one config set.
- [ ] Event destination config (SNS topic ARN) stored but provisioned in Sprint 14.

### 4.3 Sender profiles
- [ ] Model + service for `SenderProfile` (from_email, from_name, reply_to, domain_id, ses_config_set_id, ip_pool_id).
- [ ] Uniqueness: `(from_email)` globally unique.
- [ ] `POST /sender-profiles`, `GET /sender-profiles`, `PATCH /sender-profiles/{id}`, `DELETE /sender-profiles/{id}` (soft delete).

### 4.4 IP pools
- [ ] Model + service for `IPPool` (dedicated_ip list, shared pool fallback).
- [ ] Pool assignment to sender profiles.

### 4.5 DNS verification
- [ ] `dns_provisioner/base.py` abstract verify helper (no provisioning yet — read-only DNS lookups via `dnspython`).
- [ ] Background Celery task `verify_domain_dns` that polls and updates `DomainDnsRecord.status`.

## 5. Deliverables

- Admin can add a domain, see the list of DNS records to create, paste them in their DNS provider manually, and click "Verify" to transition the domain to `verified`.
- Sender profile cannot be created against an unverified domain.

## 6. Exit Criteria

- 95%+ coverage on service layer.
- Integration test: create domain → fake DNS with dns stub → verify → status becomes `verified`.
- Invariant test: creating a sender profile for an unverified domain returns 409.
- Audit log entries for domain create / verify / retire.

## 7. Risks to Watch

- DNS caching during verification — use authoritative lookups, not the default resolver.
- Accidentally exposing DKIM private keys in responses; private key material belongs only to SES.
- Naming collisions between `ip_pools` and legacy Mailgun references (already removed — confirm none reappear).

## 8. Tests to Run

- `pytest tests/unit/core/domains/`
- `pytest tests/unit/core/sender_profiles/`
- `pytest tests/integration/api/test_domains_router.py`
- `pytest tests/integration/workers/test_verify_domain_dns.py`
