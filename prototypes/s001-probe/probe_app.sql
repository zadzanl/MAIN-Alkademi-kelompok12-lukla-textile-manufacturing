-- Security probe as lukla_app (restricted role)
\set ON_ERROR_STOP 0
\echo '=== A1 direct INSERT wage_credits ==='
INSERT INTO wage_credits (tenant_id, garment_unit_id, operator_id, amount_minor, currency)
VALUES ('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000003', 999999, 'IDR');

\echo '=== A2 direct APPROVED rule insert with self-set role Owner ==='
SELECT set_config('app.role','Owner',false);
SELECT set_config('app.actor_id','00000000-0000-0000-0000-000000000009',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status, approved_by, evidence_file_id)
VALUES (gen_random_uuid(),'00000000-0000-0000-0000-000000000001','r2','2026-01-01','{}','APPROVED','00000000-0000-0000-0000-000000000009',gen_random_uuid());

\echo '=== A3 self-set role Owner, then call payroll_approve_rule on a real pending rule ==='
-- needs a tenant/actor/rule; created by admin fixture in probe_admin.sql
SELECT set_config('app.tenant_id', (SELECT id::text FROM tenants WHERE tenant_code='S001TENANT'), false);
SELECT set_config('app.actor_id', (SELECT id::text FROM actors WHERE email='s001@example.test'), false);
SELECT set_config('app.role','FinancePayroll',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT gen_random_uuid(), id, 's001-rule', '2026-01-01', '{"currency":"IDR"}', 'PENDING' FROM tenants WHERE tenant_code='S001TENANT';
\echo '--- now escalate role to Owner and approve ---'
SELECT set_config('app.role','Owner',false);
SELECT payroll_approve_rule((SELECT id FROM financial_rule_versions WHERE rule_name='s001-rule'), gen_random_uuid());

\echo '=== A4 advance run to PAID with self-set role ==='
SELECT set_config('app.role','FinancePayroll',false);
SELECT payroll_advance_run(gen_random_uuid(), 'PAID');

\echo '=== A5 read rows for another tenant id (cross-tenant) ==='
SELECT payroll_read_rows('payroll_runs', NULL, NULL, 5);
