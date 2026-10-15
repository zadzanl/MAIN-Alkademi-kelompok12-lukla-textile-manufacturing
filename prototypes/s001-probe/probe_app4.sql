-- S-001 probe v4: set context FIRST, then M009 CHECK semantics
\set ON_ERROR_STOP 0
SELECT set_config('app.tenant_id', (SELECT id::text FROM tenants WHERE tenant_code='S001TENANT'), false);
SELECT set_config('app.actor_id', (SELECT id::text FROM actors WHERE email='s001@example.test'), false);
SELECT set_config('app.role','FinancePayroll',false);

\echo '=== C1 invalid timezone UTC (expect 23514 payroll_periods_timezone) ==='
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id, '2026-01-01', '2026-01-08', 'UTC', '12:00:00', 'r' FROM tenants WHERE tenant_code='S001TENANT';

\echo '=== C2 invalid cutoff 12:00:01 (expect 23514 cutoff) ==='
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id, '2026-02-01', '2026-02-08', 'Asia/Jakarta', '12:00:01', 'r' FROM tenants WHERE tenant_code='S001TENANT';

\echo '=== C3 invalid cutoff 24:00:00 (expect 23514 cutoff) ==='
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id, '2026-03-01', '2026-03-08', 'Asia/Jakarta', '24:00:00', 'r' FROM tenants WHERE tenant_code='S001TENANT';

\echo '=== C4 valid cutoff 23:59:00 (expect INSERT 0 1) ==='
INSERT INTO payroll_periods (tenant_id, period_start, period_end, timezone, cutoff_local, rule_version)
SELECT id, '2026-04-01', '2026-04-08', 'Asia/Jakarta', '23:59:00', 'r' FROM tenants WHERE tenant_code='S001TENANT';

\echo '=== C6 cross-tenant rule insert: context=S001TENANT, target=S001OTHER (expect RLS violation) ==='
INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT gen_random_uuid(), id, 's001-cross', '2026-01-01', '{"currency":"IDR"}', 'PENDING' FROM tenants WHERE tenant_code='S001OTHER';

\echo '=== C7 read rows for other tenant via checked reader (expect 0 rows, no leak) ==='
SELECT payroll_read_rows('financial_rule_versions', NULL, NULL, 100);
