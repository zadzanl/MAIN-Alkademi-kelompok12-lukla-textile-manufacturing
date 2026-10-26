# messaging-notification-gateway Specification

## Purpose
TBD - created by archiving change messaging-bots-integration. Update Purpose after archive.
## Requirements
### Requirement: Asynchronous Outbound Notification Pipeline
The system SHALL provide an asynchronous, event-driven notification dispatch pipeline that consumes business events from the manufacturing and financial domains and broadcasts formatted alerts to designated external channels without blocking transactional persistence.

#### Scenario: Production milestone broadcast
- **WHEN** a production order transitions milestone state (e.g., cutting complete, assembly batch moved to QC)
- **THEN** the system SHALL queue a milestone notification payload containing order identifier, client scope, timestamp, and human-readable progress metrics for asynchronous external delivery

#### Scenario: Saturday payroll notification generation
- **WHEN** the weekly Saturday piece-rate payroll run is calculated and marked pending approval
- **THEN** the system SHALL queue an executive payroll summary notification for authorized factory leadership

---

### Requirement: Transactional Outbox Event Ingestion
The system SHALL decouple domain state transitions from external messaging network transports via a transactional outbox mechanism, ensuring event records are written atomically within the same database transaction as the underlying domain mutation.

#### Scenario: Atomic domain event registration
- **WHEN** a state mutation occurs in an operational domain (e.g., inventory movement, QC disposition, payroll calculation)
- **THEN** the system SHALL write a corresponding event record into an `outbox_events` store within the active transaction boundary
- **AND** failure of downstream messaging dispatchers SHALL NOT cause rollback of the committed domain transaction

#### Scenario: Idempotent dispatcher extraction
- **WHEN** an external worker or scheduled job polls for undispatched outbox events
- **THEN** the system SHALL return pending event payloads and mark events as processed atomically under concurrency locks to prevent duplicate outbound messages

---

### Requirement: Recipient Routing & Contact Linking
The system SHALL maintain a flexible association between system actors (user accounts, tenant client profiles) and external messaging channel identifiers (e.g., Telegram chat IDs, telephone numbers).

#### Scenario: Channel recipient resolution
- **WHEN** an outbound event is prepared for delivery
- **THEN** the notification service SHALL resolve the designated recipient's preferred channel and active destination address without leaking cross-tenant contact details
- **AND** if no valid destination is registered for an actor, the event SHALL be logged as undeliverable without raising an unhandled exception

---

### Requirement: Multi-Channel Transport Abstraction
The notification architecture SHALL decouple event formatting and dispatch logic from specific third-party messaging transports, supporting a modular adapter pattern that prioritizes Telegram for initial operational validation while retaining extension points for WhatsApp Business Cloud API.

#### Scenario: Primary Telegram transport delivery
- **WHEN** an event is dispatched to a recipient with an active Telegram binding
- **THEN** the dispatcher SHALL format the payload into Telegram-compliant Markdown/HTML and submit it to the Telegram Bot API within platform rate limits

#### Scenario: WhatsApp Cloud API adapter readiness
- **WHEN** WhatsApp delivery is enabled for an enterprise tenant
- **THEN** the dispatcher SHALL map the event to an approved Meta Highly Structured Message (HSM) template and payload format

---

### Requirement: Failure Isolation & Delivery Backoff
The messaging subsystem SHALL be isolated from the core manufacturing availability boundary, ensuring messaging network outages, provider rate-limiting, or third-party API deprecations do not degrade core shop-floor, warehouse, or accounting operations.

#### Scenario: External API outage tolerance
- **WHEN** the third-party messaging provider (Telegram or Meta) returns an HTTP 5xx error or network timeout
- **THEN** the dispatcher SHALL apply exponential backoff retry up to a configured threshold
- **AND** the core ERP/MES operations SHALL continue uninterrupted

