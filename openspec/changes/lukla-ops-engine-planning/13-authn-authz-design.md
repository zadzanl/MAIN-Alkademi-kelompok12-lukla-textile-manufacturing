# Phase B1 — Authentication and Authorization Design

**Status:** Planning proposal only. No identity provider, token issuer, database migration, runtime endpoint, or security certification is implemented by this document.

**Contract boundary:** This document refines authentication around the reviewed Phase A3 contract. It does **not** change operation IDs, paths, required fields, stable error codes, tenant/legal-owner/beneficiary dimensions, or idempotency scope in `artifacts/contracts/openapi.yaml`.

## 1. Sources and exact scope

- `[task]` `task-record.md`, revision 15, Phase A3 approval and Phase B authorization.
- `[plan]` `09-technical-blueprint-completion-plan.md`, §2, §3, §4, and B1 deliverable.
- `[tech]` `artifacts/tech_plan-blueprint-001.md`, especially Contract Schema Conventions, `set_request_context`, and RLS negative controls.
- `[stack]` `artifacts/10-technology-stack-and-decisions.md`, §§2–5.
- `[schema]` `artifacts/11-database-schema-spec.md`, §§2, 5–9 (`actors`, memberships, grants, credentials, sessions, RLS, and non-owner application role).
- `[api]` `artifacts/12-api-contract-plan.md`, §§1–2 and §5.
- `[contract]` `artifacts/contracts/openapi.yaml`: `login`, `refreshSession`, `logout`, `getMyContext`, all operation metadata, and reusable auth/error parameters.
- `[rbac]` `04-rbac-matrix.md`: the eight observed business roles and their source permissions/restrictions.
- `[tests]` `06-acceptance-tests.md`: AT-R01–AT-R08 and the explicit distinction between source permissions, unspecified permissions, and blocked decisions.
- `[review]` `artifacts/review/blueprint-contract-review.md`: A3 approval; any contract change reopens review.

The eight business roles are **Owner/Eksekutif**, **Tim Sample/Adis**, **Gudang/Warehouse**, **Kepala Produksi/Mandor**, **Penjahit/Tailor**, **QC Inspector**, **Finance & Payroll**, and **Klien Maklon/Ext**. Names are preserved from `[rbac]`; API role claims may use stable identifiers mapped to these display names.

## 2. Proposed protocol: bearer access plus rotating session

**PROPOSAL — unresolved provider decision:** use an OAuth2/OIDC-compatible bearer access token with a short lifetime and an opaque, rotating refresh token. The contract already exposes the shape through `POST /auth/login` (`login`), `POST /auth/refresh` (`refreshSession`), `POST /auth/logout` (`logout`), and `GET /me/context` (`getMyContext`).

### 2.1 Token and session behavior

1. Login authenticates credentials or a device flow, then returns the contract `Session`: access token, expiry, refresh token, and server-derived context. The access token is sent as `Authorization: Bearer <token>`.
2. Refresh accepts the current opaque refresh token, rotates it, stores only a hash in `sessions`, and invalidates the prior token. Reuse of an old token revokes the refresh-token family and returns `AUTH_REQUIRED`.
3. Logout is idempotent for the presented session and revokes the refresh family. It does not delete audit history.
4. Access-token signature, issuer, audience, clock tolerance, key rotation, password policy, MFA, and recovery are **DECISION NEEDED**. They must be selected without changing the HTTP contract.
5. Browser storage is **PROPOSAL**: keep the access token in memory; use a Secure, HttpOnly, SameSite refresh-token cookie for the browser portal where deployment policy permits. A native/browserless floor terminal may use an OS-protected token store. Never place refresh tokens in ordinary `localStorage`.
6. The server is authoritative for actor, memberships, grants, and scope. A tenant header, role header, client identifier, or scope query parameter is never an authorization source.

