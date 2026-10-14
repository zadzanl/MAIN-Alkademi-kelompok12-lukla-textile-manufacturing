-- Migration 001: Identities, Actors, Tenants, Idempotency, and Audit Events

-- Application runtime role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lukla_app') THEN
        CREATE ROLE lukla_app WITH LOGIN PASSWORD 'lukla_secret' NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END
$$;

-- Tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_code text NOT NULL UNIQUE,
    name text NOT NULL,
    kind text NOT NULL CHECK (kind IN ('CLIENT', 'INTERNAL_BRAND', 'FACTORY')),
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tenants_active ON tenants(active);

-- Actors table
CREATE TABLE IF NOT EXISTS actors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL,
    display_name text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_actors_lower_email ON actors (lower(email));

-- Idempotency Records table
CREATE TABLE IF NOT EXISTS idempotency_records (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    key text NOT NULL,
    operation_id text NOT NULL,
    canonical_payload_hash bytea NOT NULL,
    status text NOT NULL CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED')),
    response_status smallint NULL,
    response_body jsonb NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz NULL,
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT uq_idempotency_records UNIQUE (tenant_id, operation_id, key)
);

-- Audit Events table
CREATE TABLE IF NOT EXISTS audit_events (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    actor_id uuid NULL REFERENCES actors(id) ON DELETE RESTRICT,
    service_principal text NULL,
    action text NOT NULL,
    entity_type text NOT NULL,
    entity_id uuid NULL,
    request_id uuid NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS idx_audit_events_lookup ON audit_events (tenant_id, entity_type, entity_id);

-- Request Context Stored Procedure
CREATE OR REPLACE FUNCTION set_request_context(
    p_tenant_id uuid,
    p_actor_id uuid DEFAULT NULL,
    p_role text DEFAULT NULL,
    p_legal_owner_scope uuid[] DEFAULT NULL,
    p_beneficiary_scope uuid[] DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
    PERFORM set_config('app.tenant_id', p_tenant_id::text, true);
    IF p_actor_id IS NOT NULL THEN
        PERFORM set_config('app.actor_id', p_actor_id::text, true);
    ELSE
        PERFORM set_config('app.actor_id', '', true);
    END IF;
    IF p_role IS NOT NULL THEN
        PERFORM set_config('app.role', p_role, true);
    ELSE
        PERFORM set_config('app.role', '', true);
    END IF;
END;
$$;

-- Enable and FORCE Row-Level Security on tenant-scoped tables
ALTER TABLE idempotency_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotency_records FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON idempotency_records;
CREATE POLICY tenant_isolation_policy ON idempotency_records
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON audit_events;
CREATE POLICY tenant_isolation_policy ON audit_events
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

-- Grants to runtime application role lukla_app
GRANT USAGE ON SCHEMA public TO lukla_app;
GRANT SELECT, INSERT, UPDATE ON idempotency_records TO lukla_app;
GRANT SELECT, INSERT ON audit_events TO lukla_app;
GRANT SELECT ON tenants TO lukla_app;
GRANT SELECT ON actors TO lukla_app;
GRANT EXECUTE ON FUNCTION set_request_context TO lukla_app;
