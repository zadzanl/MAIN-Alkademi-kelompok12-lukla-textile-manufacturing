-- Behavioral Assurance B-001 probe v3, run as lukla_app.
-- Each check is its own transaction to mirror pytest's `with app.begin()`,
-- so an expected failure cannot contaminate the next assertion.
\set ON_ERROR_STOP 0
\pset pager off

\echo '=== P0 identity and table privileges ==='
SELECT current_user AS running_as;
SELECT has_table_privilege('lukla_app','financial_rule_versions','INSERT') AS rule_insert,
       has_table_privilege('lukla_app','financial_rule_versions','SELECT') AS rule_select,
       has_table_privilege('lukla_app','payroll_periods','INSERT') AS period_insert,
       has_table_privilege('lukla_app','payroll_periods','SELECT') AS period_select;

\echo '=== P1 empty role, PENDING insert (expect RULE_APPROVAL_FORBIDDEN 42501) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, '');
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
VALUES (:'rule_empty'::uuid, :'tenant_id'::uuid, 'b001-empty', '2027-01-01', '{"currency":"IDR"}', 'PENDING');
ROLLBACK;

\echo '=== P2 unknown role, PENDING insert (expect 42501) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'UnknownRole');
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
VALUES (:'rule_unknown'::uuid, :'tenant_id'::uuid, 'b001-unknown', '2027-01-01', '{"currency":"IDR"}', 'PENDING');
ROLLBACK;

\echo '=== P3 FinancePayroll PENDING insert (expect success) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
VALUES (:'rule_fin'::uuid, :'tenant_id'::uuid, 'b001-fin', '2027-01-01', '{"currency":"IDR"}', 'PENDING');
COMMIT;

\echo '=== P4 FinancePayroll approve via literal id (expect RULE_APPROVAL_FORBIDDEN 42501) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
SELECT payroll_approve_rule(:'rule_fin'::uuid, :'evidence'::uuid);
ROLLBACK;

\echo '=== P5 readback still PENDING after denied approval ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
SELECT payroll_read_rows('financial_rule_versions', :'rule_fin'::uuid);
ROLLBACK;

\echo '=== P6 Owner approve with evidence (expect success) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'Owner');
SELECT payroll_approve_rule(:'rule_fin'::uuid, :'evidence'::uuid);
COMMIT;

\echo '=== P7 readback APPROVED with approved_by/evidence ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'Owner');
SELECT payroll_read_rows('financial_rule_versions', :'rule_fin'::uuid);
ROLLBACK;

\echo '=== P8 Owner direct APPROVED insert (expect RULE_APPROVAL_FORBIDDEN) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'Owner');
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status, approved_by, evidence_file_id)
VALUES (:'rule_direct'::uuid, :'tenant_id'::uuid, 'b001-direct', '2027-01-01', '{"currency":"IDR"}', 'APPROVED', :'actor_id'::uuid, :'evidence'::uuid);
ROLLBACK;

\echo '=== P9 Owner direct REJECTED insert (expect RULE_APPROVAL_FORBIDDEN) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'Owner');
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
VALUES (:'rule_rej'::uuid, :'tenant_id'::uuid, 'b001-rejected', '2027-01-01', '{"currency":"IDR"}', 'REJECTED');
ROLLBACK;

\echo '=== P10 timezone rejects: UTC / empty / Asia/Bangkok (expect 23514) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-01-01','2027-01-08','UTC','12:00:00','fx');
ROLLBACK;
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-02-01','2027-02-08','','12:00:00','fx');
ROLLBACK;
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-03-01','2027-03-08','Asia/Bangkok','12:00:00','fx');
ROLLBACK;

\echo '=== P11 timezone accept: Asia/Jakarta (expect success) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-04-01','2027-04-08','Asia/Jakarta','12:00:00','fx');
COMMIT;

\echo '=== P12 cutoff rejects: 12:00:01 / fractional / 24:00:00 (expect 23514) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-05-01','2027-05-08','Asia/Jakarta','12:00:01','fx');
ROLLBACK;
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-06-01','2027-06-08','Asia/Jakarta','12:00:00.000001','fx');
ROLLBACK;
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-07-01','2027-07-08','Asia/Jakarta','24:00:00','fx');
ROLLBACK;

\echo '=== P13 cutoff accepts: 00:00:00 / 12:00:00 / 23:59:00 (expect success) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-08-01','2027-08-08','Asia/Jakarta','00:00:00','fx');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-09-01','2027-09-08','Asia/Jakarta','12:00:00','fx');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-10-01','2027-10-08','Asia/Jakarta','23:59:00','fx');
COMMIT;

\echo '=== P14 extra boundary: 23:59:59 (expect 23514, whole-minute) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-11-01','2027-11-08','Asia/Jakarta','23:59:59','fx');
ROLLBACK;

\echo '=== P15 extra boundary: asia/jakarta lowercase (informational) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'FinancePayroll');
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
VALUES (:'tenant_id'::uuid,'2027-12-01','2027-12-08','asia/jakarta','12:00:00','fx');
ROLLBACK;

\echo '=== P16 DELETE of a rule as Owner (expect RULE_APPROVAL_FORBIDDEN) ==='
BEGIN;
SELECT set_request_context(:'tenant_id'::uuid, :'actor_id'::uuid, 'Owner');
DELETE FROM financial_rule_versions WHERE id = :'rule_fin'::uuid;
ROLLBACK;
