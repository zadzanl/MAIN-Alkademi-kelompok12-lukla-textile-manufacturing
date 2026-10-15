\set ON_ERROR_STOP 0
-- context = S001TENANT, attempt to write a row owned by S001OTHER tenant
SELECT set_config('app.tenant_id', (SELECT id::text FROM tenants WHERE tenant_code='S001TENANT'), false);
SELECT set_config('app.actor_id', (SELECT id::text FROM actors WHERE email='s001@example.test'), false);
SELECT set_config('app.role','FinancePayroll',false);

\echo '=== D1 cross-tenant INSERT (expect RLS WITH CHECK violation 42501) ==='
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT gen_random_uuid(), id, 's001-cross', '2026-01-01', '{"currency":"IDR"}', 'PENDING'
FROM tenants WHERE tenant_code='S001OTHER';

\echo '=== D2 cross-tenant UPDATE payroll_periods of other tenant (expect 0 rows) ==='
UPDATE payroll_periods SET status='OPEN' WHERE tenant_id = (SELECT id FROM tenants WHERE tenant_code='S001OTHER');

\echo '=== D3 RLS forced on owner? check relrowsecurity/relforcerowsecurity ==='
