-- S-001 probe v2: use fixed rule id to avoid argument subquery needing SELECT
\set ON_ERROR_STOP 0
\set ruleid '11111111-1111-1111-1111-111111111111'

SELECT set_config('app.tenant_id', (SELECT id::text FROM tenants WHERE tenant_code='S001TENANT'), false);
SELECT set_config('app.actor_id', (SELECT id::text FROM actors WHERE email='s001@example.test'), false);

\echo '=== B1 FinancePayroll proposes PENDING rule (expected: success) ==='
SELECT set_config('app.role','FinancePayroll',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT :'ruleid', id, 's001-b1', '2026-01-01', '{"currency":"IDR"}', 'PENDING' FROM tenants WHERE tenant_code='S001TENANT';

\echo '=== B2 FinancePayroll calls payroll_approve_rule (expected: 42501) ==='
SELECT payroll_approve_rule(:'ruleid', gen_random_uuid());

\echo '=== B3 verify PENDING remains ==='
SELECT payroll_read_rows('financial_rule_versions', :'ruleid', NULL, 10)->0->>'status' AS status;

\echo '=== B4 SELF-ESCALATION: same connection sets app.role=Owner then approves ==='
SELECT set_config('app.role','Owner',false);
SELECT payroll_approve_rule(:'ruleid', gen_random_uuid());
SELECT payroll_read_rows('financial_rule_versions', :'ruleid', NULL, 10)->0->>'status' AS status_after_escalation;

\echo '=== B5 missing role empty string PENDING insert (expected: denied) ==='
SELECT set_config('app.role','',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT gen_random_uuid(), id, 's001-b5', '2026-01-01', '{"currency":"IDR"}', 'PENDING' FROM tenants WHERE tenant_code='S001TENANT';

\echo '=== B6 unknown role PENDING insert (expected: denied) ==='
SELECT set_config('app.role','UnknownRole',false);
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT gen_random_uuid(), id, 's001-b6', '2026-01-01', '{"currency":"IDR"}', 'PENDING' FROM tenants WHERE tenant_code='S001TENANT';

\echo '=== B7 UPDATE approved rule evidence/fields after APPROVED (immutability) ==='
SELECT set_config('app.role','Owner',false);
UPDATE financial_rule_versions SET parameters='{"currency":"USD"}' WHERE id=:'ruleid';
