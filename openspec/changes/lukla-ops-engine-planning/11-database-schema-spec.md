# Phase A2 — Database Schema and Invariant Specification

**Task record:** revision 12.  **Status:** logical schema contract; no migration has been executed.

## 1. SQL conventions

PostgreSQL is the reference dialect. Every table uses `uuid` primary keys unless stated otherwise, `timestamptz` for instants, `date` for business dates, `numeric(p,s)` for quantities, and integer minor units for money. Text enums are `CHECK`-constrained so a later service can map them to Python enums without vendor types. `created_at` and `updated_at` are UTC; business cutoffs carry an IANA timezone in configuration. A migration must add tables in dependency order and must be reversible except for immutable-ledger protection, which is forward-only.

**Normative shorthand:** every column is NOT NULL unless explicitly marked NULL. `timestamps` expands to `created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()`; `actor/timestamp` expands to `created_by uuid REFERENCES actors(id), created_at timestamptz DEFAULT now()`. Every tenant-scoped table, including children where omitted below, has `tenant_id uuid REFERENCES tenants(id)` and unique `(tenant_id,id)`. Every parent reference is a composite FK `(tenant_id,parent_id)` to that parent's `(tenant_id,id)`, with `ON DELETE RESTRICT`; no cross-tenant child is possible. Actor references point to global `actors(id)` and require a live membership on write. Every FK has a leading-column B-tree index. `legal_stock_owner_id` and beneficiary IDs reference `tenants(id)` but are NOT treated as an access grant. Nullable interval ends mean infinity; starts are mandatory; starts precede ends. All enumeration/status strings are CHECK-constrained to the API enums or states specified here. These are migration requirements, not executed SQL.

`tenant_id` on operational records is the beneficiary client workspace (or internal brand workspace). Factory-owned lots allocated to that workspace keep factory legal ownership. Unallocated shared stock is outside the initial intake contract; no silent reassignment. Payroll consolidates authorized client workspaces in one factory-scoped run; credits retain their origin scope and external clients cannot query payroll. Internal-role scope grants are explicit. Cross-client payroll references use `(source_tenant_id, wage_credit_id)` composite FKs rather than pretending all source credits share the factory tenant.

## 2. Identity, access, and commercial model

| Table | Columns (type; nullability) | Keys/constraints/indexes |
|---|---|---|
| `tenants` | `id uuid NOT NULL`, `tenant_code text NOT NULL`, `name text NOT NULL`, `kind text NOT NULL`, `active boolean NOT NULL`, timestamps | PK; unique `(tenant_code)`; kind `CLIENT|INTERNAL_BRAND|FACTORY`; index active |
| `actors` | `id uuid NOT NULL`, `email text NOT NULL`, `display_name text NOT NULL`, `active boolean NOT NULL`, timestamps | PK; unique index lower(email); identity-only table, not portal readable |
| `actor_memberships` | `id uuid`, `tenant_id uuid`, `actor_id uuid`, `role text`, `status text`, `valid_from/valid_to timestamptz` nullable | PK; unique `(tenant_id,actor_id,role)`; indexes actor and tenant; role is one of the eight canonical roles |
| `scope_grants` | `id uuid`, `actor_id uuid`, `tenant_id uuid`, `legal_stock_owner_id uuid`, `order_beneficiary_id uuid`, `capability text`, `expires_at timestamptz NULL` | PK; index actor/capability; all referenced IDs must exist; explicit grant required for cross-client administration |
| `clients` | `id uuid`, `tenant_id uuid`, `legal_name text`, `external_code text`, `active boolean`, timestamps | PK; unique `(tenant_id,external_code)`; client tenant must be `CLIENT` |
| `orders` | `id uuid`, `tenant_id uuid`, `order_number text`, `beneficiary_tenant_id uuid`, `scheme text`, `status text`, `timezone text`, `cutoff_local time`, timestamps | PK; unique `(tenant_id,order_number)`; scheme `CMT|SEMI_CMT|FULL_PACKAGE`; beneficiary is explicit and indexed |
| `order_components` | `id uuid`, `order_id uuid`, `article_code text`, `component_code text`, `planned_units numeric(18,3)`, `unit text`, `status text` | PK; unique `(order_id,article_code,component_code)`; quantity > 0 |

