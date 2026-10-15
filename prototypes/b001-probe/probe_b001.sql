-- Behavioral Assurance B-001 independent probe, run as lukla_app.
\set ON_ERROR_STOP 0
\pset pager off
\echo '=== P0 current role and privileges ==='
SELECT current_user, session_user;
SELECT has_table_privilege('lukla_app','financial_rule_versions','INSERT') AS can_insert_rule,
       has_table_privilege('lukla_app','financial_rule_versions','SELECT') AS can_select_rule,
       has_table_privilege('lukla_app','payroll_periods','INSERT') AS can_insert_period,
       has_table_privilege('lukla_app','payroll_periods','SELECT') AS can_select_period;

\echo '=== P1 seed tenant/actor as app role (should fail: no INSERT grant) ==='
SELECT set_config('app.role','Owner',false);
SELECT set_config('app.actor_id','',false);
INSERT INTO tenants (id, tenant_code, name, kind)
VALUES (gen_random_uuid(),'B001X','B001','CLIENT');

\echo '=== P2 empty-role PENDING insert: which layer raises? ==='
SELECT set_config('app.tenant_id',(SELECT id::text FROM tenants LIMIT 1),false);
SELECT set_config('app.actor_id',(SELECT id::text FROM actors LIMIT 1),false);
SELECT set_config('app.role','',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT gen_random_uuid(), id, 'b001-empty-role', '2026-01-01', '{"currency":"IDR"}', 'PENDING' FROM tenants LIMIT 1;

\echo '=== P3 unknown-role PENDING insert ==='
SELECT set_config('app.role','UnknownRole',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT gen_random_uuid(), id, 'b001-unknown-role', '2026-01-01', '{"currency":"IDR"}', 'PENDING' FROM tenants LIMIT 1;

\echo '=== P4 FinancePayroll PENDING insert (should succeed) ==='
SELECT set_config('app.role','FinancePayroll',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT gen_random_uuid(), id, 'b001-fin-pending', '2026-01-01', '{"currency":"IDR"}', 'PENDING' FROM tenants LIMIT 1;

\echo '=== P5 FinancePayroll approve attempt (should fail 42501) ==='
SELECT payroll_approve_rule((SELECT id FROM financial_rule_versions WHERE rule_name='b001-fin-pending'), gen_random_uuid());

\echo '=== P6 Owner approve attempt with evidence (should succeed) ==='
SELECT set_config('app.role','Owner',false);
SELECT payroll_approve_rule((SELECT id FROM financial_rule_versions WHERE rule_name='b001-fin-pending'), gen_random_uuid());

\echo '=== P7 readback via payroll_read_rows ==='
SELECT payroll_read_rows('financial_rule_versions',(SELECT id FROM financial_rule_versions WHERE rule_name='b001-fin-pending'));

\echo '=== P8 direct APPROVED insert as Owner (should fail) ==='
SELECT set_config('app.role','Owner',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status, approved_by, evidence_file_id)
SELECT gen_random_uuid(), id, 'b001-direct-approved', '2026-01-01', '{"currency":"IDR"}', 'APPROVED', (SELECT id FROM actors LIMIT 1), gen_random_uuid() FROM tenants LIMIT 1;

\echo '=== P9 timezone checks ==='
SELECT set_config('app.role','FinancePayroll',false);
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id,'2026-02-01','2026-02-08','UTC','12:00:00','fixture' FROM tenants LIMIT 1;
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id,'2026-03-01','2026-03-08','','12:00:00','fixture' FROM tenants LIMIT 1;
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id,'2026-04-01','2026-04-08','Asia/Jakarta','12:00:00','fixture' FROM tenants LIMIT 1;

\echo '=== P10 cutoff checks ==='
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id,'2026-05-01','2026-05-08','Asia/Jakarta','12:00:01','fixture' FROM tenants LIMIT 1;
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id,'2026-06-01','2026-06-08','Asia/Jakarta','12:00:00.000001','fixture' FROM tenants LIMIT 1;
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id,'2026-07-01','2026-07-08','Asia/Jakarta','24:00:00','fixture' FROM tenants LIMIT 1;
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id,'2026-08-01','2026-08-08','Asia/Jakarta','00:00:00','fixture' FROM tenants LIMIT 1;
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id,'2026-09-01','2026-09-08','Asia/Jakarta','23:59:00','fixture' FROM tenants LIMIT 1;
