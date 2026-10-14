-- Migration 008: Core Double-Entry Ledger Engine & Invariant Hardening

-- Ledger Accounts Table
CREATE TABLE IF NOT EXISTS ledger_accounts (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    code text NOT NULL,
    name text NOT NULL,
    account_class text NOT NULL CHECK (account_class IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')),
    currency char(3) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT uq_ledger_accounts_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_ledger_accounts_lookup ON ledger_accounts (tenant_id, code, active);

-- Ledger Transactions Table
CREATE TABLE IF NOT EXISTS ledger_transactions (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    transaction_type text NOT NULL,
    source_type text NOT NULL DEFAULT 'MANUAL',
    source_id uuid NULL,
    posted_at timestamptz NOT NULL DEFAULT now(),
    posted_by uuid NULL REFERENCES actors(id) ON DELETE RESTRICT,
    reversal_of uuid NULL,
    created_xid xid8 NOT NULL DEFAULT pg_current_xact_id(),
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT fk_ledger_transactions_reversal FOREIGN KEY (tenant_id, reversal_of) REFERENCES ledger_transactions(tenant_id, id) ON DELETE RESTRICT
);

-- Partial unique index to enforce forward-only, single reversal per transaction
CREATE UNIQUE INDEX IF NOT EXISTS uq_ledger_tx_reversal 
ON ledger_transactions (tenant_id, reversal_of) 
WHERE reversal_of IS NOT NULL;

-- Composite B-Tree index for tenant-scoped cursor pagination
CREATE INDEX IF NOT EXISTS idx_ledger_tx_tenant_posted 
ON ledger_transactions (tenant_id, posted_at ASC, id ASC);

-- Trigger to forbid reversing an existing reversal transaction
CREATE OR REPLACE FUNCTION trg_fn_check_reversal_of_reversal()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_target_reversal_of uuid;
BEGIN
    IF NEW.reversal_of IS NOT NULL THEN
        SELECT reversal_of INTO v_target_reversal_of
        FROM ledger_transactions
        WHERE tenant_id = NEW.tenant_id AND id = NEW.reversal_of;

        IF v_target_reversal_of IS NOT NULL THEN
            RAISE EXCEPTION 'CANNOT_REVERSE_REVERSAL'
            USING ERRCODE = '23514',
            DETAIL = 'Target transaction is already a reversal and cannot be reversed';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_ledger_transactions_reversal_check ON ledger_transactions;
CREATE TRIGGER trg_ledger_transactions_reversal_check
BEFORE INSERT ON ledger_transactions
FOR EACH ROW
EXECUTE FUNCTION trg_fn_check_reversal_of_reversal();

-- Ledger Entries Table
CREATE TABLE IF NOT EXISTS ledger_entries (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    transaction_id uuid NOT NULL,
    account_id uuid NOT NULL,
    direction text NOT NULL CHECK (direction IN ('DEBIT', 'CREDIT')),
    amount_minor bigint NOT NULL CHECK (amount_minor > 0),
    currency char(3) NOT NULL,
    memo text NULL,
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT fk_ledger_entries_transaction FOREIGN KEY (tenant_id, transaction_id) REFERENCES ledger_transactions(tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_ledger_entries_account FOREIGN KEY (tenant_id, account_id) REFERENCES ledger_accounts(tenant_id, id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_ledger_entries_tx ON ledger_entries (tenant_id, transaction_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_account ON ledger_entries (tenant_id, account_id);

-- Strict Immutability Triggers
CREATE OR REPLACE FUNCTION trg_fn_prevent_ledger_modification()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'LEDGER_IMMUTABLE'
    USING ERRCODE = '55000',
    DETAIL = 'Direct update or delete on ledger transactions and entries is strictly prohibited';
END;
$$;

DROP TRIGGER IF EXISTS trg_ledger_transactions_immutable ON ledger_transactions;
CREATE TRIGGER trg_ledger_transactions_immutable
BEFORE UPDATE OR DELETE ON ledger_transactions
FOR EACH ROW
EXECUTE FUNCTION trg_fn_prevent_ledger_modification();

DROP TRIGGER IF EXISTS trg_ledger_entries_immutable ON ledger_entries;
CREATE TRIGGER trg_ledger_entries_immutable
BEFORE UPDATE OR DELETE ON ledger_entries
FOR EACH ROW
EXECUTE FUNCTION trg_fn_prevent_ledger_modification();

-- Late-Line Insertion Block Trigger
CREATE OR REPLACE FUNCTION trg_fn_check_late_line_insertion()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_tx_xid xid8;
BEGIN
    SELECT created_xid INTO v_tx_xid
    FROM ledger_transactions
    WHERE tenant_id = NEW.tenant_id AND id = NEW.transaction_id;

    IF v_tx_xid IS NULL THEN
        RAISE EXCEPTION 'TRANSACTION_NOT_FOUND' USING ERRCODE = '02000';
    END IF;

    IF v_tx_xid <> pg_current_xact_id() THEN
        RAISE EXCEPTION 'LATE_LINE_INSERTION_BLOCKED'
        USING ERRCODE = '55000',
        DETAIL = 'Cannot append entries to a previously committed ledger transaction';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_ledger_entries_late_line ON ledger_entries;
CREATE TRIGGER trg_ledger_entries_late_line
BEFORE INSERT ON ledger_entries
FOR EACH ROW
EXECUTE FUNCTION trg_fn_check_late_line_insertion();

-- Deferred Zero-Sum Balancing & Non-Empty Headers Trigger
CREATE OR REPLACE FUNCTION trg_fn_verify_transaction_balance()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_debit_count int;
    v_credit_count int;
    v_unbalanced_count int;
BEGIN
    -- Check non-empty headers: require >= 1 debit and >= 1 credit
    SELECT
        COUNT(*) FILTER (WHERE direction = 'DEBIT'),
        COUNT(*) FILTER (WHERE direction = 'CREDIT')
    INTO v_debit_count, v_credit_count
    FROM ledger_entries
    WHERE tenant_id = NEW.tenant_id AND transaction_id = NEW.id;

    IF v_debit_count = 0 OR v_credit_count = 0 THEN
        RAISE EXCEPTION 'EMPTY_OR_ONE_SIDED_TRANSACTION'
        USING ERRCODE = '23514',
        DETAIL = 'Transaction header must contain at least one debit and at least one credit entry';
    END IF;

    -- Zero-sum balance verification per currency
    SELECT COUNT(*)
    INTO v_unbalanced_count
    FROM (
        SELECT currency,
               SUM(CASE WHEN direction = 'DEBIT' THEN amount_minor ELSE -amount_minor END) AS balance
        FROM ledger_entries
        WHERE tenant_id = NEW.tenant_id AND transaction_id = NEW.id
        GROUP BY currency
        HAVING SUM(CASE WHEN direction = 'DEBIT' THEN amount_minor ELSE -amount_minor END) <> 0
    ) sub;

    IF v_unbalanced_count > 0 THEN
        RAISE EXCEPTION 'TRANSACTION_UNBALANCED'
        USING ERRCODE = '23514',
        DETAIL = 'Transaction debit total does not equal credit total per currency';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_verify_transaction_balance ON ledger_transactions;
CREATE CONSTRAINT TRIGGER trg_verify_transaction_balance
AFTER INSERT ON ledger_transactions
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION trg_fn_verify_transaction_balance();

-- Stored Procedure: append_ledger_transaction
CREATE OR REPLACE FUNCTION append_ledger_transaction(
    p_transaction_id uuid,
    p_tenant_id uuid,
    p_transaction_type text,
    p_currency text,
    p_entries jsonb,
    p_posted_by uuid DEFAULT NULL,
    p_reversal_of uuid DEFAULT NULL,
    p_source_type text DEFAULT 'MANUAL',
    p_source_id uuid DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_entry jsonb;
    v_account_id uuid;
    v_direction text;
    v_amount_minor bigint;
    v_entry_currency text;
    v_memo text;
BEGIN
    INSERT INTO ledger_transactions (
        id, tenant_id, transaction_type, source_type, source_id, posted_by, reversal_of
    ) VALUES (
        p_transaction_id, p_tenant_id, p_transaction_type, p_source_type, p_source_id, p_posted_by, p_reversal_of
    );

    FOR v_entry IN SELECT * FROM jsonb_array_elements(p_entries)
    LOOP
        v_account_id := (v_entry->>'account_id')::uuid;
        v_direction := v_entry->>'direction';
        v_amount_minor := (v_entry->>'amount_minor')::bigint;
        v_entry_currency := COALESCE(v_entry->>'currency', p_currency);
        v_memo := v_entry->>'memo';

        INSERT INTO ledger_entries (
            tenant_id, transaction_id, account_id, direction, amount_minor, currency, memo
        ) VALUES (
            p_tenant_id, p_transaction_id, v_account_id, v_direction, v_amount_minor, v_entry_currency, v_memo
        );
    END LOOP;

    RETURN p_transaction_id;
END;
$$;

-- Stored Procedure: seed_operational_accounts
CREATE OR REPLACE FUNCTION seed_operational_accounts(p_tenant_id uuid, p_currency char(3) DEFAULT 'IDR')
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
    INSERT INTO ledger_accounts (tenant_id, code, name, account_class, currency, active)
    VALUES
        (p_tenant_id, 'CUSTODIAL_MATERIAL', 'Custodial Client Material', 'ASSET', p_currency, true),
        (p_tenant_id, 'CUSTODIAL_OBLIGATION', 'Custodial Obligation to Client', 'LIABILITY', p_currency, true),
        (p_tenant_id, 'RAW_MATERIAL_ASSET', 'Raw Material Asset', 'ASSET', p_currency, true),
        (p_tenant_id, 'ACCOUNTS_PAYABLE', 'Accounts Payable', 'LIABILITY', p_currency, true),
        (p_tenant_id, 'WIP_DIRECT_LABOR', 'WIP Direct Labor', 'EXPENSE', p_currency, true),
        (p_tenant_id, 'WAGES_PAYABLE', 'Wages Payable', 'LIABILITY', p_currency, true)
    ON CONFLICT (tenant_id, code) DO NOTHING;
END;
$$;

-- Row Level Security on Ledger Tables
ALTER TABLE ledger_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_accounts FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON ledger_accounts;
CREATE POLICY tenant_isolation_policy ON ledger_accounts
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE ledger_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_transactions FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON ledger_transactions;
CREATE POLICY tenant_isolation_policy ON ledger_transactions
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE ledger_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_entries FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON ledger_entries;
CREATE POLICY tenant_isolation_policy ON ledger_entries
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

-- Permissions for runtime unprivileged application role lukla_app
GRANT SELECT, INSERT ON ledger_accounts TO lukla_app;
GRANT SELECT, INSERT ON ledger_transactions TO lukla_app;
GRANT SELECT, INSERT ON ledger_entries TO lukla_app;
GRANT EXECUTE ON FUNCTION append_ledger_transaction TO lukla_app;
GRANT EXECUTE ON FUNCTION seed_operational_accounts TO lukla_app;

-- Explicitly revoke direct UPDATE and DELETE table privileges on posted ledger tables
REVOKE UPDATE, DELETE ON ledger_transactions FROM lukla_app;
REVOKE UPDATE, DELETE ON ledger_entries FROM lukla_app;
