# Sprint 06 — Templates & Template Versioning

**Phase:** MVP
**Estimated duration:** 4–6 days
**Branch:** `backend/sprint-06-templates`
**Depends on:** Sprint 02

---

## 1. Purpose

Deliver the content layer for campaigns: authorable, versioned email templates with merge-tag support. Campaigns always reference an immutable `TemplateVersion`, never the mutable `Template` head.

## 2. What Should Be Done

Build `libs/core/templates/` with `Template` and `TemplateVersion` models, a renderer that substitutes merge tags with contact fields, and endpoints to create, version-bump, preview, and archive templates.

## 3. Docs to Follow

- [../07_functional_requirements.md](../07_functional_requirements.md) §5.3 Campaign Authoring (templates)
- [../21_domain_model.md](../21_domain_model.md) §2.3 Campaign Management
- [../09_data_model.md](../09_data_model.md) — `templates`, `template_versions`

## 4. Tasks

### 4.1 Models
- [ ] `Template` (head pointer + metadata).
- [ ] `TemplateVersion` (immutable body, subject, from/reply overrides, merge-tag schema).
- [ ] Unique `(template_id, version_number)`.

### 4.2 Authoring API
- [ ] `POST /templates` creates template + v1.
- [ ] `POST /templates/{id}/versions` creates an immutable new version and bumps head.
- [ ] `GET /templates`, `GET /templates/{id}` (includes all versions), `GET /templates/{id}/versions/{n}`.
- [ ] `POST /templates/{id}/archive` (soft).

### 4.3 Rendering
- [ ] Merge-tag renderer with a strict tag grammar (`{{contact.first_name}}`, `{{contact.preferences.plan}}`).
- [ ] Safe rendering: no arbitrary code execution, no SSRF. Use a sandboxed template engine (Jinja2 SandboxedEnvironment with a minimal allow-list).
- [ ] `POST /templates/{id}/preview` with a sample contact payload.

### 4.4 Merge-tag schema
- [ ] When a version is saved, extract required merge tags and store them on the version.
- [ ] Campaigns later validate that snapshots have the required fields.

## 5. Deliverables

- Admin can create and iterate on templates with an audit trail of each version.
- Preview endpoint returns rendered HTML/text with a sample contact.

## 6. Exit Criteria

- Integration test: a template version is immutable once created (server returns 409 on attempted update).
- Security test: Jinja sandbox rejects dangerous constructs (`__class__`, imports, file access).
- Preview works with realistic merge-tag inputs and unicode safely.

## 7. Risks to Watch

- Template engine escape via sandbox bypass. Use the exact Jinja SandboxedEnvironment configuration documented in their security notes; pin version.
- Merge-tag keys that don't exist on the contact — decide policy (reject vs. render empty) and encode in the renderer.
- Subject-line injection (newlines). Strip or reject CRLF in subject fields.

## 8. Tests to Run

- `pytest tests/unit/core/templates/`
- `pytest tests/unit/core/templates/test_renderer_sandbox.py`
- `pytest tests/integration/api/test_templates_router.py`
