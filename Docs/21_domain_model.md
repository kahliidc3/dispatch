# Domain Model

## Purpose

This document explains the business domain model behind the project so frontend, backend, and database design stay aligned.

---

## 1. Domain Scope

dispatch is an internal bulk-email platform with:

- a **control plane** (contacts, campaigns, suppression, analytics, ML)
- a **delivery plane** (AWS SES as the only send provider)

Deliverability protection is a core business rule, not a technical afterthought.

---

## 2. Bounded Contexts

### 2.1 Identity & Sending Infrastructure

Defines who can send and from where.

- `Domain`
- `DomainDnsRecord`
- `SenderProfile`
- `SESConfigurationSet`
- `IPPool`

### 2.2 Audience

Defines who can receive messages.

- `Contact`
- `ContactSource`
- `Preference`
- `SubscriptionStatus`
- `SuppressionEntry`
- `List`
- `Segment`

### 2.3 Campaign Management

Defines what is sent and when.

- `Template`
- `TemplateVersion`
- `Campaign`
- `CampaignRun`
- `SegmentSnapshot`
- `SendBatch`
- `Message`

### 2.4 Event & Reputation

Defines what happened after sending.

- `DeliveryEvent`
- `BounceEvent`
- `ComplaintEvent`
- `OpenEvent`
- `ClickEvent`
- `UnsubscribeEvent`
- `ReplyEvent`
- `RollingMetrics`
- `CircuitBreakerState`

### 2.5 Platform Governance

Defines trust, security, and operations.

- `User`
- `ApiKey`
- `AuditLog`
- `AnomalyAlert`

---

## 3. Core Aggregates and Invariants

### 3.1 Contact Aggregate

Root: `Contact`  
Child/linked objects: sources, preferences, subscription status

Rules:

- Email is globally unique (case-insensitive).
- Lifecycle status controls send eligibility.
- If unsubscribed/suppressed, contact must not be sent.

### 3.2 Campaign Aggregate

Root: `Campaign`  
Child/linked objects: runs, snapshots, batches, messages

Rules:

- Launch creates an immutable audience snapshot for that run.
- In-flight sends use the frozen snapshot, not live segment changes.
- Pause/resume affects execution state without mutating historical records.

### 3.3 Suppression Aggregate

Root: `SuppressionEntry`

Rules:

- Platform-wide suppression (not campaign-specific).
- Bounce/complaint/unsubscribe can create suppression.
- Final send check must enforce suppression before delivery.

### 3.4 Domain Health Aggregate

Root: `Domain` + `CircuitBreakerState` + `RollingMetrics`

Rules:

- Sender profile depends on domain verification and reputation state.
- Circuit breaker state gates sending at domain/IP pool/profile/account scopes.
- Unknown/unsafe health states fail closed (pause sending).

---

## 4. Key Relationships (Business View)

- One `Domain` has many `SenderProfile`s.
- One `Campaign` uses one `SenderProfile` and one `TemplateVersion`.
- One `Campaign` has many `CampaignRun`s.
- One `CampaignRun` has many `SegmentSnapshot` rows and `SendBatch`es.
- One `SendBatch` has many `Message`s.
- One `Message` may emit many events over time.
- One `Contact` may belong to many lists and many segment snapshots.
- One `SuppressionEntry` can block messages across all campaigns.

---

## 5. Lifecycle Models

### 5.1 Campaign Lifecycle

`draft -> scheduled -> running -> paused -> completed | cancelled | failed`

### 5.2 Message Lifecycle

`queued -> sending -> sent -> delivered | bounced | complained | failed | skipped`

### 5.3 Contact Lifecycle

`active -> bounced | complained | unsubscribed | suppressed | deleted`

### 5.4 Domain Reputation Lifecycle

`warming -> healthy -> cooling -> burnt -> retired`

---

## 6. Domain Events (Business Events)

Important events that drive behavior across contexts:

- `CampaignLaunched`
- `SegmentSnapshotFrozen`
- `BatchEnqueued`
- `MessageSent`
- `HardBounceReceived`
- `ComplaintReceived`
- `UnsubscribeReceived`
- `SuppressionAdded`
- `CircuitBreakerTripped`
- `CircuitBreakerReset`

---

## 7. Read/Write Alignment Across Layers

- **Frontend:** route and UI modules should map to bounded contexts (`campaigns`, `contacts`, `domains`, `analytics`, `suppression`, `settings`).
- **Backend:** services/repositories should follow aggregate boundaries and enforce invariants.
- **Database:** schema tables and constraints should encode uniqueness, immutability, and state-machine safety.

---

## 8. Out of Scope (By Design)

- Multi-tenant organization boundaries
- BYOD sending domains
- Multi-ESP routing/fallback
- Transactional email product behavior