`tenant_id` governs commercial access. `beneficiary_tenant_id` governs who receives an order's output. `legal_stock_owner_id` below governs title/custody. A Semi-CMT order may have a Lukla-owned trim lot and an external-client-owned shell lot simultaneously; receiving or issuing a Lukla-owned trim does not transfer title to the external beneficiary.

## 3. Sample, production, and stock entities

| Table | Columns (type; nullability) | Keys/constraints/indexes |
|---|---|---|
| `samples` | `id uuid`, `tenant_id uuid`, `order_id uuid NULL`, `article_code text`, `status text`, `approved_revision_id uuid NULL`, timestamps | PK; tenant/order indexes; status `DRAFT|SUBMITTED|APPROVED|LOCKED` |
| `sample_revisions` | `id uuid`, `sample_id uuid`, `revision_no integer`, `spec_json jsonb`, `created_by uuid`, `approved_at timestamptz NULL`, `locked_at timestamptz NULL` | PK; unique `(sample_id,revision_no)`; locked rows immutable |
| `sample_bom_items` | `id uuid`, `tenant_id uuid`, `sample_revision_id uuid`, `sku text`, `material_description text`, `quantity numeric(18,3)`, `unit text`, `category text`, `supplier_ref text NULL`, `sort_order integer`, `created_by uuid`, timestamps | PK; unique `(sample_revision_id, sku)`; quantity > 0; unit `METER\|PIECE\|KILOGRAM\|ROLL`; category `MAIN_FABRIC\|LINING\|INTERLINING\|TRIM\|ACCESSORY\|THREAD\|OTHER`; sort_order >= 0; FK sample_revision_id; locked revision rejects insert/update/delete via trigger |
| `sample_revision_notes` | `id uuid`, `tenant_id uuid`, `sample_revision_id uuid`, `note_type text`, `body text`, `created_by uuid`, `created_at timestamptz` | PK; append-only (no UPDATE/DELETE); note_type `FITTING_NOTE\|CHANGE_REASON\|CLIENT_FEEDBACK\|INTERNAL_MEMO`; index revision; body NOT NULL, max 5000 chars enforced at app layer |
| `sample_revision_attachments` | `id uuid`, `tenant_id uuid`, `sample_revision_id uuid`, `file_object_id uuid`, `attachment_type text`, `label text NULL`, `created_by uuid`, `created_at timestamptz` | PK; FK file_object_id REFERENCES file_objects(id); attachment_type `TECH_PACK\|SKETCH\|PHOTO\|MEASUREMENT_SHEET\|OTHER`; unique `(sample_revision_id, file_object_id)`; append-only; label max 200 chars |
| `time_study_sessions` | `id uuid`, `tenant_id uuid`, `sample_revision_id uuid`, `component_code text`, `operator_ref text NULL`, `method text`, `status text`, `finalized_smv_ms bigint NULL`, `finalized_by uuid NULL`, `finalized_at timestamptz NULL`, `created_by uuid`, timestamps | PK; status `OPEN\|FINALIZED\|ABANDONED`; finalized_smv_ms NOT NULL when status=FINALIZED; index revision/component; one OPEN session per (tenant_id, sample_revision_id, component_code) at a time enforced by partial unique index |
| `time_study_observations` | `id uuid`, `tenant_id uuid`, `session_id uuid`, `observed_duration_ms bigint`, `rating_factor integer`, `exclude_flag boolean`, `exclude_reason text NULL`, `sequence_no integer`, `captured_at timestamptz`, `created_by uuid` | PK; FK session_id; observed_duration_ms > 0; rating_factor between 50 and 150 (percent of standard pace, default 100); sequence_no unique per session; exclude_flag false by default; append-only |
| `time_studies` | `id uuid`, `tenant_id uuid`, `sample_revision_id uuid`, `component_code text`, `duration_ms bigint`, `observed_units numeric(18,3)`, `method text`, `captured_by uuid`, `session_id uuid NULL`, timestamps | PK; duration > 0, units > 0; index revision/component; session_id FK time_study_sessions(id) — populated when derived from a finalized session, null for direct-entry legacy records |
| `rate_cards` | `id uuid`, `tenant_id uuid`, `order_beneficiary_id uuid`, `article_code text`, `component_code text`, `amount_minor bigint`, `currency char(3)`, `rule_version text`, `effective_from/through timestamptz NULL`, `locked_at timestamptz NULL` | PK; amount >= 0; no overlapping active interval for same scope; index lookup tuple |
| `material_lots` | `id uuid`, `tenant_id uuid`, `legal_stock_owner_id uuid`, `order_beneficiary_id uuid`, `order_id uuid`, `sku text`, `quantity numeric(18,3)`, `unit text`, `scheme text`, `status text`, timestamps | PK; quantity >= 0; indexes owner/order/beneficiary; no null owner or beneficiary |
| `stock_movements` | `id uuid`, `tenant_id uuid`, `material_lot_id uuid`, `movement_type text`, `quantity numeric(18,3)`, `source_order_id uuid NULL`, `destination_order_id uuid NULL`, `correction_of uuid NULL`, `idempotency_key text`, actor/timestamp | PK; unique `(tenant_id,idempotency_key)`; quantity > 0; correction only via compensating movement |
| `cut_batches` | `id uuid`, `tenant_id uuid`, `order_id uuid`, `material_lot_id uuid`, `issue_id uuid`, `component_code text`, `produced_pieces integer`, `consumed_qty numeric(18,3)`, `returned_qty numeric(18,3)`, `waste_qty numeric(18,3)`, `material_unit text`, timestamps | PK; issue FK; unique issue (one final result); quantities >= 0; consumed + returned + waste = issued quantity in the lot's SAME unit; pieces are separate, never added to material lengths |
| `sewing_lines` | `id uuid`, `tenant_id uuid`, `line_code text`, `active boolean`, timestamps | PK; unique `(tenant_id,line_code)` |
| `operator_assignments` | `id uuid`, `tenant_id uuid`, `line_id uuid`, `operator_id uuid`, `component_code text`, `valid_from/through timestamptz`, `active boolean` | PK; no overlapping active operator assignment per interval; indexes line/operator |
| `sewing_tallies` | `id uuid`, `tenant_id uuid`, `order_id uuid`, `cut_batch_id uuid`, `component_code text`, `operator_id uuid`, `line_id uuid`, `interval_start/through timestamptz`, `quantity integer`, `verified_by uuid NULL`, `verified_at timestamptz NULL`, `idempotency_key text`, `status text` | PK; unique `(tenant_id,operator_id,order_id,component_code,interval_start)`; quantity >= 0; duration exactly 30 minutes, aligned Asia/Jakarta half-hours; status RECORDED or VERIFIED |
| `garment_units` | `id uuid`, `tenant_id uuid`, `order_id uuid`, `component_code text`, `source_tally_id uuid`, `operator_id uuid`, `status text`, `piece_rate_snapshot_id uuid`, `wage_credited_at timestamptz NULL`, timestamps | PK; source tally FK; status `MENUNGGU_QC|QC_PASS|REWORK|REJECT_SCRAP|ASSEMBLED`; one unit cannot have two credits |
| `garment_assemblies` | `id uuid`, `tenant_id uuid`, `order_id uuid`, `serial_code text`, `status text`, `created_at timestamptz` | PK; unique `(tenant_id,serial_code)`; order FK; status `ASSEMBLING|MENUNGGU_QC|QC_PASS|REWORK|REJECT_SCRAP` |
| `assembly_components` | `id uuid`, `tenant_id uuid`, `assembly_id uuid`, `garment_unit_id uuid`, `component_code text`, `allocated_at timestamptz` | PK; UNIQUE garment_unit_id: each component piece belongs to exactly one assembly; component/assembly order and locked BOM demand must match |
| `qc_inspections` | `id uuid`, `tenant_id uuid`, `assembly_id uuid`, `inspector_id uuid`, `disposition text`, `sequence_no integer`, `idempotency_key text`, timestamps | PK; unique `(assembly_id,sequence_no)`; disposition PASS/REPAIR/REJECT; append-only, transitions serialized on assembly; no final PASS or REJECT override in initial release |
| `qc_defects` | `id uuid`, `tenant_id uuid`, `inspection_id uuid`, `garment_unit_id uuid`, `defect_code text`, `notes text NULL` | PK; FKs inspection/component; component must belong to inspection's assembly; repair operator derived from immutable component source, not supplied by caller |

