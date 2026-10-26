# Proposal: Messaging & Notification Gateway (Telegram & WhatsApp Integration)

> [!IMPORTANT]
> **HANDOFF DIRECTIVE FOR DOWNSTREAM AGENT / IMPLEMENTER:**
> This OpenSpec change is an **initial planning and exploratory architectural stub**. It was scaffolded with intentional loose ends and breadth-first design leeway.
> **WHATEVER AGENT OR DEVELOPER PICKS UP THIS CHANGE MUST:**
> 1. **Refine, enhance, sharpen, and harden** this specification further before initiating runtime coding.
> 2. Validate concrete payload schemas, authentication handshakes, and retry bounds against the core repository's Phase A API contracts (`contracts/openapi.yaml`).
> 3. Verify commercial onboarding readiness for Meta WhatsApp Cloud API (business registration, template approvals, cost approval) before migrating beyond the Telegram validation baseline.

## Why
External B2B Maklon fashion brands and remote factory executives currently lack immediate mobile visibility into apparel manufacturing milestones (cutting completion, sewing line progress, QC inspection completion) and weekly Saturday piece-rate payroll approvals without logging into the desktop web portal. Furthermore, tailors on the shop floor in Ciwidey need an accessible mechanism to receive their weekly wage breakdowns. Integrating asynchronous messaging bots via Telegram (for zero-cost operational validation) and WhatsApp Cloud API (for high-penetration client communications) bridges this visibility gap without burdening shop-floor operators.

## What Changes
This change introduces an asynchronous, event-driven messaging gateway decoupled from the core double-entry manufacturing engine:
- A transactional outbox event ingestion pipeline recording domain state changes atomically in PostgreSQL.
- An asynchronous dispatcher worker consuming pending outbox events using authenticated service credentials (`X-Service-Principal`).
- A Telegram Bot integration transport delivering formatted Markdown alerts for order milestones, weekly Saturday payroll summaries, and operational bottleneck alerts.
- A future-ready adapter interface for Meta WhatsApp Business Cloud API with Highly Structured Message (HSM) template compatibility.
- Strict isolation preventing chat channels from performing state-altering mutations, preserving PostgreSQL RLS policies and double-entry invariants.

## Capabilities

### New Capabilities
- `messaging-notification-gateway`: Asynchronous transactional outbox event dispatcher and multi-channel messaging gateway (Telegram-first, with WhatsApp Cloud API adapter hooks) providing outbound milestone alerts, payroll slips, and system notifications.

### Modified Capabilities
*(None; this change introduces an independent satellite integration layer that consumes existing core domain events)*

## Impact
- **Core Engine & Ledger:** Completely untouched. Core FastAPI endpoints and database triggers continue executing invariants (`validate_material_dispatch()`) without synchronous dependencies on third-party messaging transports.
- **Data Models:** Adds an `outbox_events` table and an optional `channel_identities` table for actor contact mapping.
- **Dependencies:** Adds Telegram Bot API integration and optional Meta Cloud API HTTP clients in a separate worker scope.
- **Security & RBAC:** Chat channels have zero mutation authority; outbound notifications respect tenant boundaries (`tenant_id`) and prevent cross-tenant contact leakage.
