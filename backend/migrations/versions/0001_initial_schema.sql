-- =============================================================================
-- dispatch — High-Volume Email Platform
-- PostgreSQL Schema v1.1
-- =============================================================================
-- Author: Platform Engineering
-- Target: PostgreSQL 15+
-- Conventions:
--   * snake_case for all identifiers
--   * UUIDs for all primary keys (distributed-friendly)
--   * TIMESTAMPTZ for all timestamps (never naive timestamps)
--   * Every table has created_at / updated_at
--   * Soft-delete via deleted_at where reversibility matters
--   * Foreign keys ON DELETE policies explicit per relationship
-- Note: Single-tenant internal platform. No org_id scoping, no plan tiers.
-- =============================================================================

SET search_path TO public;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "citext";         -- case-insensitive email
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- fuzzy search on contacts
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- composite gin indexes

-- =============================================================================
-- SECTION 1 — AUTH
-- =============================================================================

CREATE TABLE users (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT       NOT NULL UNIQUE,
    password_hash   TEXT         NOT NULL,         -- argon2id
    role            TEXT         NOT NULL DEFAULT 'user'
                                 CHECK (role IN ('admin','user')),
    mfa_secret      TEXT,                          -- null when MFA not enabled
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ
);

CREATE TABLE api_keys (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT         NOT NULL,
    key_hash        TEXT         NOT NULL UNIQUE,  -- sha256(secret)
    key_prefix      TEXT         NOT NULL,         -- visible first 8 chars for UI
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    created_by      UUID         NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- =============================================================================
-- SECTION 2 — DOMAIN & SENDER IDENTITY
-- =============================================================================

CREATE TABLE domains (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  TEXT         NOT NULL UNIQUE,  -- e.g. "m47.sendbrand.com"
    parent_domain         TEXT,                          -- "sendbrand.com" for subdomain tracking
    dns_provider          TEXT         NOT NULL CHECK (dns_provider IN ('cloudflare','route53','godaddy','manual')),
    ses_region            TEXT         NOT NULL DEFAULT 'us-east-1',
    ses_identity_arn      TEXT,                          -- set after SES verification
    verification_status   TEXT         NOT NULL DEFAULT 'pending'
                                       CHECK (verification_status IN ('pending','verified','failed','disabled')),
    spf_status            TEXT         NOT NULL DEFAULT 'pending',
    dkim_status           TEXT         NOT NULL DEFAULT 'pending',
    dmarc_status          TEXT         NOT NULL DEFAULT 'pending',
    mail_from_domain      TEXT,                          -- custom MAIL FROM
    custom_tracking_domain TEXT,
    reputation_status     TEXT         NOT NULL DEFAULT 'warming'
                                       CHECK (reputation_status IN ('warming','healthy','cooling','burnt','retired')),
    daily_send_limit      INT          NOT NULL DEFAULT 50,  -- auto-incremented during warmup
    lifetime_sends        BIGINT       NOT NULL DEFAULT 0,
    lifetime_bounces      BIGINT       NOT NULL DEFAULT 0,
    lifetime_complaints   BIGINT       NOT NULL DEFAULT 0,
    warmup_started_at     TIMESTAMPTZ,
    warmup_completed_at   TIMESTAMPTZ,
    retired_at            TIMESTAMPTZ,
    retirement_reason     TEXT,
    metadata              JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_domains_status ON domains(reputation_status);
CREATE INDEX idx_domains_verification ON domains(verification_status) WHERE verification_status != 'verified';

CREATE TABLE domain_dns_records (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id       UUID         NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    record_type     TEXT         NOT NULL CHECK (record_type IN ('TXT','CNAME','MX','A','PTR')),
    name            TEXT         NOT NULL,
    value           TEXT         NOT NULL,
    priority        INT,                           -- for MX records
    purpose         TEXT         NOT NULL CHECK (purpose IN ('spf','dkim','dmarc','mail_from','mx_inbound','verification','tracking')),
    provider_record_id TEXT,                       -- the id returned by Cloudflare/Route53
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    last_verified_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_dns_records_domain ON domain_dns_records(domain_id);

CREATE TABLE ses_configuration_sets (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT         NOT NULL UNIQUE,  -- e.g. "outreach-default"
    ses_region      TEXT         NOT NULL DEFAULT 'us-east-1',
    reputation_metrics_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    sending_enabled BOOLEAN      NOT NULL DEFAULT TRUE,
    tracking_enabled BOOLEAN     NOT NULL DEFAULT FALSE,  -- disabled by default — tracking pixels hurt
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE sender_profiles (
    id                     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name           TEXT         NOT NULL,
    from_name              TEXT         NOT NULL,
    from_email             TEXT         NOT NULL UNIQUE,   -- local-part + domain
    reply_to               TEXT,
    domain_id              UUID         NOT NULL REFERENCES domains(id) ON DELETE RESTRICT,
    configuration_set_id   UUID         REFERENCES ses_configuration_sets(id) ON DELETE SET NULL,
    allowed_campaign_types TEXT[]       NOT NULL DEFAULT '{}',
    is_active              BOOLEAN      NOT NULL DEFAULT TRUE,
    paused_at              TIMESTAMPTZ,
    paused_reason          TEXT,
    daily_send_count       INT          NOT NULL DEFAULT 0,   -- reset nightly
    daily_send_limit       INT          NOT NULL DEFAULT 50,
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_sender_profiles_domain ON sender_profiles(domain_id);
CREATE INDEX idx_sender_profiles_active ON sender_profiles(is_active) WHERE paused_at IS NULL;

CREATE TABLE ip_pools (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT         NOT NULL UNIQUE,
    ses_pool_name   TEXT         NOT NULL,
    traffic_weight  INT          NOT NULL DEFAULT 100,   -- for weighted routing
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- =============================================================================
-- SECTION 3 — CONTACTS, LISTS, SUPPRESSION
-- =============================================================================

CREATE TABLE contacts (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email                 CITEXT       NOT NULL UNIQUE,
    email_domain          TEXT         NOT NULL,         -- derived on insert
    first_name            TEXT,
    last_name             TEXT,
    company               TEXT,
    title                 TEXT,
    phone                 TEXT,
    country_code          TEXT,
    timezone              TEXT,
    custom_attributes     JSONB        NOT NULL DEFAULT '{}'::jsonb,
    lifecycle_status      TEXT         NOT NULL DEFAULT 'active'
                                       CHECK (lifecycle_status IN ('active','bounced','complained','unsubscribed','suppressed','deleted')),
    validation_status     TEXT         NOT NULL DEFAULT 'pending'
                                       CHECK (validation_status IN ('pending','valid','invalid','risky','unknown')),
    validation_score      NUMERIC(3,2),                   -- 0.00 to 1.00
    last_validated_at     TIMESTAMPTZ,
    last_engaged_at       TIMESTAMPTZ,                    -- last open/click/reply
    total_sends           INT          NOT NULL DEFAULT 0,
    total_opens           INT          NOT NULL DEFAULT 0,
    total_clicks          INT          NOT NULL DEFAULT 0,
    total_replies         INT          NOT NULL DEFAULT 0,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at            TIMESTAMPTZ
);

CREATE INDEX idx_contacts_email_domain ON contacts(email_domain);
CREATE INDEX idx_contacts_lifecycle ON contacts(lifecycle_status);
CREATE INDEX idx_contacts_engaged ON contacts(last_engaged_at DESC) WHERE lifecycle_status = 'active';
CREATE INDEX idx_contacts_trgm_email ON contacts USING gin (email gin_trgm_ops);

CREATE TABLE contact_sources (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id      UUID         NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    source_type     TEXT         NOT NULL CHECK (source_type IN ('csv_import','api','webhook','manual','integration')),
    source_detail   TEXT,                                -- e.g. import_job_id, integration name
    source_list     TEXT,                                -- the provenance tag
    ingested_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_contact_sources_contact ON contact_sources(contact_id);

CREATE TABLE subscription_statuses (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id      UUID         NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    channel         TEXT         NOT NULL DEFAULT 'email',
    status          TEXT         NOT NULL CHECK (status IN ('subscribed','unsubscribed','pending','unconfirmed')),
    reason          TEXT,
    effective_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (contact_id, channel)
);

CREATE TABLE preferences (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id      UUID         NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    campaign_types  TEXT[]       NOT NULL DEFAULT '{}',
    max_frequency_per_week INT,
    language        TEXT         DEFAULT 'en',
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (contact_id)
);

-- Suppression is INTENTIONALLY platform-wide and channel-independent.
-- An unsubscribe from any campaign blocks future sends to that address.
CREATE TABLE suppression_entries (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT       NOT NULL UNIQUE,
    reason          TEXT         NOT NULL CHECK (reason IN ('hard_bounce','soft_bounce_limit','complaint','unsubscribe','manual','spam_trap','invalid','global_blocklist')),
    source_event_id UUID,                              -- link to event that caused it
    campaign_id     UUID,                              -- campaign where it originated
    notes           TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ                        -- null = forever (default)
);

CREATE INDEX idx_suppression_reason ON suppression_entries(reason);

-- =============================================================================
-- SECTION 4 — LISTS & SEGMENTS
-- =============================================================================

CREATE TABLE lists (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT         NOT NULL,
    description     TEXT,
    member_count    INT          NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE list_members (
    list_id         UUID         NOT NULL REFERENCES lists(id) ON DELETE CASCADE,
    contact_id      UUID         NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    added_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (list_id, contact_id)
);

CREATE TABLE segments (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT         NOT NULL,
    description     TEXT,
    definition      JSONB        NOT NULL,        -- filter DSL: { and: [ {field,op,value} ] }
    cached_size     INT,
    cached_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- =============================================================================
-- SECTION 5 — IMPORTS
-- =============================================================================

CREATE TABLE import_jobs (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by      UUID         NOT NULL REFERENCES users(id),
    file_name       TEXT         NOT NULL,
    file_s3_key     TEXT         NOT NULL,
    file_size_bytes BIGINT       NOT NULL,
    column_mapping  JSONB        NOT NULL,         -- { "email": "Email Address", ... }
    source_label    TEXT,                          -- provenance tag
    target_list_id  UUID         REFERENCES lists(id) ON DELETE SET NULL,
    status          TEXT         NOT NULL DEFAULT 'queued'
                                 CHECK (status IN ('queued','parsing','validating','upserting','complete','failed','cancelled')),
    total_rows      INT,
    valid_rows      INT          NOT NULL DEFAULT 0,
    invalid_rows    INT          NOT NULL DEFAULT 0,
    duplicate_rows  INT          NOT NULL DEFAULT 0,
    suppressed_rows INT          NOT NULL DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_import_jobs_created ON import_jobs(created_at DESC);

CREATE TABLE import_rows (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    import_job_id   UUID         NOT NULL REFERENCES import_jobs(id) ON DELETE CASCADE,
    row_number      INT          NOT NULL,
    raw_data        JSONB        NOT NULL,
    parsed_email    CITEXT,
    status          TEXT         NOT NULL CHECK (status IN ('valid','invalid','duplicate','suppressed','upserted','errored')),
    contact_id      UUID         REFERENCES contacts(id) ON DELETE SET NULL,
    error_reason    TEXT,
    processed_at    TIMESTAMPTZ
);

CREATE INDEX idx_import_rows_job ON import_rows(import_job_id);

-- =============================================================================
-- SECTION 6 — TEMPLATES & CAMPAIGNS
-- =============================================================================

CREATE TABLE templates (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT         NOT NULL,
    description     TEXT,
    category        TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE template_versions (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id     UUID         NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    version_number  INT          NOT NULL,
    subject         TEXT         NOT NULL,
    body_text       TEXT         NOT NULL,        -- always keep plain text
    body_html       TEXT,                          -- optional, discouraged for outreach
    spintax_enabled BOOLEAN      NOT NULL DEFAULT TRUE,
    merge_tags      TEXT[]       NOT NULL DEFAULT '{}',
    ml_spam_score   NUMERIC(3,2),                  -- computed by Model 1
    is_published    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_by      UUID         NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (template_id, version_number)
);

CREATE TABLE campaigns (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  TEXT         NOT NULL,
    campaign_type         TEXT         NOT NULL CHECK (campaign_type IN ('outreach','transactional','newsletter','drip','reengagement')),
    sender_profile_id     UUID         NOT NULL REFERENCES sender_profiles(id) ON DELETE RESTRICT,
    template_version_id   UUID         NOT NULL REFERENCES template_versions(id) ON DELETE RESTRICT,
    segment_id            UUID         REFERENCES segments(id) ON DELETE SET NULL,
    list_id               UUID         REFERENCES lists(id) ON DELETE SET NULL,
    schedule_type         TEXT         NOT NULL DEFAULT 'immediate'
                                       CHECK (schedule_type IN ('immediate','scheduled','recurring','drip')),
    scheduled_at          TIMESTAMPTZ,
    timezone              TEXT         DEFAULT 'UTC',
    send_rate_per_hour    INT          NOT NULL DEFAULT 100,
    status                TEXT         NOT NULL DEFAULT 'draft'
                                       CHECK (status IN ('draft','scheduled','running','paused','completed','cancelled','failed')),
    tracking_opens        BOOLEAN      NOT NULL DEFAULT FALSE,
    tracking_clicks       BOOLEAN      NOT NULL DEFAULT FALSE,
    total_eligible        INT          NOT NULL DEFAULT 0,
    total_sent            INT          NOT NULL DEFAULT 0,
    total_delivered       INT          NOT NULL DEFAULT 0,
    total_bounced         INT          NOT NULL DEFAULT 0,
    total_complained      INT          NOT NULL DEFAULT 0,
    total_opened          INT          NOT NULL DEFAULT 0,
    total_clicked         INT          NOT NULL DEFAULT 0,
    total_replied         INT          NOT NULL DEFAULT 0,
    total_unsubscribed    INT          NOT NULL DEFAULT 0,
    created_by            UUID         NOT NULL REFERENCES users(id),
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    started_at            TIMESTAMPTZ,
    completed_at          TIMESTAMPTZ
);

CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_scheduled ON campaigns(scheduled_at) WHERE status = 'scheduled';

CREATE TABLE campaign_runs (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id     UUID         NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    run_number      INT          NOT NULL,
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    eligible_count  INT,
    sent_count      INT          NOT NULL DEFAULT 0,
    status          TEXT         NOT NULL DEFAULT 'running',
    UNIQUE (campaign_id, run_number)
);

-- Segment snapshot: the exact audience frozen at campaign launch
-- Storing this is critical for reproducibility and audit
CREATE TABLE segment_snapshots (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_run_id  UUID         NOT NULL REFERENCES campaign_runs(id) ON DELETE CASCADE,
    contact_id       UUID         NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    included         BOOLEAN      NOT NULL,
    exclusion_reason TEXT,                          -- 'suppressed','unsubscribed','invalid', etc.
    frozen_attributes JSONB       NOT NULL DEFAULT '{}'::jsonb,  -- contact data at launch
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (campaign_run_id, contact_id)
);

CREATE INDEX idx_segment_snapshots_run ON segment_snapshots(campaign_run_id) WHERE included = TRUE;

-- =============================================================================
-- SECTION 7 — EXECUTION: BATCHES & MESSAGES
-- =============================================================================

CREATE TABLE send_batches (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_run_id   UUID         NOT NULL REFERENCES campaign_runs(id) ON DELETE CASCADE,
    batch_number      INT          NOT NULL,
    batch_size        INT          NOT NULL,
    sender_profile_id UUID         NOT NULL REFERENCES sender_profiles(id),
    ip_pool_id        UUID         REFERENCES ip_pools(id),
    status            TEXT         NOT NULL DEFAULT 'queued'
                                   CHECK (status IN ('queued','sending','complete','failed','cancelled')),
    enqueued_at       TIMESTAMPTZ,
    started_at        TIMESTAMPTZ,
    completed_at      TIMESTAMPTZ,
    UNIQUE (campaign_run_id, batch_number)
);

-- messages is the largest table. Expect billions of rows in production.
-- Partitioning by created_at is recommended at scale.
CREATE TABLE messages (
    id                   UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id          UUID         REFERENCES campaigns(id) ON DELETE SET NULL,
    send_batch_id        UUID         REFERENCES send_batches(id) ON DELETE SET NULL,
    contact_id           UUID         REFERENCES contacts(id) ON DELETE SET NULL,
    sender_profile_id    UUID         NOT NULL REFERENCES sender_profiles(id),
    domain_id            UUID         NOT NULL REFERENCES domains(id),
    to_email             CITEXT       NOT NULL,
    from_email           TEXT         NOT NULL,
    subject              TEXT         NOT NULL,
    ses_message_id       TEXT,                       -- returned by SES, globally unique
    status               TEXT         NOT NULL DEFAULT 'queued'
                                      CHECK (status IN ('queued','sending','sent','delivered','bounced','complained','failed','skipped')),
    ml_spam_score        NUMERIC(3,2),
    personalization_score NUMERIC(3,2),
    headers              JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    sent_at              TIMESTAMPTZ,
    delivered_at         TIMESTAMPTZ,
    first_opened_at      TIMESTAMPTZ,
    first_clicked_at     TIMESTAMPTZ,
    replied_at           TIMESTAMPTZ,
    bounce_type          TEXT,
    complaint_type       TEXT,
    error_code           TEXT,
    error_message        TEXT
);

CREATE INDEX idx_messages_ses_id ON messages(ses_message_id) WHERE ses_message_id IS NOT NULL;
CREATE INDEX idx_messages_campaign ON messages(campaign_id, created_at DESC);
CREATE INDEX idx_messages_contact ON messages(contact_id, created_at DESC);
CREATE INDEX idx_messages_status ON messages(status, created_at DESC);
CREATE INDEX idx_messages_to_email ON messages(to_email, created_at DESC);

CREATE TABLE message_tags (
    message_id      UUID         NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tag_key         TEXT         NOT NULL,
    tag_value       TEXT         NOT NULL,
    PRIMARY KEY (message_id, tag_key)
);

-- =============================================================================
-- SECTION 8 — EVENTS (from SES via SNS)
-- =============================================================================

-- All event tables share this structural pattern.
-- Denormalized: we duplicate message_id + timestamp for fast range scans.

CREATE TABLE delivery_events (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID         NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    occurred_at     TIMESTAMPTZ  NOT NULL,
    smtp_response   TEXT,
    processing_time_ms INT,
    raw_payload     JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_delivery_events_message ON delivery_events(message_id);
CREATE INDEX idx_delivery_events_time ON delivery_events(occurred_at DESC);

CREATE TABLE bounce_events (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID         NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    occurred_at     TIMESTAMPTZ  NOT NULL,
    bounce_type     TEXT         NOT NULL CHECK (bounce_type IN ('Permanent','Transient','Undetermined')),
    bounce_subtype  TEXT,
    diagnostic_code TEXT,
    raw_payload     JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_bounce_events_message ON bounce_events(message_id);
CREATE INDEX idx_bounce_events_time ON bounce_events(occurred_at DESC);

CREATE TABLE complaint_events (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id       UUID         NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    occurred_at      TIMESTAMPTZ  NOT NULL,
    complaint_type   TEXT,
    user_agent       TEXT,
    feedback_type    TEXT,
    raw_payload      JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_complaint_events_message ON complaint_events(message_id);
CREATE INDEX idx_complaint_events_time ON complaint_events(occurred_at DESC);

CREATE TABLE open_events (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID         NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    occurred_at     TIMESTAMPTZ  NOT NULL,
    user_agent      TEXT,
    ip_address      INET,
    is_machine_open BOOLEAN      NOT NULL DEFAULT FALSE,  -- Gmail proxy detection
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_open_events_message ON open_events(message_id);

CREATE TABLE click_events (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID         NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    occurred_at     TIMESTAMPTZ  NOT NULL,
    link_url        TEXT         NOT NULL,
    user_agent      TEXT,
    ip_address      INET,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_click_events_message ON click_events(message_id);

CREATE TABLE unsubscribe_events (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID         REFERENCES messages(id) ON DELETE SET NULL,
    contact_id      UUID         NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    occurred_at     TIMESTAMPTZ  NOT NULL,
    method          TEXT         NOT NULL CHECK (method IN ('one_click','preference_center','reply','manual','api')),
    campaign_id     UUID         REFERENCES campaigns(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_unsub_events_contact ON unsubscribe_events(contact_id);

CREATE TABLE reply_events (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID         REFERENCES messages(id) ON DELETE SET NULL,
    contact_id      UUID         REFERENCES contacts(id) ON DELETE SET NULL,
    occurred_at     TIMESTAMPTZ  NOT NULL,
    from_email      TEXT         NOT NULL,
    subject         TEXT,
    body_text       TEXT,
    intent_class    TEXT,                           -- Model 2 output
    intent_confidence NUMERIC(3,2),
    s3_raw_key      TEXT,                           -- original mime stored in S3
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_reply_events_contact ON reply_events(contact_id);

-- =============================================================================
-- SECTION 9 — OPERATIONAL: RATE LIMITS, CIRCUIT BREAKERS, AUDIT
-- =============================================================================

CREATE TABLE circuit_breaker_state (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type          TEXT         NOT NULL CHECK (scope_type IN ('domain','ip_pool','account','sender_profile')),
    scope_id            UUID         NOT NULL,
    state               TEXT         NOT NULL DEFAULT 'closed'
                                     CHECK (state IN ('closed','half_open','open')),
    bounce_rate_24h     NUMERIC(5,4),
    complaint_rate_24h  NUMERIC(5,4),
    tripped_at          TIMESTAMPTZ,
    tripped_reason      TEXT,
    auto_reset_at       TIMESTAMPTZ,
    manually_reset_by   UUID         REFERENCES users(id),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (scope_type, scope_id)
);

CREATE INDEX idx_cb_state_open ON circuit_breaker_state(state) WHERE state != 'closed';

-- Rolling metrics: computed every 5 minutes, used by circuit breakers and dashboards
CREATE TABLE rolling_metrics (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type      TEXT         NOT NULL,
    scope_id        UUID         NOT NULL,
    "window"        TEXT         NOT NULL CHECK ("window" IN ('1h','6h','24h','7d','30d')),
    window_end      TIMESTAMPTZ  NOT NULL,
    sends           INT          NOT NULL DEFAULT 0,
    deliveries      INT          NOT NULL DEFAULT 0,
    bounces         INT          NOT NULL DEFAULT 0,
    complaints      INT          NOT NULL DEFAULT 0,
    opens           INT          NOT NULL DEFAULT 0,
    clicks          INT          NOT NULL DEFAULT 0,
    replies         INT          NOT NULL DEFAULT 0,
    unsubscribes    INT          NOT NULL DEFAULT 0,
    bounce_rate     NUMERIC(5,4) GENERATED ALWAYS AS (CASE WHEN sends = 0 THEN 0 ELSE bounces::numeric / sends END) STORED,
    complaint_rate  NUMERIC(5,4) GENERATED ALWAYS AS (CASE WHEN sends = 0 THEN 0 ELSE complaints::numeric / sends END) STORED,
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (scope_type, scope_id, "window")
);

CREATE INDEX idx_rolling_metrics_scope ON rolling_metrics(scope_type, scope_id);

CREATE TABLE audit_log (
    id              BIGSERIAL    PRIMARY KEY,
    actor_type      TEXT         NOT NULL CHECK (actor_type IN ('user','api_key','system')),
    actor_id        UUID,
    action          TEXT         NOT NULL,       -- 'campaign.launch','domain.create',...
    resource_type   TEXT         NOT NULL,
    resource_id     UUID,
    before_state    JSONB,
    after_state     JSONB,
    ip_address      INET,
    user_agent      TEXT,
    occurred_at     TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_time ON audit_log(occurred_at DESC);
CREATE INDEX idx_audit_actor ON audit_log(actor_id, occurred_at DESC);

-- =============================================================================
-- SECTION 10 — ML FEATURE STORE
-- =============================================================================

CREATE TABLE contact_ml_features (
    contact_id              UUID         PRIMARY KEY REFERENCES contacts(id) ON DELETE CASCADE,
    fatigue_score           NUMERIC(3,2),
    complaint_risk          NUMERIC(3,2),
    bounce_risk             NUMERIC(3,2),
    engagement_score        NUMERIC(3,2),
    best_send_hour_utc      SMALLINT,
    best_send_day_of_week   SMALLINT,
    domain_trust_score      NUMERIC(3,2),
    computed_at             TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE template_ml_scores (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    template_version_id UUID         NOT NULL REFERENCES template_versions(id) ON DELETE CASCADE,
    spam_score          NUMERIC(3,2) NOT NULL,
    feature_contributions JSONB      NOT NULL DEFAULT '{}'::jsonb,
    model_version       TEXT         NOT NULL,
    computed_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (template_version_id, model_version)
);

CREATE TABLE anomaly_alerts (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    scope_type      TEXT         NOT NULL,
    scope_id        UUID         NOT NULL,
    metric          TEXT         NOT NULL,
    severity        TEXT         NOT NULL CHECK (severity IN ('info','warning','critical')),
    message         TEXT         NOT NULL,
    observed_value  NUMERIC,
    expected_value  NUMERIC,
    acknowledged_by UUID         REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_anomaly_open ON anomaly_alerts(severity) WHERE resolved_at IS NULL;

-- =============================================================================
-- SECTION 11 — TRIGGERS: updated_at auto-maintenance
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT table_name FROM information_schema.columns
           WHERE column_name = 'updated_at' AND table_schema = 'public'
  LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_%s_updated_at ON %I;', t, t);
    EXECUTE format('CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %I
                    FOR EACH ROW EXECUTE FUNCTION set_updated_at();', t, t);
  END LOOP;
END $$;

-- =============================================================================
-- SECTION 12 — MATERIALIZED VIEWS FOR DASHBOARDS
-- =============================================================================

CREATE MATERIALIZED VIEW mv_domain_health AS
SELECT
    d.id AS domain_id,
    d.name,
    d.reputation_status,
    COALESCE(rm.sends, 0) AS sends_24h,
    COALESCE(rm.bounce_rate, 0) AS bounce_rate_24h,
    COALESCE(rm.complaint_rate, 0) AS complaint_rate_24h,
    cb.state AS breaker_state,
    d.updated_at
FROM domains d
LEFT JOIN rolling_metrics rm ON rm.scope_type = 'domain' AND rm.scope_id = d.id AND rm."window" = '24h'
LEFT JOIN circuit_breaker_state cb ON cb.scope_type = 'domain' AND cb.scope_id = d.id;

CREATE UNIQUE INDEX ON mv_domain_health (domain_id);

-- Refresh policy: every 5 minutes via pg_cron or application scheduler

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