## 4. Ledger, payroll, procurement, and files

| Table | Columns (type; nullability) | Keys/constraints/indexes |
|---|---|---|
| `ledger_accounts` | `id uuid`, `tenant_id uuid`, `code text`, `name text`, `account_class text`, `currency char(3)`, `active boolean` | PK; unique `(tenant_id,code)` |
| `ledger_transactions` | `id uuid`, `tenant_id uuid`, `transaction_type text`, `source_type text`, `source_id uuid NULL`, `posted_at timestamptz`, `posted_by uuid`, `reversal_of uuid NULL`, `idempotency_key text`, `canonical_payload_hash bytea` | PK; unique `(tenant_id,idempotency_key)`; unique source for non-correction events; **no UPDATE/DELETE** |
| `ledger_entries` | `id uuid`, `transaction_id uuid`, `account_id uuid`, `direction text`, `amount_minor bigint`, `currency char(3)`, `tenant_id uuid`, `memo text NULL` | PK; direction `DEBIT|CREDIT`; amount > 0; index transaction/account; **no UPDATE/DELETE** |
| `piece_rate_snapshots` | `id uuid`, `rate_card_id uuid`, `amount_minor bigint`, `currency char(3)`, `rule_version text`, `captured_at timestamptz`, `source_unit_id uuid NULL` | PK; immutable; unit references exactly one snapshot |
| `payroll_periods` | `id uuid`, `tenant_id uuid`, `period_start/end date`, `timezone text`, `cutoff_local time`, `rule_version text`, `status text`, `approved_by uuid NULL`, timestamps | PK; unique `(tenant_id,period_start,period_end)`; status `OPEN|CALCULATED|PENDING_RULE|APPROVED|PAID|REVERSED` |
| `wage_credits` | `id uuid`, `tenant_id uuid`, `garment_unit_id uuid`, `operator_id uuid`, `amount_minor bigint`, `currency char(3)`, `period_id uuid`, `reversal_of uuid NULL`, timestamps | PK; unique `(garment_unit_id)` for original credit; correction pair allowed; amount >= 0 |
| `qc_bonus_accruals` | `id uuid`, `tenant_id uuid`, `assembly_id uuid`, `amount_minor bigint`, `currency char(3)`, `rule_version text`, timestamps | PK; unique `(assembly_id)`; only first PASS can accrue, independent of number of component contributors |
| `payroll_adjustments` | `id uuid`, `tenant_id uuid`, `period_id uuid`, `operator_id uuid`, `kind text`, `amount_minor bigint`, `reason text`, `authorized_by uuid`, `correction_of uuid NULL`, timestamps | PK; no negative deduction without explicit authorization and reason; append-only |
| `financial_rule_versions` | `id uuid`, `tenant_id uuid`, `rule_name text`, `effective_from/through date`, `parameters jsonb`, `status text`, `approved_by uuid NULL` | PK; unique non-overlapping rule interval; unresolved rules are `PENDING` |
| `overhead_events` | `id uuid`, `tenant_id uuid`, `period_id uuid`, `kind text`, `amount_minor bigint`, `currency char(3)`, `source_ref text`, `authorized_by uuid`, timestamps | PK; amount >= 0; append-only |
| `purchase_orders` | `id uuid`, `tenant_id uuid`, `supplier_name text`, `order_id uuid NULL`, `status text`, timestamps | PK; status `DRAFT|APPROVED|RECEIVED|CANCELLED` |
| `purchase_order_lines` | `id uuid`, `purchase_order_id uuid`, `sku text`, `quantity numeric(18,3)`, `unit_price_minor bigint`, `currency char(3)` | PK; quantity > 0; price >= 0 |
| `supplier_invoices` | `id uuid`, `tenant_id uuid`, `purchase_order_id uuid`, `invoice_number text`, `total_minor bigint`, `currency char(3)`, `status text`, timestamps | PK; unique `(tenant_id,invoice_number)`; no automatic payment |
| `file_objects` | `id uuid`, `tenant_id uuid`, `legal_owner_id uuid NULL`, `object_key text`, `content_sha256 bytea`, `size_bytes bigint`, `content_type text`, `classification text`, `created_by uuid`, timestamps | PK; unique `(tenant_id,object_key)`; legal owner scope enforced; financial evidence is append-only metadata |
| `audit_events` | `id uuid`, `tenant_id uuid`, `actor_id uuid NULL`, `service_principal text NULL`, `action text`, `entity_type text`, `entity_id uuid NULL`, `request_id uuid`, `payload jsonb`, `occurred_at timestamptz` | PK; indexes tenant/entity/request; append-only |
| `idempotency_records` | `id uuid`, `tenant_id uuid`, `key text`, `operation_id text`, `canonical_payload_hash bytea`, `status text`, `response_status smallint`, `response_body jsonb`, `created_at`, `completed_at NULL` | PK; unique `(tenant_id,key,operation_id)`; never global-only; lease/retry state is explicit |
| `outbox_events` | `id uuid`, `tenant_id uuid`, `aggregate_type text`, `aggregate_id uuid`, `event_type text`, `payload jsonb`, `occurred_at timestamptz`, `published_at NULL`, `attempts integer` | PK; unique aggregate/event/idempotency key where applicable; written in same transaction as source mutation |

