# Operational Guardrails

---

## 9.1 Circuit Breakers

Circuit breakers exist at four scopes. Each scope has its own thresholds. Breakers operate independently — a tripped domain breaker does not trip the account breaker.

| Scope | Trip threshold (24h) | Response | Auto-reset |
|---|---|---|---|
| Domain | Bounce > 1.5% OR Complaint > 0.05% | Pause domain queue | After 24h of clean metrics |
| IP pool | Bounce > 2% OR Complaint > 0.07% | Pause pool | Manual after investigation |
| Sender profile | Bounce > 1.5% OR Complaint > 0.05% | Pause profile | Manual |
| Account | Bounce > 2.5% OR Complaint > 0.08% | Pause all sending, alert on-call | Manual only |

> **Why half the ESP's warning level?** AWS SES warns at 5% bounce / 0.1% complaint. We trip our breakers at 1.5% / 0.05%. By the time AWS issues a warning, domain-level reputation damage has already accumulated at Gmail and Outlook — damage that persists for weeks.

---

## 9.2 Rate Limiting

- **Per-domain:** Redis token bucket, enforced inside the send task. Default 150/hour, ramps during warmup.
- **Per-IP-pool:** aggregate rate limit, prevents any single campaign from dominating a pool.
- **Platform-wide:** daily send cap configurable in settings. Blocks enqueue (not send) when exceeded.

---

## 9.3 Fallback Routing

No fallback ESP is configured. AWS SES is the sole sending backbone. In the event of an SES account suspension, the response is to open an AWS support case and halt sending until reinstated — not to route to a secondary provider. See the operations runbook (§4.3) for the full SES suspension procedure.
