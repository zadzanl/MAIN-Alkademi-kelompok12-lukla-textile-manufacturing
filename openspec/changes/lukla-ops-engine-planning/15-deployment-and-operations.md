# Phase B3 — Deployment and Operations

**Change:** `lukla-ops-engine-planning`  
**Task record:** revision 15  
**Status:** planning artifact only; no application, dependency, infrastructure, cloud, runtime, or price validation was performed.

## 1. Boundary and invariants

This document operationalizes the reviewed Phase A baseline in:

- `10-technology-stack-and-decisions.md` — FastAPI, plain PostgreSQL, S3-compatible storage, portable adapters.
- `11-database-schema-spec.md` — transaction-local context, RLS, immutable ledger, idempotency, audit/outbox, jobs.
- `12-api-contract-plan.md` and `contracts/openapi.yaml` — stable `/api/v1` paths, operation IDs, schemas, errors, ownership dimensions.
- `review/blueprint-contract-review.md` — Phase A approved with runtime/tooling proof gaps.
- `09-technical-blueprint-completion-plan.md` and `tech_plan-blueprint-001.md` — AWS-first, portable, planning-only direction.

The deployment plan must not change operation IDs, paths, schemas, error codes, idempotency scope, tenant access, legal stock ownership, order beneficiary, or unresolved financial gates. AWS is the first deployment shape, not a provider lock-in.

## 2. AWS-first reference topology

```text
Browser / portal
      |
      v
HTTPS edge / browser host
      |
      v
FastAPI service: ECS Express Mode / Fargate
      |                 |                  |
      v                 v                  v
RDS PostgreSQL       S3-compatible       logs/metrics/traces
      ^                 ^
      |                 |
EventBridge Scheduler -> Lambda -> authenticated POST /api/v1/internal/jobs/{job}
```

### Components

| Concern | AWS-first choice | Portable boundary / non-decision |
|---|---|---|
| API runtime | FastAPI container on ECS Express Mode/Fargate | Any standard ASGI container host; no App Runner/new-customer availability claim. |
| Relational database | Plain PostgreSQL on RDS | `DATABASE_URL`; Neon, Supabase-as-plain-Postgres, or self-hosted PostgreSQL remain pivots. |
| Object storage | S3 | `StorageService`, object key/content hash/metadata contract; local or S3-compatible test adapter. |
| Scheduled work | EventBridge Scheduler invokes Lambda; Lambda calls the authenticated FastAPI job endpoint | External scheduler plus authenticated HTTP call. Scheduler is not modeled as a direct arbitrary HTTP target. |
| Browser hosting | Standard browser host selected per environment | CloudFront/Amplify, Vercel, or a standalone host may be selected later without Vercel-only APIs. |
| Search/vector extension | Separate adapter, disabled by default | pgvector or Qdrant behind `VectorStore`; not part of the ledger critical path. |

No NAT requirement is asserted. Subnet, egress, VPC endpoint, ingress, and firewall choices are environment decisions after the selected topology is tested. No exact AWS price, free-tier assumption, or customer-availability claim is frozen here.

## 3. Environments and promotion gates

Use separate `dev`, `test`, and `prod` accounts or isolated environments as governance permits. Each environment has separate database, bucket prefix/bucket, service credentials, log groups, and scheduler targets. Production data must not be used as a test fixture.

Promotion gates are documentary until CI exists:

1. Contract source parses and local references resolve; operation IDs remain unique.
2. Database migration and RLS checks pass using a restricted non-owner application role; owner/BYPASSRLS is not evidence of isolation.
3. API, database, system, and browser evidence passes the Phase B harness contract.
4. Unresolved financial rules remain visibly `PENDING` and production payroll approval remains blocked.
5. Backup/restore rehearsal and rollback decision are recorded for the target environment.
6. Deployment identity, secrets, audit, and alert ownership are documented.