## 5. Required database functions and triggers

```sql
set_request_context(p_tenant_id uuid, p_actor_id uuid, p_role text,
                    p_legal_owner_scope uuid[], p_beneficiary_scope uuid[])
validate_material_dispatch(p_stock_lot_id uuid, p_order_id uuid)
append_ledger_transaction(p_transaction_id uuid, p_entries jsonb)
record_sewing_tally(p_order_id uuid, p_component_code text, p_operator_id uuid,
                    p_interval_start timestamptz, p_interval_end timestamptz,
                    p_quantity numeric, p_idempotency_key text)
classify_qc_unit(p_unit_id uuid, p_disposition text, p_defect_code text,
                 p_idempotency_key text)
calculate_weekly_payroll(p_period_id uuid, p_rule_version text)
calculate_overhead_allocation(p_period_id uuid, p_rule_version text)
```

`set_request_context` verifies the actor and grants before setting transaction-local GUCs. RLS policies read only validated settings. `validate_material_dispatch` locks the lot and order, checks available quantity, `legal_stock_owner_id`, `order_beneficiary_id`, and scheme rules, then permits movement; mismatch aborts before decrement. CMT client material, Lukla-owned Semi-CMT trims, and Full Package material remain distinct legal-owner cases.

`append_ledger_transaction` canonicalizes entries, requires at least one debit and credit, equal total minor units per currency, positive amounts, one tenant, and a source/idempotency record. Runtime role has no direct DML on ledger tables, only EXECUTE on a narrowly granted posting function (fixed search_path; no dynamic SQL). A deferred constraint trigger checks every inserted header at COMMIT, including empty headers. Record `created_xid xid8 DEFAULT pg_current_xact_id()` on the header; line INSERT trigger requires the same current transaction ID, so balanced lines cannot be appended in a later transaction. Header/line UPDATE/DELETE triggers raise LEDGER_IMMUTABLE for all operational roles. Function owner is a dedicated no-login, non-superuser role, with explicit scoped policies under FORCE RLS. Migration/DBA tampering is outside ordinary-user protection and must be separately audited. Reversal inserts exactly mirrored lines once (partial unique reversal_of); never edits original rows.

