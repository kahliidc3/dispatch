# Sprint 07 — Segment Builder

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `frontend/sprint-07-segment-builder`
**Depends on:** frontend Sprint 04, backend Sprint 07

---

## 1. Purpose

Turn the segment DSL into a visual audience builder. Users build predicates with dropdowns, not JSON, and get instant size previews. This is the UI that makes segmentation accessible without training.

## 2. What Should Be Done

Build `(dashboard)/segments/` with a list and a builder. The builder compiles user choices into the backend's allow-listed DSL and calls the preview endpoint for size + sample.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.3 (segmentation)
- [../21_domain_model.md](../21_domain_model.md) §2.2, §3.2
- [../09_data_model.md](../09_data_model.md) — segments

## 4. Tasks

### 4.1 Segment list
- [ ] `segments/page.tsx` table with name, last-computed count, last-computed at, owner.
- [ ] Create / duplicate / archive actions.

### 4.2 Visual builder
- [ ] `segments/[id]/page.tsx` builder Client Component.
- [ ] Group/operator/predicate tree UI (and/or nesting).
- [ ] Fields list pulled from backend allow-list (lifecycle, source, preferences, subscription, recent-event).
- [ ] Operators gated by field type.

### 4.3 Preview
- [ ] Live preview (debounced): size count + sample 50 contacts.
- [ ] Suppressed / unsubscribed / hard-bounced excluded from preview counts; display exclusion breakdown.

### 4.4 Save
- [ ] Save validates DSL against the same schema the backend uses.
- [ ] Saved segments are read-only if used by an active campaign run (server-enforced).

## 5. Deliverables

- Operators can build, preview, and save a non-trivial segment without writing JSON.
- Segment preview reflects current suppression accurately.

## 6. Exit Criteria

- E2E: build 3-level nested predicate → preview count matches backend's count.
- UI rejects unknown fields / unsupported operators before calling the API.
- a11y: builder is keyboard-navigable; focus management on add/remove is correct.

## 7. Risks to Watch

- UI and backend DSL schemas diverging. Generate the TS type from the backend's JSON schema (contract-first).
- Runaway previews on every keystroke. Debounce and cancel in-flight requests.
- Sharing segment links with embedded DSL in URL hitting URL length limits; use ID-based deep links once saved.

## 8. Tests to Run

- `pnpm test src/app/(dashboard)/segments/**`
- Playwright: `tests/e2e/segment_builder.spec.ts`
- axe on builder
