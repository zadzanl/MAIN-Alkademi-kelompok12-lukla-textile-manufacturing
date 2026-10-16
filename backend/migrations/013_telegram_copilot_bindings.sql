-- Migration 013: Telegram Copilot Bot Bindings, Single-Use Enrollment Codes, and Update Idempotency
-- Additive migration preserving existing 001-012 tables and RLS boundaries.

CREATE TABLE IF NOT EXISTS telegram_enrollment_codes (
    code_hash text PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    actor_id uuid NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    role text NOT NULL CHECK (
        role IN (
            'Owner',
            'SampleTeam',
            'Warehouse',
            'ProductionHead',
            'Tailor',
            'QCInspector',
            'FinancePayroll',
            'MaklonClient'
        )
    ),
    legal_owner_id uuid NULL,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz NULL,
    consumed_by_chat_id text NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_telegram_enrollment_codes_tenant
    ON telegram_enrollment_codes (tenant_id, expires_at);

CREATE TABLE IF NOT EXISTS telegram_bindings (
    telegram_chat_id text PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    actor_id uuid NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    roles text[] NOT NULL,
    legal_owner_id uuid NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_bindings_active
    ON telegram_bindings (telegram_chat_id, active);

CREATE TABLE IF NOT EXISTS telegram_processed_updates (
    update_id bigint PRIMARY KEY,
    telegram_chat_id text NULL,
    status text NOT NULL CHECK (status IN ('CLAIMED', 'PROCESSED', 'REJECTED')),
    processed_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE telegram_enrollment_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_enrollment_codes FORCE ROW LEVEL SECURITY;

ALTER TABLE telegram_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_bindings FORCE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE ON telegram_enrollment_codes TO lukla_app;
GRANT SELECT, INSERT, UPDATE ON telegram_bindings TO lukla_app;
GRANT SELECT, INSERT, UPDATE ON telegram_processed_updates TO lukla_app;
