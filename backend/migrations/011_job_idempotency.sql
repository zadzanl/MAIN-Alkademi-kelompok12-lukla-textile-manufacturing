-- M001 owns idempotency_records and its (tenant_id, operation_id, key) unique key.
-- M011 owns only job_runs. Apply atomically after M009, including retries after rollback.
CREATE TABLE job_runs (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    kind text NOT NULL CHECK (kind IN ('SATURDAY_PAYROLL','MONTHLY_OVERHEAD')),
    period_id uuid NOT NULL,
    scheduled_for timestamptz NOT NULL,
    status text NOT NULL CHECK (status IN ('RUNNING','SUCCEEDED','BLOCKED','FAILED')),
    error_code text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, kind, period_id),
    CHECK (status <> 'BLOCKED' OR error_code IS NOT NULL)
);
CREATE INDEX job_runs_period ON job_runs (tenant_id, period_id);
-- Job period IDs refer to payroll_periods for both weekly and monthly scheduling.
ALTER TABLE job_runs ADD CONSTRAINT job_runs_payroll_period
    FOREIGN KEY (tenant_id, period_id) REFERENCES payroll_periods(tenant_id, id) ON DELETE RESTRICT;
