# Sprint 04 — Contacts, Lists & Preferences

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `backend/sprint-04-contacts-lists`
**Depends on:** Sprint 02

---

## 1. Purpose

Deliver the audience side of the platform: contacts, the lists they belong to, their subscription status, and their preferences. This is what segmentation and campaigns will later query.

## 2. What Should Be Done

Build `libs/core/contacts/` and `libs/core/lists/`. Enforce the global uniqueness of `contacts.email` (case-insensitive) and the contact lifecycle state machine.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.2 Contact & List Management
- [../21_domain_model.md](../21_domain_model.md) §2.2 Audience, §3.1 Contact Aggregate, §5.3 Contact Lifecycle
- [../09_data_model.md](../09_data_model.md) — tables `contacts`, `lists`, `list_memberships`, `contact_sources`, `preferences`, `subscription_statuses`
- [../01_schema.sql](../01_schema.sql)

## 4. Tasks

### 4.1 Contacts
- [ ] Model + schemas + repo + service.
- [ ] Lifecycle: `active → bounced | complained | unsubscribed | suppressed | deleted`; enforce one-way transitions.
- [ ] `POST /contacts`, `GET /contacts` (paginated, filterable), `GET /contacts/{id}`, `PATCH /contacts/{id}`, `DELETE /contacts/{id}` (GDPR-compliant hard delete).
- [ ] `POST /contacts/{id}/unsubscribe` and public unsubscribe flow (signed token, no auth).

### 4.2 Lists
- [ ] Model + service for `List` and `ListMembership`.
- [ ] `POST /lists`, `GET /lists`, add/remove contacts, bulk add/remove.
- [ ] Prevent a `suppressed`/`unsubscribed` contact from receiving regardless of list membership.

### 4.3 Contact sources & preferences
- [ ] `ContactSource` tracks where a contact came from (CSV import, API, public form).
- [ ] `Preference` stores arbitrary key/value prefs (used later by segments).
- [ ] Endpoints to read/write preferences for a contact.

### 4.4 Invariants
- [ ] DB unique index `lower(email)`.
- [ ] Lifecycle transitions implemented in service layer, not the router.
- [ ] Deleting a contact cascades to list memberships but preserves historical message records.

## 5. Deliverables

- Fully functional contact and list APIs behind the auth layer.
- Public unsubscribe endpoint that works unauthenticated with a signed token.
- CSV import is *not* delivered here — it is Sprint 05's scope. This sprint delivers only single-contact creation.

## 6. Exit Criteria

- 95%+ coverage on `contacts/service.py`.
- Integration test: attempting to set an unsubscribed contact back to active is rejected.
- Integration test: unsubscribe token with a forged signature is rejected.
- Audit log entries for unsubscribe and hard-delete.

## 7. Risks to Watch

- Case sensitivity bugs: enforce `lower(email)` everywhere, not just at insert.
- Accidentally sending to unsubscribed contacts via a missing filter. Every read path feeding send eligibility must filter by lifecycle.
- GDPR erasure: ensure `audit_log` references survive a hard delete, with PII tombstoned.

## 8. Tests to Run

- `pytest tests/unit/core/contacts/`
- `pytest tests/unit/core/lists/`
- `pytest tests/integration/api/test_contacts_router.py`
- `pytest tests/integration/api/test_unsubscribe_flow.py`