A failed gate stops promotion. It does not justify editing the contract or treating a proposed financial default as approved.

## 4. Container and configuration contract

The future service image should be deterministic and boring: install from a committed lock/configuration chosen during implementation, run as a non-root user, expose the documented health/readiness surface, and receive configuration through environment references or a secret manager. This planning artifact does not add dependencies or prescribe versions.

Required configuration categories:

- `DATABASE_URL` for plain PostgreSQL.
- API issuer/audience/key references for the provisional bearer/session design.
- Service-principal credential reference for scheduled jobs.
- S3 bucket/region/object-prefix references through `StorageService`.
- log/trace correlation configuration.
- feature flags for fenced search and other non-core extensions.

Secrets must never be committed, baked into an image, printed in logs, included in evidence bundles, or returned in API errors. Use a managed secret store in AWS; the portable equivalent is the hosting provider’s secret mechanism or an injected runtime secret. Rotate service credentials and revoke compromised credentials without changing employee roles or database ownership.

## 5. Scheduled jobs and authenticated service boundary

The two contract operations are `runSaturdayPayrollJob` and `runMonthlyOverheadJob`. The future flow is:

1. EventBridge Scheduler invokes a dedicated Lambda target.
2. Lambda authenticates with the OpenAPI `serviceAuth` bearer `service-token` credential. An optional `X-Service-Principal` value is metadata validated against that credential, not an authentication mechanism.
3. Lambda sends an HTTPS POST to the corresponding FastAPI internal job endpoint with an `Idempotency-Key`.
4. FastAPI authenticates the service identity, checks allowed service scope, installs transaction-local context, and runs the database job transaction.
5. The job writes `job_runs`, audit, idempotency, and outbox records according to the database contract.
6. Lambda records only safe correlation/status data; sensitive payroll data remains in the API/database boundary.

The job endpoint must not accept an employee JWT as a substitute for service authority. A retry must be safe under the operation’s idempotency contract. `getJob` is the readback operation for authorized status inspection.

Portable fallback: use another external scheduler to make the same authenticated HTTP call. Do not add in-process cron or claim that EventBridge Scheduler directly targets arbitrary HTTP.

## 6. Secrets, access, and data protection

Tenant-scoped tables use both `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`; the per-table policy matrix and non-owner negative-control requirement are defined in `artifacts/11-database-schema-spec.md` §6 and §9.

- Separate deploy, runtime, database migration, scheduler, and read-only observability identities.
- Runtime API roles cannot alter deployment configuration or read unrelated secrets.
- Database application connections use the restricted non-owner role described in artifact 11; migrations use a separately controlled migration identity and are auditable.
- RLS context is set inside each transaction with `SET LOCAL`; pooled connections are rolled back/reset before reuse.
- S3 objects use opaque keys and recorded content hashes. Download capability is short-lived and authorized against source ACL, tenant, and legal-owner scope.
- Logs redact bearer tokens, service credentials, refresh tokens, passwords, raw payroll evidence, and document contents.
- Audit records retain actor/service principal, request ID, operation ID, entity, outcome, and safe metadata; failed business transactions are logged after rollback through a separate sanitized path.

Threats to test before production include credential replay, cross-tenant reads, cross-legal-owner file access, leaked pooled context, duplicate job delivery, forged service headers, and direct database use by a table owner/BYPASSRLS role.

## 7. Backups, recovery, and data lifecycle

Posted ledger history is append-only. The `reverseLedgerTransaction` operation creates a compensating transaction; rollback never deletes or mutates posted ledger rows.

RDS backup retention, point-in-time recovery, snapshots, S3 versioning/retention, and cross-environment restore policy must be selected per environment and recorded before production approval. This document does not claim that backups are enabled or that restore has succeeded.

Required future evidence:

