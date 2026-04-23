# Security

---

## 12.1 Authentication & Authorization

- **UI auth:** email + password (Argon2id) + TOTP MFA. Sessions via server-side store.
- **API auth:** API keys (sha256 hashed). Key prefix visible in UI; secret shown once at creation.
- **Service-to-service:** IAM roles (ECS task roles). No long-lived credentials in containers.
- **Authorization:** role-based (admin / user). No cross-user data scoping required.
- **Audit:** every authentication event and permission change logged to `audit_log`.

---

## 12.2 Secrets Management

- AWS Secrets Manager for: database credentials, SES SMTP credentials, third-party API keys
- Automatic rotation: 90 days for DB, 90 days for SES SMTP, 180 days for DNS API tokens
- Secrets injected at container start via IAM role — never baked into images, never in env vars passed via CLI
- `.env` files in local development only; not committed
- Pre-commit hook scans for leaked secrets (truffleHog)

---

## 12.3 Data Protection

- **At rest:** RDS with KMS CMK encryption; S3 SSE-KMS; EBS volumes encrypted
- **In transit:** TLS 1.2+ enforced; internal services use service mesh mTLS (future)
- **In logs:** email addresses hashed; no passwords/tokens; PII scrubbed via structlog processor
- **Right to erasure (GDPR):** contact deletion propagates to messages (soft nullify `contact_id`), events (retained, `contact_id` set to `NULL`)