The exact issuer and provider remain portable: the backend should depend on standard JWT/OIDC validation interfaces, not provider SDK types. A self-hosted issuer, AWS-compatible managed issuer, or another OIDC provider may implement the same validated claims. Provider migration must preserve actor IDs, membership IDs, audit identity, and session-revocation semantics.

## 3. Claims to request context

### 3.1 Minimum validated identity

The verifier accepts only a signature-validated token with the expected issuer and audience. Proposed claim mapping:

| Token value | Validation | Internal result |
|---|---|---|
| `sub` | Non-empty stable provider subject; mapped to a local actor, never used directly as a tenant ID | `actors.id` via an identity mapping table or equivalent account link |
| `iss`, `aud`, `exp`, `iat`, `nbf` | Issuer/audience/time checks | Reject with `AUTH_REQUIRED` on failure |
| `jti` | Optional access-token replay/audit correlation | Request/session correlation only; not a scope grant |
| `sid` | Optional session family reference | Used to revoke or correlate a local session where supported |
| `amr`/`acr` | Optional authentication-strength evidence | May gate sensitive actions only after an approved policy decision |

`tenant_id`, role, legal-owner scope, and beneficiary scope are **not trusted merely because a caller places them in a token**. Proposed implementation validates the actor against current local `actor_memberships` and `scope_grants` inside the request transaction. If a provider emits these claims, they are hints for lookup and audit comparison, not permission grants.

### 3.2 `set_request_context` sequence

For every authenticated API request:

1. Parse the bearer token and validate signature, issuer, audience, time, and revocation/session state.
2. Resolve `sub` to an active `actors` row.
3. Begin a database transaction on a pooled connection.
4. Call `set_request_context(tenant_id, actor_id, role, legal_owner_scope, beneficiary_scope)` using server-resolved values. The function rechecks active membership and grants before setting transaction-local values.
5. Install `SET LOCAL`/`set_config(..., true)` values for actor, tenant, role, legal-owner scope, beneficiary scope, request ID, and service principal where applicable.
6. Execute the operation. Database RLS and invariant functions recheck access and ownership; API checks are not the final trust boundary.
7. Write audit/outbox/idempotency records in the same transaction when the operation mutates data, then commit or roll back before returning the pooled connection.

Missing or invalid context yields no tenant rows and rejects writes with `TENANT_CONTEXT_MISSING` or `FORBIDDEN` as appropriate. Context is never installed from an unvalidated `X-Tenant-Id` or request body field.

### 3.3 Three independent scope dimensions

- `tenant_id`: commercial/workspace access boundary.
- `legal_stock_owner_id` / legal-owner scope: title or custody of material and files.
- `order_beneficiary_id` / beneficiary scope: party entitled to order output.

The authorization layer must carry all three dimensions separately. A user may be allowed to work in a tenant while lacking legal ownership of a lot or entitlement to an order. A CMT, Semi-CMT, or Full Package flow must not acquire access by silently copying one dimension into another. `validate_material_dispatch(stock_lot_id, order_id)` remains the database authority for dispatch compatibility.

## 4. Authorization model

The proposed model is deny-by-default capability authorization over current local membership and explicit grants:

1. No authenticated actor receives a capability unless an active membership/grant matches the operation and scope.
2. An absent permission is not silently converted into a new business prohibition; it is simply not granted. The source-specific restrictions in `[rbac]` are enforced as explicit negative rules.
3. Row visibility is filtered by RLS and scope. An inaccessible identifier is normally returned as `404` to avoid cross-tenant enumeration; a recognized authorization denial uses `403`.
4. Sensitive workflow operations recheck capability and state under the same transaction that mutates data.
5. Owners cannot edit locked/posting history; Finance cannot change physical warehouse stock; QC cannot change rates/order data; external clients are restricted to their own `client_id`/beneficiary scope. See `[rbac]` and AT-R01–AT-R08 in `[tests]`.
6. A permission catalog is an implementation proposal, not a frozen API change. It must be reviewed against the eight source roles before runtime authorization is built.