`record_sewing_tally` locks cut_batch and operator interval, prevents total claimed pieces exceeding cut_batch.produced_pieces, snapshots the applicable locked rate and creates RECORDED tally. `verify_tally(p_tally_id uuid)` is mandor-only and creates one garment_units component row per piece exactly once. Units awaiting assembly cannot be inspected independently. `classify_qc_unit(p_assembly_id uuid, p_disposition text, p_defects jsonb, p_idempotency_key text)` locks the finished assembly. MENUNGGU_QC -> PASS/REPAIR/REJECT; REWORK -> PASS/REPAIR/REJECT; PASS/REJECT terminal. First PASS creates one wage credit per allocated component piece/contributor and ONE bonus per assembly atomically, only under an approved effective rule. A pending rule records quality disposition plus an unvalued eligibility event; later valuation uses that event's effective rate/rule, never a silently chosen current rule. No automatic reject deduction. Corrections after final QC require a separately authorized future policy, not reinspection through this endpoint.

`create_assembly(p_order_id uuid, p_serial text, p_component_ids uuid[])` locks all source units in sorted UUID order, checks VERIFIED tallies, same tenant/order, distinct unallocated pieces, and exact locked BOM counts per component. Inserts assembly + allocations atomically in MENUNGGU_QC. Uniqueness prevents parallel reuse. REPAIR routes defect-linked component pieces to their existing operator; rework does not consume new pieces or create new wage eligibility. Entire assembly remains the QC target.

