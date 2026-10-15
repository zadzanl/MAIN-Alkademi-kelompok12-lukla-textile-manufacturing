\set ON_ERROR_STOP 1
SELECT set_config('app.tenant_id',(SELECT id::text FROM tenants WHERE tenant_code='S001TENANT'),false);
SELECT set_config('app.actor_id',(SELECT id::text FROM actors WHERE email='s001@example.test'),false);
SELECT set_config('app.role','Owner',false);

INSERT INTO tenants (id, tenant_code, name, kind)
VALUES ('aaaaaaaa-0000-0000-0000-00000000000a','S001OTHER','S001 Other','CLIENT')
ON CONFLICT (tenant_code) DO NOTHING;

INSERT INTO financial_rule_versions (id, tenant_id, rule_name, effective_from, parameters, status)
SELECT 'eeeeeeee-0000-0000-0000-00000000000e'::uuid, t.id, 'r', '2026-01-01', '{"currency":"IDR"}', 'PENDING'
FROM tenants t WHERE t.tenant_code='S001TENANT'
ON CONFLICT DO NOTHING;
SELECT payroll_approve_rule('eeeeeeee-0000-0000-0000-00000000000e'::uuid, gen_random_uuid());

ALTER TABLE wage_credits DISABLE TRIGGER USER;
ALTER TABLE payroll_runs DISABLE TRIGGER USER;
ALTER TABLE payroll_run_credits DISABLE TRIGGER USER;

INSERT INTO wage_credits (id, tenant_id, garment_unit_id, operator_id, amount_minor, currency, period_id)
SELECT 'cccccccc-0000-0000-0000-00000000000c', t.id, gen_random_uuid(), a.id, 1000, 'IDR', p.id
FROM tenants t, actors a, payroll_periods p
WHERE t.tenant_code='S001TENANT' AND a.email='s001@example.test' AND p.period_start='2026-04-01'
ON CONFLICT DO NOTHING;

INSERT INTO payroll_runs (id, tenant_id, period_id, period_start, period_end, timezone, cutoff_local, rule_version_id, status, input_hash, version)
SELECT 'dddddddd-0000-0000-0000-00000000000d', t.id, p.id, p.period_start, p.period_end, p.timezone, p.cutoff_local,
       'eeeeeeee-0000-0000-0000-00000000000e'::uuid, 'CALCULATED',
       decode(md5('cccccccc-0000-0000-0000-00000000000c:1000:IDR'),'hex'), 1
FROM tenants t, payroll_periods p
WHERE t.tenant_code='S001TENANT' AND p.period_start='2026-04-01'
ON CONFLICT DO NOTHING;

INSERT INTO payroll_run_credits (id, tenant_id, run_id, source_tenant_id, wage_credit_id, committed)
SELECT gen_random_uuid(), t.id, 'dddddddd-0000-0000-0000-00000000000d', t.id, 'cccccccc-0000-0000-0000-00000000000c', false
FROM tenants t WHERE t.tenant_code='S001TENANT'
ON CONFLICT DO NOTHING;

ALTER TABLE wage_credits ENABLE TRIGGER USER;
ALTER TABLE payroll_runs ENABLE TRIGGER USER;
ALTER TABLE payroll_run_credits ENABLE TRIGGER USER;

SELECT 'run_fixture_ready' AS status, (SELECT status FROM payroll_runs WHERE id='dddddddd-0000-0000-0000-00000000000d') AS run_status;
