# Sprint 15 — Warmup Engine & Postmaster Tools

**Phase:** Scale
**Estimated duration:** 1 week
**Branch:** `backend/sprint-15-warmup-postmaster`
**Depends on:** Sprints 12, 13, 14

---

## 1. Purpose

Protect new domains and IPs by ramping traffic gradually instead of dumping full volume on day one. Pair this with Google Postmaster Tools so we can observe the actual reputation impact from the other side of the pipe.

## 2. What Should Be Done

Build `apps/workers/warmup_tasks.py` that computes a daily send budget per domain based on where it is in its warmup schedule, and integrate Google Postmaster Tools as an external signal source.

## 3. Docs to Follow

- [../11_operational_guardrails.md](../11_operational_guardrails.md) §9 (rate limiting + reputation management)
- [../07_functional_requirements.md](../07_functional_requirements.md) §5.1 (warmup)
- [../21_domain_model.md](../21_domain_model.md) §5.4 Domain Reputation Lifecycle

## 4. Tasks

### 4.1 Warmup state
- [ ] `domains.warmup_schedule` JSON column: day-by-day target volumes.
- [ ] `domains.warmup_stage` enum: `none | warming | graduated`.
- [ ] Warmup template generator based on ESP best practices (e.g., 50 → 100 → 500 → 1K → 5K …).

### 4.2 Daily budget & enforcement
- [ ] Nightly task computes today's budget per warming domain.
- [ ] The token bucket's daily cap (Sprint 12) reads from this budget instead of a static value.
- [ ] When budget is exhausted, subsequent messages stay queued until tomorrow.

### 4.3 Graduation
- [ ] After N days under good reputation, mark domain `graduated` and remove warmup cap.
- [ ] If bounce/complaint rates during warmup exceed tighter thresholds, extend warmup by N more days (don't graduate on bad signals).

### 4.4 Google Postmaster Tools
- [ ] OAuth 2.0 flow to authorize the platform's Postmaster account.
- [ ] Daily poll of domain reputation, spam rate, authentication results.
- [ ] Persist into `postmaster_metrics` table.
- [ ] Feed into circuit breaker evaluator as an additional signal.

## 5. Deliverables

- New domains follow a predictable ramp and cannot exceed it.
- Postmaster metrics show up on the domain dashboard, side by side with our own rolling metrics.

## 6. Exit Criteria

- Integration test: a warming domain at day 3 of its schedule cannot exceed the day-3 cap even if requested volume is higher.
- Integration test: Postmaster fetch stores the expected fields and is idempotent on re-runs of the same day.
- Documentation: a runbook page in [../04_operations_runbook.md](../04_operations_runbook.md) describes how to extend a warmup by hand.

## 7. Risks to Watch

- Over-aggressive ramp schedules burning reputation. Start conservative; measure.
- Google Postmaster token expiry — handle refresh; alert on prolonged unauthenticated state.
- Budget + token-bucket interaction bugs. Test the combined behavior explicitly.

## 8. Tests to Run

- `pytest tests/unit/core/domains/test_warmup_schedule.py`
- `pytest tests/integration/workers/test_warmup_tasks.py`
- `pytest tests/integration/core/postmaster/`