Canonical idempotency payload bytes are a sorted-key JSON encoding with normalized decimal strings, UTC timestamps, and explicit owner/beneficiary IDs; hash with SHA-256. Reserve `(tenant_id,operation_id,key)` under a unique constraint in the same business transaction, authenticate/recheck authorization even on replay, then compare hashes. Same hash returns the stored response/status; different hash fails `IDEMPOTENCY_CONFLICT`. A concurrent in-flight duplicate waits for commit or returns a retryable conflict without running the mutation twice. A crash before commit rolls back both reservation and mutation; a retry may then execute. A committed response remains replayable for the retention period (policy pending).

Payroll refuses approval when any required rule is PENDING or QC/payment inputs are not final. Zero-output payroll is a valid zero preview, not a division error; monthly overhead returns NO_OUTPUT and does not allocate until a policy is approved. Meal basis, bonus remainder, recipient configuration, cutoff, and overhead basis remain production-blocking until authorized. Approval freezes contributing credit IDs, rules and amounts. Payment recording references the approved run and external payment evidence; it does not initiate a bank transfer. One credit can belong to only one approved run. Late credits go to a later open period, never mutate a paid run.

## 6. RLS and pooled connections

Every table with `tenant_id` has `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY`. Policies use `current_setting('app.tenant_id', true)` and validate actor scope; owner and `BYPASSRLS` roles are never used by the application pool. Legal-owner and beneficiary policies add `legal_stock_owner_id`/`order_beneficiary_id` predicates where present. Administrative cross-client access requires a recorded grant and a bounded explicit scope.

Each request checks out a connection, begins a transaction, calls `set_request_context`, performs work, writes audit/outbox records, and commits or rolls back. `SET LOCAL` values disappear at transaction end. A reset/rollback is mandatory before pool return; tests deliberately reuse a connection to detect leakage. RLS tests run as a non-owner role and include a table-owner/BYPASSRLS negative-control assertion.

## 7. Transaction and outbox boundaries

The primary mutation, ledger entries, stock/wage/QC rows, idempotency completion, audit event, and outbox row are one transaction. Publishing outbox messages is separate and retryable; consumers are idempotent. Files are uploaded through a temporary object key and promoted only after the database transaction records the content hash; an orphan cleanup job is allowed. Search indexing is asynchronous and cannot block or mutate financial commits.

## 8. Required supporting tables and mappings

These complete the logical schema. Apply §1 tenant/FK/index/nullability conventions. JSON is permitted only with the named OpenAPI schema validated before storage; it is not an unspecified extension point.