### 4.1 Role-to-capability baseline

| Role | Contract-visible baseline | Explicit restriction to enforce | Scope note |
|---|---|---|---|
| Owner/Eksekutif | system configuration, analytics, rate-card operations, audit/ledger visibility as granted | cannot alter locked transaction history | explicit internal tenant/grant scope |
| Tim Sample/Adis | sample usage, time study, sample-version approval | cannot approve mass order without required confirmation | sample/order beneficiary scope |
| Gudang/Warehouse | receiving, issuing, stocktake, stock views | cannot issue when client/order IDs do not match | legal stock owner plus order beneficiary |
| Kepala Produksi/Mandor | lines, assignments, rate-card component workflow, tallies and tally verification | cannot change payroll formula or final QC result | production tenant and assigned lines |
| Penjahit/Tailor | own assigned work and unverified work reporting | cannot edit verified output | actor/operator assignment scope |
| QC Inspector | assembly inspection and defect recording | cannot alter rate or client order data | assembly/order scope |
| Finance & Payroll | PO/invoice, payroll and overhead workflows, approved financial evidence | cannot alter physical warehouse stock | finance-authorized tenant/run scope |
| Klien Maklon/Ext | own order status, progress, and own consigned stock | only own `client_id`; no cross-client records | beneficiary/client scope only |

The exact permission names, owner-versus-Mandor rate-card precedence, portal write actions, QC reopen behavior, and mass-order confirmer are **DECISION NEEDED**. Do not infer them from this table.

## 5. Service roles and internal jobs

Employee roles are never substituted for job authority. Proposed non-human service principals:

- `svc-saturday-payroll`: may invoke `runSaturdayPayrollJob` and the underlying `calculate_weekly_payroll` flow for explicitly scheduled periods; cannot log in as an employee or query arbitrary portal data.
- `svc-monthly-overhead`: may invoke `runMonthlyOverheadJob` and `calculate_overhead_allocation` for the requested period; pending rules remain blocking.
- `svc-search-indexer`: may write only authorized search projection/index data; cannot read unrestricted payroll/ledger data and cannot write operational records.
- `svc-outbox-publisher`: may claim/publish outbox events and record delivery attempts; cannot mutate source aggregates.
- `svc-file-cleaner`: may clean expired temporary uploads/orphans according to retention policy; cannot delete verified financial evidence.

These names are **PROPOSAL**. Each service receives a separate credential, narrow endpoint allowlist, explicit service scope, and an audit principal. The contract term is `serviceAuth`: a bearer `service-token` credential authenticates the job. `X-Service-Principal`, where supplied, is optional metadata validated against that credential; it is not a substitute for authentication. The scheduled path remains `EventBridge Scheduler -> Lambda -> authenticated HTTPS POST /internal/jobs/{job}` from `[stack]`, with an external scheduler pivot available.

## 6. Floor tablet lifecycle

**PROPOSAL — unresolved device policy:** floor tablets use a device enrollment and short-lived operator session instead of shared employee passwords.

1. An Owner/admin provisions a tablet record and one-time enrollment code through the account/device workflow. The code is single-use, expires, and is never a standing API credential.
2. Enrollment binds the device to a factory/site and allowed production scope. It does not grant a role by itself.
3. The operator selects or authenticates their own actor. The server resolves the actor's active role and line assignment; a shared tablet account must not make every operator an Owner or permit cross-line access.
4. The device receives a short-lived access session with a refresh family bound to device identity. Idle timeout, re-authentication, offline grace, and maximum session age are **DECISION NEEDED**.
5. On sign-out, device loss, role removal, or suspected compromise, the session family and device credential are revoked. Enrollment records remain auditable.
6. Offline tally capture is limited to the explicitly supported tally queue described in `14-frontend-architecture.md`; offline mode never creates an unbounded authorization bypass. On reconnect, the server revalidates actor, assignment, ownership, state, and idempotency before accepting each item.

