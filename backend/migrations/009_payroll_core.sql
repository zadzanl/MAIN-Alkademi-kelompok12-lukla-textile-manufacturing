-- Factory payroll persists versioned results; upstream order/tally/file tables are not present yet.
-- Apply atomically after M008; monetary facts are append-only after M012.
CREATE TABLE financial_rule_versions (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    rule_name text NOT NULL,
    effective_from date NOT NULL,
    effective_through date,
    parameters jsonb NOT NULL,
    status text NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','APPROVED','REJECTED')),
    approved_by uuid REFERENCES actors(id) ON DELETE RESTRICT,
    evidence_file_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    CHECK (effective_through IS NULL OR effective_from < effective_through),
    CHECK ((status = 'APPROVED') = (approved_by IS NOT NULL AND evidence_file_id IS NOT NULL)),
    CONSTRAINT financial_rules_no_overlap EXCLUDE USING gist (
        tenant_id WITH =, rule_name WITH =,
        daterange(effective_from, effective_through, '[)') WITH &&
    ) WHERE (status = 'APPROVED')
);
CREATE INDEX financial_rules_lookup ON financial_rule_versions (tenant_id, rule_name, status);
CREATE INDEX financial_rules_approver ON financial_rule_versions (approved_by);

CREATE TABLE eligibility_events (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    assembly_id uuid NOT NULL,
    passed_at timestamptz NOT NULL,
    rule_version_id uuid,
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, assembly_id),
    FOREIGN KEY (tenant_id, assembly_id) REFERENCES garment_assemblies(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, rule_version_id) REFERENCES financial_rule_versions(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX eligibility_rules ON eligibility_events (tenant_id, rule_version_id);

CREATE TABLE payroll_periods (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    period_start date NOT NULL,
    period_end date NOT NULL,
    timezone text NOT NULL,
    cutoff_local time NOT NULL,
    rule_version uuid NOT NULL,
    status text NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN','CALCULATED','PENDING_RULE','APPROVED','PAID','REVERSED')),
    approved_by uuid REFERENCES actors(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, rule_version) REFERENCES financial_rule_versions(tenant_id, id) ON DELETE RESTRICT,
    UNIQUE (tenant_id, period_start, period_end),
    CHECK (period_start < period_end),
    CONSTRAINT payroll_periods_timezone CHECK (timezone = 'Asia/Jakarta'),
    CONSTRAINT payroll_periods_cutoff_local CHECK (
        EXTRACT(SECOND FROM cutoff_local) = 0 AND cutoff_local < TIME '24:00:00'
    )
);
CREATE INDEX payroll_periods_approver ON payroll_periods (approved_by);

CREATE TABLE payroll_runs (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    period_id uuid NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    timezone text NOT NULL,
    cutoff_local time NOT NULL,
    rule_version_id uuid NOT NULL,
    status text NOT NULL CHECK (status IN ('OPEN','CALCULATED','PENDING_RULE','APPROVED','PAID')),
    input_hash bytea NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, period_id, version),
    CHECK (period_start < period_end),
    FOREIGN KEY (tenant_id, period_id) REFERENCES payroll_periods(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, rule_version_id) REFERENCES financial_rule_versions(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX payroll_runs_rule ON payroll_runs (tenant_id, rule_version_id);

CREATE TABLE wage_credits (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    garment_unit_id uuid NOT NULL,
    operator_id uuid NOT NULL,
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL,
    period_id uuid,
    reversal_of uuid,
    ledger_transaction_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, garment_unit_id) REFERENCES garment_units(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, period_id) REFERENCES payroll_periods(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, reversal_of) REFERENCES wage_credits(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, ledger_transaction_id) REFERENCES ledger_transactions(tenant_id, id) ON DELETE RESTRICT
);
CREATE UNIQUE INDEX wage_one_original_per_unit ON wage_credits (tenant_id, garment_unit_id)
    WHERE reversal_of IS NULL;
CREATE UNIQUE INDEX wage_one_reversal ON wage_credits (tenant_id, reversal_of)
    WHERE reversal_of IS NOT NULL;
CREATE INDEX wage_credits_period ON wage_credits (tenant_id, period_id);
CREATE INDEX wage_credits_operator ON wage_credits (tenant_id, operator_id);
CREATE INDEX wage_credits_ledger ON wage_credits (tenant_id, ledger_transaction_id);

CREATE TABLE payroll_run_credits (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    run_id uuid NOT NULL,
    source_tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    wage_credit_id uuid NOT NULL,
    committed boolean NOT NULL DEFAULT false,
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, run_id, source_tenant_id, wage_credit_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES payroll_runs(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (source_tenant_id, wage_credit_id) REFERENCES wage_credits(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX payroll_run_credits_source ON payroll_run_credits (source_tenant_id, wage_credit_id);
CREATE UNIQUE INDEX payroll_committed_credit ON payroll_run_credits (source_tenant_id, wage_credit_id)
    WHERE committed;

CREATE TABLE payroll_items (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    run_id uuid NOT NULL,
    recipient_id uuid NOT NULL,
    base_minor bigint NOT NULL CHECK (base_minor >= 0),
    meal_minor bigint NOT NULL CHECK (meal_minor >= 0),
    bonus_minor bigint NOT NULL CHECK (bonus_minor >= 0),
    currency char(3) NOT NULL,
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, run_id, recipient_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES payroll_runs(tenant_id, id) ON DELETE RESTRICT
);

CREATE TABLE payroll_payments (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    run_id uuid NOT NULL,
    external_reference text NOT NULL,
    evidence_file_id uuid NOT NULL,
    recorded_by uuid NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, run_id),
    FOREIGN KEY (tenant_id, run_id) REFERENCES payroll_runs(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX payroll_payments_recorder ON payroll_payments (recorded_by);

CREATE TABLE payroll_adjustments (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    period_id uuid NOT NULL,
    operator_id uuid NOT NULL,
    kind text NOT NULL CHECK (kind IN ('CREDIT','DEDUCTION')),
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL,
    reason text NOT NULL CHECK (length(trim(reason)) > 0),
    authorized_by uuid NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    correction_of uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, period_id) REFERENCES payroll_periods(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, correction_of) REFERENCES payroll_adjustments(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX payroll_adjustments_period ON payroll_adjustments (tenant_id, period_id);
CREATE INDEX payroll_adjustments_authorizer ON payroll_adjustments (authorized_by);

CREATE TABLE qc_bonus_accruals (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    assembly_id uuid NOT NULL,
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL,
    rule_version uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, rule_version) REFERENCES financial_rule_versions(tenant_id, id) ON DELETE RESTRICT,
    UNIQUE (tenant_id, assembly_id),
    FOREIGN KEY (tenant_id, assembly_id) REFERENCES garment_assemblies(tenant_id, id) ON DELETE RESTRICT
);

CREATE TABLE overhead_periods (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    starts_on date NOT NULL,
    ends_on date NOT NULL,
    total_minor bigint NOT NULL CHECK (total_minor >= 0),
    produced_units integer NOT NULL CHECK (produced_units >= 0),
    status text NOT NULL CHECK (status IN ('NO_OUTPUT','CALCULATED')),
    currency char(3) NOT NULL,
    rule_version_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, starts_on, ends_on),
    CHECK (starts_on < ends_on),
    CHECK ((status = 'NO_OUTPUT') = (produced_units = 0)),
    FOREIGN KEY (tenant_id, rule_version_id) REFERENCES financial_rule_versions(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX overhead_periods_rule ON overhead_periods (tenant_id, rule_version_id);

CREATE TABLE overhead_events (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    period_id uuid,
    starts_on date NOT NULL,
    ends_on date NOT NULL,
    rule_version uuid NOT NULL,
    kind text NOT NULL,
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL,
    source_ref text NOT NULL,
    authorized_by uuid NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, rule_version) REFERENCES financial_rule_versions(tenant_id, id) ON DELETE RESTRICT,
    CHECK (starts_on < ends_on),
    FOREIGN KEY (tenant_id, period_id) REFERENCES overhead_periods(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX overhead_events_period ON overhead_events (tenant_id, period_id);
CREATE INDEX overhead_events_window ON overhead_events (tenant_id, starts_on, ends_on);
CREATE INDEX overhead_events_authorizer ON overhead_events (authorized_by);