| Table | Columns beyond id/tenant_id | Constraints / API binding |
|---|---|---|
| `credentials` | actor_id uuid, password_hash text, changed_at timestamptz | global identity table; unique actor; private auth role only, Argon2id hash, never API-readable |
| `sessions` | actor_id uuid, refresh_hash bytea, family_id uuid, expires_at timestamptz, revoked_at timestamptz NULL, device_label text | global auth-only; unique hash; rotating replay revokes family; never store raw tokens |
| `operators` | actor_id uuid NULL, display_name text, active boolean, employee_code text | factory directory, unique employee_code; authenticated tailor may view only linked self |
| `sample_approvals` | sample_revision_id uuid, evidence_file_id uuid, approved_by uuid, approved_at timestamptz | append-only; sample version approval not mass-order confirmation |
| `order_confirmations` | order_id uuid, sample_revision_id uuid, evidence_file_id uuid, approved_by uuid, approved_at timestamptz | unique order; role policy pending; order stores immutable snapshot of SampleSpec and rate IDs |
| `stocktakes` | material_lot_id uuid, observed_qty numeric(18,3), observed_at timestamptz, created_by uuid | observation only; not a stock mutation |
| `stock_adjustments` | stocktake_id uuid, direction text, quantity numeric(18,3), reason text, decision_id uuid | INCREASE/DECREASE; approved discrepancy policy required; Finance never writes stock |
| `eligibility_events` | assembly_id uuid, passed_at timestamptz, rule_version_id uuid NULL | unique assembly; immutable; valuation job resolves only approved effective rule |
| `payroll_runs` | period_start date, period_end date, timezone text, cutoff_local time, rule_version_id uuid, status text, input_hash bytea, version integer | factory tenant; dates inclusive start/exclusive end; unique period/version; OPEN/CALCULATED/PENDING_RULE/APPROVED/PAID |
| `payroll_run_credits` | run_id uuid, source_tenant_id uuid, wage_credit_id uuid | immutable after approval; unique source_tenant_id/wage_credit_id for committed runs; across-client FK explicit |
| `payroll_items` | run_id uuid, recipient_id uuid, base_minor bigint, meal_minor bigint, bonus_minor bigint, currency char(3) | integer >=0; unique run/recipient; total and reserve reconcile to source pool |
| `payroll_payments` | run_id uuid, external_reference text, evidence_file_id uuid, recorded_by uuid, recorded_at timestamptz | unique run; all amounts from approved run, never caller-controlled |
| `overhead_periods` | starts_on date, ends_on date, total_minor bigint, produced_units integer, status text | factory tenant, unique range; monetary rows refer here (not payroll periods); snapshot first-PASS finished units in period |
| `client_invoices` | order_id uuid, invoice_number text, status text, currency char(3), total_minor bigint, issued_at timestamptz NULL | unique tenant/invoice_number; DRAFT/ISSUED; issued immutable; commercial/tax policy gated |
| `client_invoice_lines` | invoice_id uuid, description text, quantity integer, unit_price_minor bigint | qty>0 price>=0; invoice total=sum lines; no automatic taxes |
| `file_uploads` | created_by uuid, expected_sha256 bytea, size_bytes bigint, mime_type text, key text, expires_at timestamptz, status text | PENDING/VERIFIED/REJECTED; only verified objects downloadable; file_objects stores upload_id FK |
| `job_runs` | kind text, period_id uuid, scheduled_for timestamptz, status text, error_code text NULL | unique kind/period; RUNNING/SUCCEEDED/BLOCKED/FAILED; read via getJob |
| `search_documents` | file_id uuid NULL, source_type text, source_id uuid, source_version text, classification text, acl_version integer, indexed_at timestamptz NULL | authorized projection, not copy of unrestricted payroll/audit; tombstones propagated |
| `search_chunks` | document_id uuid, ordinal integer, text text, model_id text, dimension integer, vector optional adapter column | unique doc/ordinal/version; extension migration only if search enabled |