Do not use a single permanent tablet token shared across a production floor. If the business chooses a different lifecycle, document the replacement while preserving operation IDs, actor attribution, and server-side authorization.

## 7. B2B portal lifecycle

**PROPOSAL:** an internal provisioner creates a client actor and membership, associates it with exactly the intended client/beneficiary scope, and issues an invitation or external IdP link. The client cannot self-select a tenant, legal owner, beneficiary, or scope by editing a request body.

- Portal sessions resolve to `MaklonClient` plus a current `client_id`/beneficiary grant.
- `getPortalOrderStatus` and portal-visible dashboard data are filtered server-side; a B client ID must not disclose A data.
- Own consigned stock is visible only where the legal-owner and beneficiary predicates permit it. Client access does not imply ownership of factory stock.
- Portal order creation/editing, mass-order confirmation, invoice visibility, and invitation approval are **DECISION NEEDED** because `[rbac]` marks them unspecified.
- Suspension, contract end, client reassignment, and compromised invitation revoke memberships/grants without deleting historical orders or audit events.

## 8. RLS hazard and required negative tests

The application pool must use a restricted, non-owner PostgreSQL role with no `BYPASSRLS`. Every tenant-scoped table uses RLS and `FORCE ROW LEVEL SECURITY`; pooled connections must rollback/reset transaction-local settings before reuse. A table owner or `BYPASSRLS` role can bypass RLS, so testing only as owner proves nothing.

Required planning-to-runtime checks:

- missing context returns no rows/rejects writes;
- tenant A cannot read or mutate tenant B data;
- legal-owner mismatch rejects material dispatch;
- beneficiary mismatch rejects order/material operations;
- client A cannot query client B through portal operations;
- reused pooled connection cannot retain tenant A context for tenant B;
- same idempotency key with a changed canonical payload returns `409 IDEMPOTENCY_CONFLICT`;
- Owner cannot update locked history; ledger UPDATE/DELETE remains rejected;
- a non-owner application role is tested against a table-owner/BYPASSRLS negative control, which must demonstrate why the owner role is not acceptable for application tests.

These are future runtime gates, not executed tests in this planning change. They extend AT-R01–AT-R08 from `[tests]` and the RLS requirements in `[schema]`.

## 9. Portability and unresolved decisions

Provider portability is maintained by isolating token verification behind an application interface (`TokenVerifier` proposal), storing local actor/membership/grant identity separately from provider subjects, and keeping authorization decisions in the API/database rather than provider-specific claims. No `auth.uid()`, vendor-only tenant header, or provider SDK type may appear in domain authorization code.

Unresolved decisions that must be recorded before implementation:

1. identity provider/issuer, key distribution and rotation;
2. password/MFA/recovery policy and authentication assurance for payroll approval;
3. browser refresh-cookie policy versus another protected client store;
4. floor-tablet enrollment, idle timeout, offline grace, and device replacement;
5. exact capability names and Owner/Mandor rate-card precedence;
6. B2B invitation, portal mutations, mass-order confirmation, and client suspension policy;
7. service-credential mechanism and scheduler/network topology;
8. retention and revocation windows for sessions, audit, and device records.

Until resolved, these are `PROPOSED` and implementation remains gated. None changes the frozen contract.

## 10. Verification commands

From `C:\Projects\hackathon-MAIN-alkademi`:

```powershell
python -c "import yaml; d=yaml.safe_load(open('openspec/changes/lukla-ops-engine-planning/artifacts/contracts/openapi.yaml')); ids=[o['operationId'] for item in d['paths'].values() for o in item.values() if isinstance(o,dict) and 'operationId' in o]; assert len(ids)==len(set(ids)); print('operationIds=PASS', len(ids))"
openspec validate lukla-ops-engine-planning
git diff --check
```

These commands check YAML/operation-ID structure and planning syntax only. They do not prove token validation, RLS enforcement, device security, portal isolation, or runtime behavior.