- backup policy and owner;
- encrypted snapshot/object configuration;
- restore into an isolated environment;
- row counts/checksums for operational data and immutable ledger continuity;
- application smoke checks after restore;
- recovery time and recovery point observations;
- cleanup/retention handling for temporary uploads, logs, traces, and evidence.

Financial evidence and ledger history are append-only at the application boundary. Rollback of a data mutation uses a compensating transaction or forward fix; it does not delete posted ledger history. A deployment rollback must not silently roll back committed business data.

## 8. Observability and alerts

Every request and job carries a correlation identifier. Emit structured events with timestamp, environment, service, operation ID, request ID, status, latency class, actor/service principal class, and safe error code. Do not emit secrets or unrestricted business payloads.

Minimum signals:

- API availability/readiness and error rate.
- latency by operation ID, with attention to writes and job endpoints.
- database connection saturation, transaction rollback rate, lock contention, and migration state.
- RLS/context failures, idempotency conflicts, ledger invariant failures, material dispatch mismatches, and `FINANCIAL_RULE_PENDING` blocks.
- job run state, duration, retry count, dead-letter/manual-recovery state.
- outbox lag and failed publication attempts.
- object upload completion/orphan cleanup failures.
- backup failure and restore rehearsal status.

Alerts require an owner, severity, notification route, runbook link, and a safe correlation ID. Metrics and logs are operational evidence, not proof that business acceptance passed.

## 9. Rollout, rollback, and incident handling

Use an immutable image identifier and a deployment record containing commit, contract hash, migration level, configuration version, operator, and time. Roll out first to a non-production environment, then a controlled production slice if the hosting mechanism supports it.

Rollback rules:

- Application-only failure: return to the last known image after checking contract/migration compatibility.
- Expand migration: deploy backward-compatible schema changes first; switch traffic only after checks pass.
- Contract/data incompatibility: stop rollout and forward-fix or restore an isolated copy; never delete financial history to make an old image work.
- Job failure: inspect `job_runs`, idempotency, audit, and outbox state; retry the job operation, not an unbounded duplicate mutation.
- Security incident: revoke/rotate affected credentials, isolate access, preserve sanitized evidence, and review scope grants.

A rollback is not complete until health checks, one authenticated read, one safe write/control, job state, and audit continuity are verified. These are future runtime gates and have not run.

## 10. Budget and portability fallback

Cost control is a design responsibility, not an exact price claim. Start with the smallest supported environment shape, schedule non-production resources only when allowed, cap log retention, set storage lifecycle rules, and alert on budget thresholds. Exact thresholds and prices belong in an environment decision record after current provider validation.

If AWS deployment is unavailable or unsuitable, preserve the same interfaces:

- ASGI container host instead of ECS;
- plain PostgreSQL provider instead of RDS;
- S3-compatible storage instead of S3;
- external scheduler plus Lambda-equivalent worker or scheduled HTTP caller;
- standard browser host instead of the AWS edge choice.

The fallback must still preserve authentication, service scope, idempotency, transaction-local RLS context, audit/outbox behavior, and the same OpenAPI contract. It must not weaken isolation to reduce cost.

## 11. Explicit non-claims and exit criteria

This artifact does **not** claim application implementation, dependency installation, Docker build success, Terraform, cloud deployment, AWS account access, network validation, backup success, restore success, observability readiness, exact pricing, or production readiness. It also does not claim that App Runner is available to new customers, that NAT is required, or that Scheduler directly invokes arbitrary HTTP.

Phase B3 is complete when a later implementation can produce, without changing the contract:

- an environment-specific topology decision;
- a secret/access inventory;
- a migration and rollback runbook;
- backup/restore evidence;
- monitoring/alert ownership;
- scheduled job delivery and retry evidence;
- budget threshold and portable fallback decision.

All unresolved financial gates remain unresolved: meal basis, QC bonus recipient/configuration, integer remainder destination, payroll eligibility, overhead denominator, cutoff/period policy, and any related approval evidence. A deployment cannot authorize those rules.
