\set ON_ERROR_STOP 0
SELECT set_config('app.tenant_id', (SELECT id::text FROM tenants WHERE tenant_code='S001TENANT'), false);
SELECT set_config('app.actor_id', (SELECT id::text FROM actors WHERE email='s001@example.test'), false);

\echo '=== E1 QCInspector advances CALCULATED run to APPROVED (should require Owner/Finance?) ==='
SELECT set_config('app.role','QCInspector',false);
SELECT payroll_advance_run('dddddddd-0000-0000-0000-00000000000d', 'APPROVED');

\echo '=== E2 ProductionHead advances APPROVED run to PAID ==='
SELECT set_config('app.role','ProductionHead',false);
SELECT payroll_advance_run('dddddddd-0000-0000-0000-00000000000d', 'PAID');

\echo '=== E3 read final run status via checked reader ==='
SELECT payroll_read_rows('payroll_runs', 'dddddddd-0000-0000-0000-00000000000d', NULL, 1)->0->>'status' AS status;
