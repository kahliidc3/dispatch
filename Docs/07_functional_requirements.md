# Functional Requirements

---

## 5.1 Domain & Sender Management

- **Automated domain provisioning:** operator requests N domains, system creates DNS records in Cloudflare, initializes SES identity, enrolls in warmup schedule
- **Continuous warmup:** every active domain has its send count ramped over 4–8 weeks per the warmup schedule (defined in the operations runbook)
- **Domain retirement:** when reputation drops below thresholds, domain is marked burnt and removed from rotation automatically
- **Sender profile management:** each domain hosts multiple sender profiles (From address + display name + reply-to) tied to a configuration set
- **Per-profile daily limits:** enforced by rate limiter, reset nightly
- **Sender validation:** every send runs the pre-flight check listed in the Delivery Pipeline doc (§8.1)

---

## 5.2 Contact & List Management

- Contacts are keyed by `email` with case-insensitive matching
- Every contact has provenance: at least one `contact_sources` row identifying how they entered the system
- CSV import preserves the raw row (`import_rows.raw_data`) indefinitely for audit
- Contact validation runs asynchronously, updating `validation_status` and `validation_score`
- Lifecycle status (`active`, `bounced`, `complained`, `unsubscribed`, `suppressed`, `deleted`) is the authoritative enrollment state
- Lists are explicit memberships; segments are query-based and evaluated at campaign launch
- Custom attributes live in `contacts.custom_attributes` (JSONB) — no schema migration required for new fields

---

## 5.3 Campaign Authoring & Launch

- Operator selects: sender profile, template version, list or segment, schedule, rate limit
- Launch is a two-phase operation: validation gate → segment snapshot → batch enqueue
- Segment snapshots are frozen at launch — subsequent contact changes do not affect in-flight campaigns
- Campaigns can be paused at any point; pause is immediate (workers check status before each send)
- Resuming a paused campaign continues from the last unsent batch
- Campaign-level rate limit (`send_rate_per_hour`) is enforced per-campaign AND per-domain
- Every campaign send is recorded in `messages` with a stable `campaign_id` reference

---

## 5.4 Suppression & Compliance

- Suppression is platform-wide. An unsubscribe from any campaign blocks all future sends to that address
- Hard bounces trigger immediate suppression with `reason='hard_bounce'`
- Soft bounces increment a counter; at threshold (3 in 30 days), suppression is applied with `reason='soft_bounce_limit'`
- Complaints trigger immediate suppression with `reason='complaint'`
- One-click unsubscribe (RFC 8058) headers are added to every outbound email
- Unsubscribe endpoint processes POST and returns 200 within 200ms; no user interaction required
- Suppression lookups happen twice: at segment evaluation (batch filter) and at send time (per-message final check)
- Suppression list is also synced to AWS SES account-level suppression as a secondary safety layer

---

## 5.5 Analytics

- Real-time campaign dashboards: sends, deliveries, bounces, complaints, opens, clicks, replies, unsubscribes
- Rolling health metrics per domain, IP pool, sender profile, and account
- Google Postmaster reputation ingested daily via API and surfaced alongside internal metrics
- Seed test results (Glockapps / MailReach) integrated into the health dashboard
- Export: all raw event data available via a read-only BI-friendly view (for Metabase, Looker, etc.)
