# Sprint 18 — Reply Intent Inbox

**Phase:** ML
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-18-reply-inbox`
**Depends on:** frontend Sprint 10, backend Sprint 18

---

## 1. Purpose

Give the team a triage surface for replies: intent-labeled stream, per-class action review, and a manual override path for low-confidence classifications.

## 2. What Should Be Done

Build `(dashboard)/inbox/page.tsx` and `[replyId]/page.tsx` with intent filters, confidence badges, auto-taken actions, and a human-review queue for low-confidence replies.

## 3. Docs to Follow

- [../12_ml_services.md](../12_ml_services.md) §10.2 (seven intents + actions)
- [../21_domain_model.md](../21_domain_model.md) §2.4 Event & Reputation (`ReplyEvent`)
- [../14_security.md](../14_security.md) — PII handling in reply content

## 4. Tasks

### 4.1 Inbox list
- [ ] Columns: received-at, contact (masked), campaign, intent label + confidence, action taken.
- [ ] Filters: intent class, confidence threshold, has-action, unassigned, date range.
- [ ] Saved-filter presets: "Needs review (< 0.7)", "Positive interest last 24h", "Complaints".

### 4.2 Reply detail
- [ ] Cleaned reply text (quoted history collapsed) + full original (expandable).
- [ ] Model version + feature summary (what drove the intent).
- [ ] Taken actions timeline (`unsubscribe`, `suppression_added`, `notify_owner`).
- [ ] Manual override: pick another intent → trigger the correct action (with audit).

### 4.3 Notifications
- [ ] `positive_interest` and `question` replies notify the assigned user with a link.
- [ ] Low-confidence classifications land in the "Needs review" preset and appear as a badge on the sidebar.

### 4.4 Model feedback
- [ ] Every manual correction flags a training sample.

## 5. Deliverables

- Reply triage moves from "nothing" to "seconds per reply" for the common cases.
- Model gets labeled corrections automatically.

## 6. Exit Criteria

- E2E: low-confidence reply → lands in review → manual reclassify → action triggered → suppression / unsubscribe reflected in contact.
- Auto-unsubscribes from replies are clearly marked and linkable back to the reply.
- a11y clean on inbox + detail.

## 7. Risks to Watch

- Overconfident auto-unsubscribe on ambiguous language. Respect class-specific confidence thresholds from backend config.
- Leaking reply content into logs/telemetry. Redact body before any non-essential logging.
- Inbox becoming unscannable. Default to "Needs review" and last 24h.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/inbox/**`
- Playwright: `tests/e2e/reply_triage.spec.ts`
- axe on inbox
