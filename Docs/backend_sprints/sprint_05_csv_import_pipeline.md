# Sprint 05 — CSV Import Pipeline (Gates 1–3)

**Phase:** MVP
**Estimated duration:** 1 week
**Branch:** `backend/sprint-05-csv-import`
**Depends on:** Sprint 04

---

## 1. Purpose

Deliver the ingestion path that gets contacts *into* the platform at scale, with the first three of the seven pre-send validation gates applied at import time so bad addresses never make it near a send task.

## 2. What Should Be Done

Build `libs/core/imports/`, a CSV upload endpoint that writes to S3 (or local Minio in dev), an import Celery task that streams rows, applies Gates 1–3, and upserts contacts. Import results are summarized in an `ImportJob` record.

## 3. Docs to Follow

- [../10_delivery_pipeline.md](../10_delivery_pipeline.md) §Seven-Gate Validation (gates 1–3)
- [../07_functional_requirements.md](../07_functional_requirements.md) §5.2 Contact & List Management (import)
- [../21_domain_model.md](../21_domain_model.md) §2.2 Audience
- [../09_data_model.md](../09_data_model.md) — `import_jobs`, `import_errors`

## 4. Tasks

### 4.1 Upload & job model
- [ ] `POST /imports` accepts multipart CSV, writes object to S3, creates `ImportJob(status='pending')`.
- [ ] `GET /imports/{id}` returns status, counts (total / accepted / rejected / duplicates), sample error rows.

### 4.2 Import worker
- [ ] `apps/workers/import_tasks.py::run_import(job_id)` streams CSV from S3, chunks rows.
- [ ] Idempotent: reload job; return early if `status != 'pending'`.
- [ ] For each row, apply gates in order.

### 4.3 Gate 1 — Format
- [ ] RFC 5321/5322 syntactic check.
- [ ] Reject rows with missing required columns.

### 4.4 Gate 2 — SMTP validation
- [ ] MX record lookup with short timeout; cache per-domain result in Redis.
- [ ] Optional SMTP RCPT TO check (config-flagged; default off in MVP).

### 4.5 Gate 3 — Role-account filter
- [ ] Reject `info@`, `admin@`, `noreply@`, `postmaster@`, etc. List is configurable.

### 4.6 Persistence
- [ ] Upsert contacts respecting the case-insensitive email unique index.
- [ ] Attach a `ContactSource` entry per row with import job reference.
- [ ] Write rejected rows into `import_errors` with a typed reason code.

### 4.7 Observability
- [ ] Log per-batch summary with row counts and timing.
- [ ] Metric: rows/sec and rejection rate by gate.

## 5. Deliverables

- Admin can upload a CSV, see a progress view, and later inspect per-row rejection reasons.
- Gates 1–3 block bad rows before a contact is created.

## 6. Exit Criteria

- Integration test using a fixture CSV with known-good and known-bad rows — exact accepted/rejected counts match expectations.
- A re-run of the same CSV produces zero duplicate contacts.
- Throughput: ≥ 5,000 rows/sec in local integration test (no SMTP probe).
- Audit log entries for job creation and completion.

## 7. Risks to Watch

- DNS amplification risk if an attacker uploads 10M rows with random domains. Cap upload size; per-user concurrent job limit.
- CSV parsing vulnerabilities (CSV injection, quoted newlines). Use Python's `csv` module with strict quoting.
- Slow MX lookups stalling the worker. Bound lookup time aggressively and cache aggressively.

## 8. Tests to Run

- `pytest tests/unit/core/imports/`
- `pytest tests/integration/workers/test_import_tasks.py`
- `pytest tests/integration/api/test_imports_router.py`
