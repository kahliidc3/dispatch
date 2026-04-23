# Sprint 21 — DR, SOC 2 Readiness & Security Hardening

**Phase:** 1M/Day
**Estimated duration:** 2 weeks
**Branch:** `backend/sprint-21-dr-soc2`
**Depends on:** all previous sprints

---

## 1. Purpose

Bring the platform to production hardness: cross-region disaster recovery, SOC 2 Type I readiness, and a final security audit pass. This is the last backend sprint before the platform is considered GA.

## 2. What Should Be Done

Stand up cross-region RDS read replicas and a DR runbook. Complete the SOC 2 control checklist (access reviews, change management, incident response, data classification). Run a full security review with an external or internal red team.

## 3. Docs to Follow

- [../14_security.md](../14_security.md) — full security spec
- [../13_deployment_infrastructure.md](../13_deployment_infrastructure.md) — DR topology
- [../04_operations_runbook.md](../04_operations_runbook.md) — incident response
- [../08_non_functional_requirements.md](../08_non_functional_requirements.md) §Availability, §Durability, §Compliance

## 4. Tasks

### 4.1 Disaster recovery
- [ ] Cross-region read replica for RDS with documented promotion procedure.
- [ ] S3 cross-region replication for message artifacts and archives.
- [ ] Redis: documented rebuild procedure (it is cache, not source of truth).
- [ ] Terraform for a warm-standby region (load balancer + ECS services at 0 desired count).
- [ ] DR game day: measured RTO and RPO.

### 4.2 SOC 2 readiness
- [ ] Access control: annual review script, role matrix, least-privilege audit of IAM.
- [ ] Change management: PR approval policy enforced by CI (no self-merges to `main`).
- [ ] Incident response: template post-mortem, on-call schedule, SEV-1 runbook exercise.
- [ ] Data classification: tag every table column; PII columns have documented retention.
- [ ] Vendor list with security review for each (AWS, Cloudflare, Postmaster Tools, etc.).
- [ ] Evidence collection automation where possible.

### 4.3 Security hardening
- [ ] Secret rotation: every provider API key and DB password rotatable via automation.
- [ ] Dependency scan: SBOM + automated CVE scanning in CI.
- [ ] Static analysis: run bandit, semgrep; triage findings.
- [ ] API key usage review: cap per-key rate; expire unused keys.
- [ ] Row-level security audit: confirm no path leaks data across the internal surface.

### 4.4 Final audit
- [ ] Threat model refresh (STRIDE pass on the whole architecture).
- [ ] Penetration test — external or internal team.
- [ ] Close out any findings above "informational."

## 5. Deliverables

- Working DR plan with measured RTO ≤ 4h and RPO ≤ 15 min.
- SOC 2 control evidence package.
- Clean security review with no open high-severity findings.

## 6. Exit Criteria

- DR game day completed with timings meeting the RTO/RPO targets.
- SOC 2 Type I readiness package reviewed by compliance.
- Penetration test findings triaged; no `high` or `critical` left open.
- 1M sends/day sustained run with 99.95% API availability over 14 days.
- SEV-2+ incident rate ≤ 4 per quarter (exit criterion of Phase 4).

## 7. Risks to Watch

- DR plan that looks good on paper but fails under real pressure. Game-day is non-optional.
- Compliance scope creep — stay at Type I, defer Type II.
- Secret rotation breaking live systems. Rotate in staging first, every time.
- Pen test findings landing on an already-shipped surface. Reserve time in the sprint for remediation.

## 8. Tests to Run

- `pytest tests/integration/dr/test_replica_promotion_dry_run.py`
- `pytest tests/integration/security/test_api_key_scope.py`
- Full regression test suite (unit + integration + e2e).
- Manual DR game day and pen test (tracked outside the test suite).
