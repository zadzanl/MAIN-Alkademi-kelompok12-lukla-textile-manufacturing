# Implementation Tasks: Messaging & Notification Gateway

> [!IMPORTANT]
> **HANDOFF DIRECTIVE FOR DOWNSTREAM AGENT / IMPLEMENTER:**
> This tasks document represents an **exploratory planning stub**.
> **ANY AGENT OR DEVELOPER WHO PICKS UP THIS CHANGE MUST:**
> 1. **Refine, enhance, sharpen, and harden** the task definitions and technical verification steps prior to code implementation.
> 2. Ensure Phase 1 (Specification Hardening & Contract Alignment) is completed and verified against the core OpenAPI contracts before writing runtime adapters.
> 3. Enforce the non-negotiable security boundary: messaging channels must remain outbound-only or read-only; no operational mutations or double-entry ledger state changes may occur over chat.

## 1. Specification Hardening & Contract Alignment (Mandatory First Step)

- [ ] 1.1 Downstream agent refines and sharpens `proposal.md`, `design.md`, and `spec.md` with precise domain constraints
- [ ] 1.2 Define strict JSON schemas for the candidate event payloads:
  - `production.order.milestone_reached`
  - `payroll.weekly.statement_ready`
  - `floor.operational.alert`
- [ ] 1.3 Add operation `POST /internal/jobs/dispatch-outbox` to core API contract plan (`12-api-contract-plan.md` & `contracts/openapi.yaml`) with `X-Service-Principal` security definitions
- [ ] 1.4 Validate tenant isolation guarantees to ensure cross-tenant notification delivery is structurally impossible

## 2. Database Schema & Transactional Outbox Foundation

- [ ] 2.1 Author database migration for `outbox_events` table with indexes on `(created_at) WHERE NOT dispatched`
- [ ] 2.2 Author optional `channel_identities` table mapping `app_users.id` and `clients.id` to external chat IDs / phone numbers
- [ ] 2.3 Integrate outbox emission hooks within core FastAPI domain services (Order status transitions, Saturday payroll calculation) within active PostgreSQL transactions

## 3. Dispatcher Worker & Service-Principal Auth

- [ ] 3.1 Implement core endpoint `POST /internal/jobs/dispatch-outbox` with atomic row selection (`FOR UPDATE SKIP LOCKED`)
- [ ] 3.2 Implement standalone dispatcher worker service consuming pending outbox items via authenticated service token
- [ ] 3.3 Implement exponential backoff retry mechanism and dead-letter queue (DLQ) logging for permanent delivery failures

## 4. Telegram Transport Adapter (Primary Validation Spike)

- [ ] 4.1 Implement `TelegramTransport` implementing the abstract `NotificationTransport` interface
- [ ] 4.2 Configure Telegram Bot token and connection pool via environment variables
- [ ] 4.3 Implement Markdown/HTML message template formatting for order milestones, payroll slips, and floor alerts
- [ ] 4.4 Implement global (30 msgs/sec) and per-chat (1 msg/sec) rate limiters
- [ ] 4.5 Execute automated test suite validating message formatting and delivery against a mock Telegram API

## 5. WhatsApp Business Cloud API Adapter (Commercial Phase 2 - Deferred)

- [ ] 5.1 Verify Lukla Manufacturing Meta Business Manager verification, NIB/SIUP, and registered phone number
- [ ] 5.2 Draft and submit Meta Highly Structured Message (HSM) utility templates for order milestone updates
- [ ] 5.3 Implement `WhatsAppTransport` adapter implementing `NotificationTransport`
- [ ] 5.4 Configure webhook verification and delivery status callback tracking

## 6. End-to-End Verification & Operational Hardening

- [ ] 6.1 Test failure tolerance: Verify core order processing and payroll runs succeed without rollback when Telegram API is unreachable (HTTP 500 / timeout)
- [ ] 6.2 Test idempotency: Verify simulated worker crash during dispatch does not send duplicate messages to recipients
- [ ] 6.3 Run workspace hygiene check (`python scripts/check_workspace_hygiene.py`) and ensure clean code isolation
