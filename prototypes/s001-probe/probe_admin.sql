-- Admin fixture (migration owner) for the S-001 security probe
\set ON_ERROR_STOP 1
INSERT INTO tenants (id, tenant_code, name, kind)
VALUES (gen_random_uuid(), 'S001TENANT', 'S001 Tenant', 'CLIENT')
ON CONFLICT (tenant_code) DO NOTHING;
INSERT INTO actors (id, email, display_name)
VALUES (gen_random_uuid(), 's001@example.test', 'S001 Actor')
ON CONFLICT DO NOTHING;
SELECT 'fixture-ok' AS status;
