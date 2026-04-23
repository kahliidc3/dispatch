# Sprint 07 — Segments & Segment Snapshots

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `backend/sprint-07-segments`
**Depends on:** Sprints 04 (contacts) and 06 (templates)

---

## 1. Purpose

Deliver the audience-selection layer. Segments define "who can receive this campaign" via a safe query DSL; segment snapshots freeze that selection at campaign launch so the audience cannot change underneath a running campaign.

## 2. What Should Be Done

Build `libs/core/segments/` with a typed query DSL (JSON predicates compiled to SQL via SQLAlchemy), a preview endpoint that returns counts and a sample, and a snapshot service that writes append-only `SegmentSnapshot` rows when a campaign launches.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.3 Campaign Authoring (segments)
- [../09_data_model.md](../09_data_model.md) — `segments`, `segment_snapshots` (append-only invariant)
- [../21_domain_model.md](../21_domain_model.md) §2.2 Audience, §3.2 Campaign Aggregate

## 4. Tasks

### 4.1 Segment DSL
- [ ] JSON predicate format with typed operators: `eq`, `neq`, `in`, `gt`, `lt`, `contains`, `and`, `or`, `not`.
- [ ] Allowed fields declared in an explicit allow-list (contact columns + preference keys + subscription fields).
- [ ] Compile DSL → SQLAlchemy `Select` with no string interpolation.

### 4.2 Models & CRUD
- [ ] `Segment` with `name`, `dsl_json`, `last_computed_count`, `last_computed_at`.
- [ ] Endpoints: create, list, get, update (versioned under the hood), delete (soft).
- [ ] `POST /segments/{id}/preview` → count + sample of 50 contacts.

### 4.3 Snapshots
- [ ] `SegmentSnapshot` (append-only) stores the exact contact IDs at a point in time.
- [ ] DB-level trigger or app-level guard that rejects UPDATE / DELETE on `segment_snapshots`.
- [ ] `freeze_segment(segment_id, campaign_run_id)` service: runs the compiled query with `FOR UPDATE` semantics and writes rows in chunks.

### 4.4 Suppression integration
- [ ] Every segment preview and every snapshot excludes suppressed, unsubscribed, and hard-bounced contacts.
- [ ] Snapshot size and exclusion counts recorded on the campaign run.

## 5. Deliverables

- Admin can author a segment, preview its size, and reuse it across campaigns.
- Snapshot service is fast enough to freeze 1M contacts in under 60 seconds.

## 6. Exit Criteria

- Integration test: DSL compiler rejects unknown fields and non-allow-listed operators.
- Integration test: attempting to UPDATE or DELETE a snapshot row fails at the DB level.
- Load test: snapshot of 1M contacts completes ≤ 60s on integration DB.
- Security test: DSL cannot express arbitrary SQL; fuzz with hostile payloads.

## 7. Risks to Watch

- SQL injection through DSL. Never pass user-provided field names or operators through a string — always map through allow-lists.
- Memory blowup on preview queries. Apply hard `LIMIT` on preview and stream snapshots in batches.
- Race: a contact unsubscribes during snapshot freeze. Enforce the filter *inside* the freeze query; do not post-filter.

## 8. Tests to Run

- `pytest tests/unit/core/segments/test_dsl_compiler.py`
- `pytest tests/integration/core/segments/test_snapshot_freeze.py`
- `pytest tests/integration/db/test_segment_snapshot_append_only.py`
- `pytest tests/integration/api/test_segments_router.py`