`orders` additionally stores `sample_revision_id uuid NULL`, `spec_snapshot jsonb NULL` (SampleSpec), `confirmed_at timestamptz NULL`. `order_components.planned_units` is integer; locked BOM `pieces_per_garment integer >0`. `sample_revisions.spec_json` conforms to SampleSpec. `financial_rule_versions.parameters` conforms to FinancialRuleRequest, no arbitrary keys. `rate_cards.effective_from` is mandatory; overlap prevented under advisory lock keyed on scope/component plus database exclusion constraint (btree_gist, preflight availability) or serializable validated function if unavailable. `wage_credits.period_id` is nullable until assigned to run; original unique constraint is partial WHERE reversal_of IS NULL. Add `ledger_transaction_id uuid NULL` linking monetary events to ledger. `idempotency_records.created_at/completed_at` and `outbox_events.published_at` are timestamptz; only completion/publication fields are nullable. Identity and runtime idempotency table writes occur through narrow routines. No source document is mutated by these engineering proposals.

## 9. RLS / privilege matrix and migration order

| Tables | Read rule | Write rule |
|---|---|---|
| tenants, clients | own membership or explicitly granted internal scope | Owner provisioning capability; proposed permission requires approval |
| actors, credentials, sessions | auth routines only; /me returns safe projection | auth routines only; no generic domain SQL access |
| memberships, scope_grants | current actor safe projection | Owner explicit provisioning grant, no self-elevation |
| orders, components, samples, revisions, approvals, rates, time_studies | allowed client scope and operation capability | operation roles; locked records immutable; confirmation gated |
| lots, movements, stocktakes, adjustments, cut_batches | tenant + beneficiary; external portal only own consigned lot projection | Warehouse capabilities, same owner/beneficiary eligibility; adjustment decision gate |
| lines, assignments, operators, tallies, units, assemblies, allocations | internal scoped role; tailor own assignments/tallies | ProductionHead; Tailor create own unverified tally only; QC cannot modify source outputs |
| inspections, defects, eligibility, bonus accruals | scoped QC/Production/Finance; no portal operator/pay details | QC routine for inspection; derived credits only via valuation routine |
| ledger, credits, runs, items, payments, rules, overhead, procurement, invoices | scoped Finance/Owner; portal only own issued client invoice | Finance workflow or derived routines; Owner cannot mutate posted history |
| file objects/uploads | explicit source record ACL and classification, not merely tenant | authorized source writer; append-only financial evidence |
| audit, outbox, idempotency, jobs | narrow service capabilities; safe audit projection to Owner | routines, no arbitrary operational-role DML |
| search docs/chunks | source ACL recheck plus scope, disabled by default | indexing service only; never allow model to grant scope |

All non-identity children inherit tenant policy even when not explicitly listed in §2–4. Missing/invalid context returns no rows and rejects writes. The backend credential is a trusted service: custom GUCs are not secure against someone with unrestricted direct SQL access. End users never receive that credential. Test SQL injection separately; restrict callable functions, fixed search_path, parameterized queries, no PUBLIC execute. Report rejected requests in a separate sanitized security log after transaction rollback; the failed business transaction cannot retain its own audit row.

Migration sequence: M001 identities/grants; M002 sessions/operators/clients; M003 samples/revisions/rates (add circular approved_revision FK after tables); M004 orders/components/confirmations; M005 lots/movements/cutting/stocktake; M006 lines/tallies/snapshots/component units (add snapshot source FK after both tables); M007 assemblies/allocations/QC; M008 ledger headers/accounts/lines/sealing; M009 rules/eligibility/payroll/overhead/invoices; M010 files/uploads and evidence FKs; M011 audit/idempotency/outbox/jobs; M012 functions/grants/RLS FORCE and policies; M013 optional search/extension. No app traffic until M012 tests pass. Each migration is one transaction where supported; failed migration rolls back. Production rollback is forward-fix for data migrations, never drop financial tables.

Future tripwires: append balanced lines in a later transaction -> reject; empty/unbalanced header at commit -> reject; two simultaneous dispatches of last 10m -> only one succeeds; two assemblies reuse component -> one fails; mixed-unit cutting ->422; first PASS of 3-contributor assembly ->3 wage credits/1 bonus; repeated PASS ->409 with unchanged money; pool reuse after tenant A rollback ->tenant B sees no A rows. No SQL migration or these runtime tests executed during planning.
