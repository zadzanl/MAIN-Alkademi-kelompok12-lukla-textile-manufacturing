-- M001 owns set_request_context, idempotency_records and their grants/RLS.
-- M008 owns ledger entries and all ledger triggers. This migration does not replace them.
-- The trusted pool credential must never be exposed: custom GUCs are not authentication.
-- Apply M012 in one transaction after M001/M006/M007/M008/M009/M011.
-- The checked read API pages by UUID (at most 1000 rows); phase 4 can add
-- purpose-built filtered readers when a list needs time ordering or richer scope.

CREATE FUNCTION payroll_context_tenant() RETURNS uuid LANGUAGE plpgsql VOLATILE
SECURITY INVOKER SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_tenant text := current_setting('app.tenant_id', true);
    v_actor text := current_setting('app.actor_id', true);
    v_role text := current_setting('app.role', true);
BEGIN
    IF v_tenant IS NULL OR v_tenant = '' OR v_actor IS NULL OR v_actor = '' OR
       v_role IS NULL OR v_role NOT IN
       ('Owner','ProductionHead','QCInspector','FinancePayroll','ServicePayrollJob','ServiceOverheadJob') THEN
        RAISE EXCEPTION 'TENANT_CONTEXT_MISSING' USING ERRCODE = '42501';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM tenants WHERE id = v_tenant::uuid AND active)
       OR NOT EXISTS (SELECT 1 FROM actors WHERE id = v_actor::uuid AND active) THEN
        RAISE EXCEPTION 'TENANT_CONTEXT_MISSING' USING ERRCODE = '42501';
    END IF;
    RETURN v_tenant::uuid;
END $$;
REVOKE ALL ON FUNCTION payroll_context_tenant() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION payroll_context_tenant() TO lukla_app;

-- RLS predicates are per-row; an empty scan does not invoke this check.
-- Every callable calculation validates context before its first table access.

-- M007 cannot reference M009's eligibility table. A first PASS records the
-- unvalued event here; pending rules still write no monetary row.
CREATE FUNCTION payroll_record_eligibility() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    IF NEW.disposition = 'PASS' THEN
        INSERT INTO eligibility_events (tenant_id, assembly_id, passed_at)
        VALUES (NEW.tenant_id, NEW.assembly_id, NEW.created_at)
        ON CONFLICT (tenant_id, assembly_id) DO NOTHING;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER qc_first_pass_eligibility AFTER INSERT ON qc_inspections
    FOR EACH ROW EXECUTE FUNCTION payroll_record_eligibility();

-- Guards execute on direct SQL as well as routine writes. No unapproved policy can mint monetary rows.
CREATE FUNCTION payroll_monetary_guard() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_rule uuid;
    v_date date;
    v_currency char(3);
    v_rule_id uuid;
BEGIN
    IF TG_TABLE_NAME = 'wage_credits' THEN
        SELECT p.rule_version, p.period_start INTO v_rule, v_date
        FROM payroll_periods p WHERE p.tenant_id = NEW.tenant_id AND p.id = NEW.period_id;
        IF EXISTS (SELECT 1 FROM payroll_periods p WHERE (p.tenant_id, p.id) =
            (NEW.tenant_id, NEW.period_id) AND p.status IN ('APPROVED','PAID','REVERSED')) THEN
            RAISE EXCEPTION 'APPROVED_RUN_IMMUTABLE' USING ERRCODE = '55000';
        END IF;
        IF NEW.reversal_of IS NOT NULL OR NEW.period_id IS NULL OR NOT EXISTS (
            SELECT 1 FROM garment_units u JOIN piece_rate_snapshots s
              ON (s.tenant_id, s.id) = (u.tenant_id, u.piece_rate_snapshot_id)
                        JOIN sewing_tallies t ON (t.tenant_id, t.id) = (u.tenant_id, u.source_tally_id)
                                                JOIN assembly_components c ON (c.tenant_id, c.garment_unit_id) = (u.tenant_id, u.id)
                                                JOIN eligibility_events e ON (e.tenant_id, e.assembly_id) = (c.tenant_id, c.assembly_id)
                        WHERE (u.tenant_id, u.id) = (NEW.tenant_id, NEW.garment_unit_id)
              AND u.status = 'QC_PASS' AND u.operator_id = NEW.operator_id
                            AND t.status = 'VERIFIED'
                            AND (e.passed_at AT TIME ZONE 'Asia/Jakarta')::date >= v_date
                            AND (e.passed_at AT TIME ZONE 'Asia/Jakarta')::date < (SELECT period_end FROM payroll_periods
                                    WHERE (tenant_id, id) = (NEW.tenant_id, NEW.period_id))
              AND s.currency = NEW.currency AND s.amount_minor = NEW.amount_minor
        ) THEN RAISE EXCEPTION 'WAGE_INPUT_INVALID' USING ERRCODE = '23514'; END IF;
    ELSIF TG_TABLE_NAME = 'qc_bonus_accruals' THEN
        SELECT (e.passed_at AT TIME ZONE 'Asia/Jakarta')::date, s.currency INTO v_date, v_currency
        FROM eligibility_events e
        JOIN assembly_components c ON (c.tenant_id, c.assembly_id) = (e.tenant_id, e.assembly_id)
        JOIN garment_units u ON (u.tenant_id, u.id) = (c.tenant_id, c.garment_unit_id)
        JOIN piece_rate_snapshots s ON (s.tenant_id, s.id) = (u.tenant_id, u.piece_rate_snapshot_id)
        WHERE (e.tenant_id, e.assembly_id) = (NEW.tenant_id, NEW.assembly_id)
        LIMIT 1;
        v_rule := NEW.rule_version;
                IF v_date IS NULL OR v_currency IS DISTINCT FROM NEW.currency OR EXISTS (
                        SELECT 1 FROM assembly_components c
                        JOIN garment_units u ON (u.tenant_id, u.id) = (c.tenant_id, c.garment_unit_id)
                        JOIN piece_rate_snapshots s ON (s.tenant_id, s.id) = (u.tenant_id, u.piece_rate_snapshot_id)
                        WHERE (c.tenant_id, c.assembly_id) = (NEW.tenant_id, NEW.assembly_id)
                            AND s.currency <> NEW.currency
                ) OR NOT EXISTS (
            SELECT 1 FROM garment_assemblies a WHERE (a.tenant_id, a.id) = (NEW.tenant_id, NEW.assembly_id)
            AND a.status = 'QC_PASS'
        ) THEN RAISE EXCEPTION 'BONUS_INPUT_INVALID' USING ERRCODE = '23514'; END IF;
    ELSIF TG_TABLE_NAME = 'overhead_events' THEN
        v_rule := NEW.rule_version;
        v_date := NEW.starts_on;
    ELSIF TG_TABLE_NAME = 'overhead_periods' THEN
        v_rule_id := NEW.rule_version_id;
        v_rule := NEW.rule_version_id;
        v_date := NEW.starts_on;
    ELSIF TG_TABLE_NAME = 'payroll_items' THEN
        SELECT r.rule_version_id, p.period_start, r.rule_version_id INTO v_rule, v_date, v_rule_id FROM payroll_runs r
        JOIN financial_rule_versions f ON (f.tenant_id, f.id) = (r.tenant_id, r.rule_version_id)
        JOIN payroll_periods p ON (p.tenant_id, p.id) = (r.tenant_id, r.period_id)
        WHERE (r.tenant_id, r.id) = (NEW.tenant_id, NEW.run_id);
        IF EXISTS (SELECT 1 FROM payroll_items i WHERE (i.tenant_id, i.run_id) = (NEW.tenant_id, NEW.run_id)
                   AND i.currency <> NEW.currency) THEN
            RAISE EXCEPTION 'CURRENCY_MISMATCH' USING ERRCODE = '23514';
        END IF;
    ELSIF TG_TABLE_NAME = 'payroll_adjustments' THEN
        SELECT rule_version, period_start INTO v_rule, v_date FROM payroll_periods
        WHERE (tenant_id, id) = (NEW.tenant_id, NEW.period_id);
    END IF;
    IF v_rule IS NULL OR v_date IS NULL OR NOT EXISTS (
        SELECT 1 FROM financial_rule_versions f
        WHERE f.tenant_id = NEW.tenant_id AND f.id = v_rule AND f.status = 'APPROVED'
                    AND (v_rule_id IS NULL OR f.id = v_rule_id)
          AND f.effective_from <= v_date
          AND (f.effective_through IS NULL OR v_date < f.effective_through)
    ) THEN
        RAISE EXCEPTION 'FINANCIAL_RULE_PENDING' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;

-- Terminal periods cannot be reopened to bypass the run's immutable state.
CREATE FUNCTION payroll_period_transition() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    IF (to_jsonb(NEW) - 'status' - 'updated_at') IS DISTINCT FROM
       (to_jsonb(OLD) - 'status' - 'updated_at') OR
       NOT (CASE OLD.status
           WHEN 'OPEN' THEN NEW.status IN ('CALCULATED','PENDING_RULE')
           WHEN 'PENDING_RULE' THEN NEW.status IN ('CALCULATED','PENDING_RULE')
           WHEN 'CALCULATED' THEN NEW.status IN ('CALCULATED','PENDING_RULE','APPROVED')
           WHEN 'APPROVED' THEN NEW.status = 'PAID'
           WHEN 'PAID' THEN NEW.status = 'REVERSED'
           ELSE false
       END) THEN
        RAISE EXCEPTION 'APPROVED_RUN_IMMUTABLE' USING ERRCODE = '55000';
    END IF;
    IF NEW.status IN ('APPROVED','PAID') AND NEW.status IS DISTINCT FROM OLD.status
       AND NOT EXISTS (SELECT 1 FROM payroll_runs r WHERE
           (r.tenant_id, r.period_id) = (NEW.tenant_id, NEW.id)
           AND r.status = NEW.status) THEN
        RAISE EXCEPTION 'RUN_INPUT_INVALID' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER payroll_period_transition BEFORE UPDATE ON payroll_periods
    FOR EACH ROW EXECUTE FUNCTION payroll_period_transition();

DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['wage_credits','qc_bonus_accruals','overhead_events',
                             'overhead_periods','payroll_items','payroll_adjustments'] LOOP
        EXECUTE format('CREATE TRIGGER payroll_rule_guard BEFORE INSERT ON %I FOR EACH ROW EXECUTE FUNCTION payroll_monetary_guard()', t);
    END LOOP;
END $$;

-- A run can be approved once. Credits from draft recalculations remain reusable until approval.
CREATE FUNCTION payroll_run_transition() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_period payroll_periods%ROWTYPE;
    v_hash bytea;
    v_credits integer;
BEGIN
    SELECT * INTO v_period FROM payroll_periods
    WHERE (tenant_id, id) = (NEW.tenant_id, NEW.period_id) FOR UPDATE;
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'CALCULATED' OR NOT EXISTS (
            SELECT 1 FROM financial_rule_versions f WHERE (f.tenant_id, f.id) =
            (NEW.tenant_id, NEW.rule_version_id) AND f.status = 'APPROVED'
        ) THEN
            RAISE EXCEPTION 'FINANCIAL_RULE_PENDING' USING ERRCODE = '23514';
        END IF;
    ELSE
        IF OLD.status = 'PAID' OR NEW.status NOT IN ('APPROVED','PAID') OR
           (NEW.status = 'APPROVED' AND OLD.status <> 'CALCULATED') OR
           (NEW.status = 'PAID' AND OLD.status <> 'APPROVED') OR
           (to_jsonb(NEW) - 'status') IS DISTINCT FROM (to_jsonb(OLD) - 'status') THEN
            RAISE EXCEPTION 'APPROVED_RUN_IMMUTABLE' USING ERRCODE = '55000';
        END IF;
    END IF;
    IF v_period.id IS NULL OR v_period.status IN ('PAID','REVERSED') OR
       (v_period.status = 'APPROVED' AND (TG_OP = 'INSERT' OR NEW.status <> 'PAID')) OR
       (NEW.period_start, NEW.period_end, NEW.timezone, NEW.cutoff_local) IS DISTINCT FROM
       (v_period.period_start, v_period.period_end, v_period.timezone, v_period.cutoff_local) OR
       NOT EXISTS (SELECT 1 FROM financial_rule_versions f WHERE
           (f.tenant_id, f.id) = (NEW.tenant_id, NEW.rule_version_id)
           AND f.id = v_period.rule_version AND f.status = 'APPROVED'
           AND f.effective_from <= v_period.period_start
           AND (f.effective_through IS NULL OR v_period.period_start < f.effective_through)) THEN
        RAISE EXCEPTION 'RUN_INPUT_INVALID' USING ERRCODE = '23514';
    END IF;
    SELECT count(*), decode(md5(string_agg(c.id::text || ':' || c.amount_minor::text || ':' || c.currency,
        ',' ORDER BY c.id)), 'hex') INTO v_credits, v_hash
    FROM wage_credits c WHERE c.tenant_id = NEW.tenant_id AND c.period_id = NEW.period_id
      AND c.reversal_of IS NULL;
    IF v_credits = 0 OR NEW.input_hash IS DISTINCT FROM v_hash THEN
        RAISE EXCEPTION 'RUN_INPUT_INVALID' USING ERRCODE = '23514';
    END IF;
    IF TG_OP = 'INSERT' THEN RETURN NEW; END IF;
    IF NEW.status = 'APPROVED' THEN
        IF NOT EXISTS (SELECT 1 FROM financial_rule_versions f
           WHERE (f.tenant_id, f.id) = (NEW.tenant_id, NEW.rule_version_id)
           AND f.status = 'APPROVED') THEN
            RAISE EXCEPTION 'FINANCIAL_RULE_PENDING' USING ERRCODE = '23514';
        END IF;
                IF EXISTS (
                        (SELECT c.tenant_id, c.id FROM wage_credits c WHERE c.tenant_id = NEW.tenant_id
                            AND c.period_id = NEW.period_id AND c.reversal_of IS NULL
                         EXCEPT SELECT l.source_tenant_id, l.wage_credit_id FROM payroll_run_credits l
                            WHERE (l.tenant_id, l.run_id) = (NEW.tenant_id, NEW.id))
                        UNION ALL
                        (SELECT l.source_tenant_id, l.wage_credit_id FROM payroll_run_credits l
                            WHERE (l.tenant_id, l.run_id) = (NEW.tenant_id, NEW.id)
                         EXCEPT SELECT c.tenant_id, c.id FROM wage_credits c WHERE c.tenant_id = NEW.tenant_id
                            AND c.period_id = NEW.period_id AND c.reversal_of IS NULL)
                ) THEN
                        RAISE EXCEPTION 'RUN_INPUT_INVALID' USING ERRCODE = '23514';
                END IF;
    ELSIF NOT EXISTS (SELECT 1 FROM payroll_payments
        WHERE (tenant_id, run_id) = (NEW.tenant_id, NEW.id)) THEN
        RAISE EXCEPTION 'PAYROLL_NOT_PAID' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER payroll_run_transition BEFORE INSERT OR UPDATE ON payroll_runs
    FOR EACH ROW EXECUTE FUNCTION payroll_run_transition();
CREATE FUNCTION payroll_commit_run_credits() RETURNS trigger LANGUAGE plpgsql
SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
    IF NEW.status = 'APPROVED' AND OLD.status = 'CALCULATED' THEN
        UPDATE payroll_run_credits SET committed = true
        WHERE tenant_id = NEW.tenant_id AND run_id = NEW.id;
        UPDATE payroll_periods SET status = 'APPROVED', updated_at = now()
        WHERE (tenant_id, id) = (NEW.tenant_id, NEW.period_id);
    ELSIF NEW.status = 'PAID' AND OLD.status = 'APPROVED' THEN
        UPDATE payroll_periods SET status = 'PAID', updated_at = now()
        WHERE (tenant_id, id) = (NEW.tenant_id, NEW.period_id);
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER payroll_run_commit_credits AFTER UPDATE ON payroll_runs
    FOR EACH ROW EXECUTE FUNCTION payroll_commit_run_credits();
CREATE TRIGGER payroll_run_delete BEFORE DELETE ON payroll_runs
    FOR EACH ROW EXECUTE FUNCTION payroll_snapshot_immutable();

CREATE FUNCTION payroll_child_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_status text;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'APPROVED_RUN_IMMUTABLE' USING ERRCODE = '55000';
    END IF;
    SELECT status INTO v_status FROM payroll_runs
    WHERE tenant_id = NEW.tenant_id AND id = NEW.run_id FOR UPDATE;
    IF v_status IS NULL THEN
        RAISE EXCEPTION 'RUN_NOT_FOUND' USING ERRCODE = '23514';
    END IF;
     IF v_status IN ('APPROVED','PAID') OR
         (TG_TABLE_NAME = 'payroll_run_credits' AND NEW.committed) THEN
        RAISE EXCEPTION 'APPROVED_RUN_IMMUTABLE' USING ERRCODE = '55000';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER payroll_items_run_guard BEFORE INSERT ON payroll_items
    FOR EACH ROW EXECUTE FUNCTION payroll_child_guard();
CREATE TRIGGER payroll_credits_run_guard BEFORE INSERT ON payroll_run_credits
    FOR EACH ROW EXECUTE FUNCTION payroll_child_guard();
CREATE FUNCTION payroll_run_credit_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' OR OLD.committed OR NOT NEW.committed OR
       (to_jsonb(NEW) - 'committed') IS DISTINCT FROM (to_jsonb(OLD) - 'committed') THEN
        RAISE EXCEPTION 'APPROVED_RUN_IMMUTABLE' USING ERRCODE = '55000';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM payroll_runs r WHERE (r.tenant_id, r.id) =
        (NEW.tenant_id, NEW.run_id) AND r.status = 'APPROVED') THEN
        RAISE EXCEPTION 'APPROVED_RUN_IMMUTABLE' USING ERRCODE = '55000';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER payroll_run_credits_immutable BEFORE UPDATE OR DELETE ON payroll_run_credits
    FOR EACH ROW EXECUTE FUNCTION payroll_run_credit_update();
CREATE FUNCTION payroll_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM payroll_runs WHERE (tenant_id, id) = (NEW.tenant_id, NEW.run_id)
       AND status = 'APPROVED' FOR UPDATE) THEN
        RAISE EXCEPTION 'PAYROLL_NOT_APPROVED' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER payroll_payment_approved BEFORE INSERT ON payroll_payments
    FOR EACH ROW EXECUTE FUNCTION payroll_payment_guard();

-- Monetary facts and contributing records are append-only, including direct SQL paths.
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['rate_cards','eligibility_events','wage_credits','qc_bonus_accruals',
        'payroll_items','payroll_payments','payroll_adjustments',
        'overhead_events','overhead_periods'] LOOP
        EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION payroll_snapshot_immutable()', t || '_immutable', t);
    END LOOP;
END $$;
CREATE FUNCTION payroll_rule_approval_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.status <> 'PENDING' OR
           current_setting('app.role', true) IS NULL OR
           current_setting('app.role', true) NOT IN ('Owner', 'FinancePayroll') THEN
            RAISE EXCEPTION 'RULE_APPROVAL_FORBIDDEN' USING ERRCODE = '42501';
        END IF;
        RETURN NEW;
    END IF;
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'RULE_APPROVAL_FORBIDDEN' USING ERRCODE = '42501';
    END IF;
    IF OLD.status = 'APPROVED' OR NEW.status <> 'APPROVED' OR
       current_setting('app.role', true) IS DISTINCT FROM 'Owner' OR
       NEW.approved_by::text IS DISTINCT FROM current_setting('app.actor_id', true) OR
       NEW.evidence_file_id IS NULL OR
       (to_jsonb(NEW) - 'status' - 'approved_by' - 'evidence_file_id') IS DISTINCT FROM
       (to_jsonb(OLD) - 'status' - 'approved_by' - 'evidence_file_id') THEN
        RAISE EXCEPTION 'RULE_APPROVAL_FORBIDDEN' USING ERRCODE = '42501';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER financial_rule_approval BEFORE INSERT OR UPDATE OR DELETE ON financial_rule_versions
    FOR EACH ROW EXECUTE FUNCTION payroll_rule_approval_guard();

CREATE FUNCTION sewing_tally_verification_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.status <> 'RECORDED' OR NEW.status <> 'VERIFIED' OR
       current_setting('app.role', true) IS DISTINCT FROM 'ProductionHead' OR
       NEW.verified_by::text IS DISTINCT FROM current_setting('app.actor_id', true) OR
       (to_jsonb(NEW) - 'status' - 'verified_by' - 'verified_at') IS DISTINCT FROM
       (to_jsonb(OLD) - 'status' - 'verified_by' - 'verified_at') THEN
        RAISE EXCEPTION 'TALLY_VERIFICATION_FORBIDDEN' USING ERRCODE = '42501';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER sewing_tally_verification BEFORE UPDATE OR DELETE ON sewing_tallies
    FOR EACH ROW EXECUTE FUNCTION sewing_tally_verification_guard();

CREATE FUNCTION calculate_weekly_payroll(p_period_id uuid, p_rule_version uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_period payroll_periods%ROWTYPE;
    v_tenant uuid;
    v_rule_id uuid;
    v_run_id uuid;
    v_version integer;
BEGIN
    v_tenant := payroll_context_tenant();
    SELECT * INTO v_period FROM payroll_periods WHERE tenant_id = v_tenant
        AND id = p_period_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'PERIOD_NOT_FOUND' USING ERRCODE = '02000'; END IF;
    IF v_period.rule_version <> p_rule_version OR v_period.status IN ('APPROVED','PAID','REVERSED') THEN
        RAISE EXCEPTION 'PERIOD_NOT_CALCULABLE' USING ERRCODE = '23514';
    END IF;
    SELECT id INTO v_rule_id FROM financial_rule_versions
    WHERE tenant_id = v_period.tenant_id AND id = p_rule_version
      AND status = 'APPROVED' AND effective_from <= v_period.period_start
      AND (effective_through IS NULL OR v_period.period_start < effective_through);
    IF v_rule_id IS NULL THEN
        -- An exception rolls back this transaction; phase 4 records PENDING_RULE
        -- in a separate transaction after returning the conflict response.
        RAISE EXCEPTION 'FINANCIAL_RULE_PENDING' USING ERRCODE = '23514';
    END IF;
    -- Capture only eligible first-pass component units; the partial unique index
    -- prevents repeat valuation after repair or concurrent requests.
    INSERT INTO wage_credits (tenant_id, garment_unit_id, operator_id, amount_minor,
        currency, period_id)
    SELECT u.tenant_id, u.id, u.operator_id, s.amount_minor, s.currency, p_period_id
    FROM eligibility_events e
    JOIN assembly_components c ON (c.tenant_id, c.assembly_id) = (e.tenant_id, e.assembly_id)
    JOIN garment_units u ON (u.tenant_id, u.id) = (c.tenant_id, c.garment_unit_id)
    JOIN sewing_tallies t ON (t.tenant_id, t.id) = (u.tenant_id, u.source_tally_id)
    JOIN piece_rate_snapshots s ON (s.tenant_id, s.id) = (u.tenant_id, u.piece_rate_snapshot_id)
        WHERE e.tenant_id = v_period.tenant_id AND (e.passed_at AT TIME ZONE 'Asia/Jakarta')::date >= v_period.period_start
            AND (e.passed_at AT TIME ZONE 'Asia/Jakarta')::date < v_period.period_end AND u.status = 'QC_PASS'
      AND t.status = 'VERIFIED'
    ON CONFLICT (tenant_id, garment_unit_id) WHERE reversal_of IS NULL DO NOTHING;
    -- NULL means a valid zero-output preview. Phase 4 maps it to NO_OUTPUT;
    -- there is no invented SQL/API status field and no monetary row is written.
    IF NOT EXISTS (SELECT 1 FROM wage_credits c WHERE c.tenant_id = v_period.tenant_id
        AND c.period_id = p_period_id AND c.reversal_of IS NULL) THEN
        RETURN NULL;
    END IF;
    SELECT COALESCE(max(version), 0) + 1 INTO v_version FROM payroll_runs
    WHERE tenant_id = v_period.tenant_id AND period_id = p_period_id;
    INSERT INTO payroll_runs (tenant_id, period_id, period_start, period_end, timezone,
        cutoff_local, rule_version_id, status, input_hash, version)
    VALUES (v_period.tenant_id, p_period_id, v_period.period_start, v_period.period_end,
        v_period.timezone, v_period.cutoff_local, v_rule_id, 'CALCULATED',
        decode(md5((SELECT string_agg(c.id::text || ':' || c.amount_minor::text || ':' || c.currency,
            ',' ORDER BY c.id) FROM wage_credits c WHERE c.tenant_id = v_period.tenant_id
            AND c.period_id = p_period_id AND c.reversal_of IS NULL)), 'hex'), v_version)
    RETURNING id INTO v_run_id;
    INSERT INTO payroll_run_credits (tenant_id, run_id, source_tenant_id, wage_credit_id)
    SELECT v_period.tenant_id, v_run_id, c.tenant_id, c.id FROM wage_credits c
    WHERE c.tenant_id = v_period.tenant_id AND c.period_id = p_period_id AND c.reversal_of IS NULL;
    UPDATE payroll_periods SET status = 'CALCULATED', updated_at = now()
    WHERE (tenant_id, id) = (v_period.tenant_id, p_period_id);
    RETURN v_run_id;
END $$;

CREATE FUNCTION calculate_overhead_allocation(p_period_id uuid, p_rule_version uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_period payroll_periods%ROWTYPE;
    v_tenant uuid;
    v_rule_id uuid;
    v_units integer;
    v_total bigint;
    v_currency char(3);
    v_id uuid;
    v_rule_currency text;
BEGIN
    v_tenant := payroll_context_tenant();
    SELECT * INTO v_period FROM payroll_periods WHERE tenant_id = v_tenant
        AND id = p_period_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'PERIOD_NOT_FOUND' USING ERRCODE = '02000'; END IF;
        SELECT id, parameters->>'currency' INTO v_rule_id, v_rule_currency
            FROM financial_rule_versions WHERE tenant_id = v_period.tenant_id
        AND id = p_rule_version AND p_rule_version = v_period.rule_version AND status = 'APPROVED'
        AND effective_from <= v_period.period_start
        AND (effective_through IS NULL OR v_period.period_start < effective_through);
    IF v_rule_id IS NULL THEN RAISE EXCEPTION 'FINANCIAL_RULE_PENDING' USING ERRCODE = '23514'; END IF;
    IF v_rule_currency IS NULL OR v_rule_currency !~ '^[A-Z]{3}$' THEN
        RAISE EXCEPTION 'CURRENCY_MISMATCH' USING ERRCODE = '23514';
    END IF;
    SELECT count(DISTINCT e.assembly_id) INTO v_units FROM eligibility_events e
        WHERE e.tenant_id = v_period.tenant_id AND (e.passed_at AT TIME ZONE 'Asia/Jakarta')::date >= v_period.period_start
        AND (e.passed_at AT TIME ZONE 'Asia/Jakarta')::date < v_period.period_end;
    SELECT COALESCE(sum(amount_minor), 0), min(currency) INTO v_total, v_currency
        FROM overhead_events WHERE tenant_id = v_period.tenant_id
        AND starts_on = v_period.period_start AND ends_on = v_period.period_end;
    IF EXISTS (SELECT 1 FROM overhead_events WHERE tenant_id = v_period.tenant_id
       AND starts_on = v_period.period_start AND ends_on = v_period.period_end
       AND currency <> v_currency) THEN
        RAISE EXCEPTION 'CURRENCY_MISMATCH' USING ERRCODE = '23514';
    END IF;
    IF v_currency IS NOT NULL AND v_currency <> v_rule_currency THEN
        RAISE EXCEPTION 'CURRENCY_MISMATCH' USING ERRCODE = '23514';
    END IF;
    IF v_units = 0 THEN
        -- Do not persist an allocation or an invented division-by-zero result.
        RETURN NULL;
    END IF;
    INSERT INTO overhead_periods (tenant_id, starts_on, ends_on, total_minor,
        produced_units, status, currency, rule_version_id)
    VALUES (v_period.tenant_id, v_period.period_start, v_period.period_end,
        v_total, v_units, CASE WHEN v_units = 0 THEN 'NO_OUTPUT' ELSE 'CALCULATED' END,
        v_rule_currency, v_rule_id) RETURNING id INTO v_id;
    RETURN v_id;
END $$;

REVOKE ALL ON FUNCTION calculate_weekly_payroll(uuid,uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION calculate_overhead_allocation(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION calculate_weekly_payroll(uuid,uuid), calculate_overhead_allocation(uuid,uuid) TO lukla_app;

-- Phase 4 reads use this checked, bounded JSON row API instead of direct table SELECT.
-- The explicit tenant filter also protects calls when the migration owner bypasses RLS.
CREATE FUNCTION payroll_read_rows(p_table text, p_id uuid DEFAULT NULL,
    p_after uuid DEFAULT NULL, p_limit integer DEFAULT 100)
RETURNS SETOF jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_tenant uuid;
BEGIN
    v_tenant := payroll_context_tenant();
    IF p_table IS NULL OR p_table <> ALL (ARRAY[
        'rate_cards','piece_rate_snapshots','sewing_tallies','garment_units',
        'garment_assemblies','assembly_components','qc_inspections','qc_defects',
        'financial_rule_versions','eligibility_events','payroll_periods','payroll_runs',
        'payroll_run_credits','payroll_items','payroll_payments','wage_credits',
        'payroll_adjustments','qc_bonus_accruals','overhead_events','overhead_periods','job_runs'
    ]) OR p_limit IS NULL OR p_limit < 1 OR p_limit > 1000 THEN
        RAISE EXCEPTION 'PAYROLL_READ_INVALID' USING ERRCODE = '22023';
    END IF;
    RETURN QUERY EXECUTE format('SELECT to_jsonb(t) FROM public.%I t
        WHERE t.tenant_id = $1 AND ($2 IS NULL OR t.id = $2)
          AND ($3 IS NULL OR t.id > $3) ORDER BY t.id LIMIT $4', p_table)
        USING v_tenant, p_id, p_after, p_limit;
END $$;
REVOKE ALL ON FUNCTION payroll_read_rows(text,uuid,uuid,integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION payroll_read_rows(text,uuid,uuid,integer) TO lukla_app;

-- The application has no direct period UPDATE or SELECT; lock and compare under
-- the same tenant context while retaining the period/run trigger prerequisites.
CREATE FUNCTION payroll_transition_period(p_period_id uuid, p_expected_status text,
    p_target_status text) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_tenant uuid;
    v_status text;
BEGIN
    v_tenant := payroll_context_tenant();
    IF current_setting('app.role', true) NOT IN
       ('Owner','FinancePayroll','ServicePayrollJob') OR
       current_setting('app.role', true) IS NULL THEN
        RAISE EXCEPTION 'PERIOD_TRANSITION_FORBIDDEN' USING ERRCODE = '42501';
    END IF;
    SELECT status INTO v_status FROM public.payroll_periods
    WHERE tenant_id = v_tenant AND id = p_period_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'PERIOD_NOT_FOUND' USING ERRCODE = '02000'; END IF;
    IF p_expected_status IS NULL OR v_status IS DISTINCT FROM p_expected_status THEN
        RAISE EXCEPTION 'PERIOD_STATUS_STALE' USING ERRCODE = '55000';
    END IF;
    UPDATE public.payroll_periods SET status = p_target_status, updated_at = now()
    WHERE tenant_id = v_tenant AND id = p_period_id;
END $$;
REVOKE ALL ON FUNCTION payroll_transition_period(uuid,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION payroll_transition_period(uuid,text,text) TO lukla_app;

-- Run transitions still go through the existing approval/payment triggers;
-- direct UPDATE needs SELECT privileges, which the app intentionally lacks.
CREATE FUNCTION payroll_advance_run(p_run_id uuid, p_status text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_tenant uuid;
BEGIN
    v_tenant := payroll_context_tenant();
    IF p_status IS NULL OR p_status NOT IN ('APPROVED','PAID') THEN
        RAISE EXCEPTION 'APPROVED_RUN_IMMUTABLE' USING ERRCODE = '55000';
    END IF;
    UPDATE public.payroll_runs SET status = p_status
    WHERE tenant_id = v_tenant AND id = p_run_id;
    IF NOT FOUND THEN RAISE EXCEPTION 'RUN_NOT_FOUND' USING ERRCODE = '02000'; END IF;
END $$;
REVOKE ALL ON FUNCTION payroll_advance_run(uuid,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION payroll_advance_run(uuid,text) TO lukla_app;

-- Rule approval remains an Owner-only trigger transition after raw reads close.
CREATE FUNCTION payroll_approve_rule(p_rule_id uuid, p_evidence_file_id uuid,
    p_approval_reference text, p_note text, p_request_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    v_tenant uuid;
BEGIN
    v_tenant := payroll_context_tenant();
    IF current_setting('app.role', true) IS DISTINCT FROM 'Owner' OR
       p_evidence_file_id IS NULL OR p_request_id IS NULL OR
       length(p_approval_reference) > 200 OR length(p_note) > 500 OR
       p_approval_reference = '' THEN
        RAISE EXCEPTION 'RULE_APPROVAL_FORBIDDEN' USING ERRCODE = '42501';
    END IF;
    UPDATE public.financial_rule_versions
    SET status = 'APPROVED', approved_by = current_setting('app.actor_id')::uuid,
        evidence_file_id = p_evidence_file_id
    WHERE tenant_id = v_tenant AND id = p_rule_id AND status = 'PENDING';
    IF NOT FOUND THEN RAISE EXCEPTION 'RULE_NOT_FOUND' USING ERRCODE = '02000'; END IF;
    INSERT INTO public.audit_events (tenant_id, actor_id, action, entity_type,
        entity_id, request_id, payload)
    VALUES (v_tenant, current_setting('app.actor_id')::uuid, 'APPROVED',
        'financial_rule_versions', p_rule_id, p_request_id,
        jsonb_build_object('evidenceFileId', p_evidence_file_id,
          'approvalReference', p_approval_reference, 'note', p_note));
END $$;
REVOKE ALL ON FUNCTION payroll_approve_rule(uuid,uuid,text,text,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION payroll_approve_rule(uuid,uuid,text,text,uuid) TO lukla_app;

-- FORCE RLS applies even to the table owner. The pool role is non-owner/NOBYPASSRLS.
-- Upstream ledger/identity policies remain owned by their migrations.
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['rate_cards','piece_rate_snapshots','sewing_tallies','garment_units',
      'garment_assemblies','assembly_components','qc_inspections','qc_defects',
      'financial_rule_versions','eligibility_events','payroll_periods','payroll_runs',
      'payroll_run_credits','payroll_items','payroll_payments','wage_credits',
      'payroll_adjustments','qc_bonus_accruals','overhead_events','overhead_periods','job_runs'] LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
        EXECUTE format('DROP POLICY IF EXISTS payroll_tenant ON %I', t);
        EXECUTE format('CREATE POLICY payroll_tenant ON %I FOR ALL TO PUBLIC USING (tenant_id = payroll_context_tenant()) WITH CHECK (tenant_id = payroll_context_tenant())', t);
        EXECUTE format('GRANT INSERT ON %I TO lukla_app', t);
        EXECUTE format('REVOKE SELECT ON %I FROM lukla_app', t);
    END LOOP;
END $$;
-- The app cannot read raw payroll/QC tables or insert a run/link; only the
-- checked reader and owner-executed calculator expose these capabilities.
REVOKE INSERT ON payroll_runs, payroll_run_credits FROM lukla_app;
-- public is trusted only while untrusted roles cannot create objects there.
REVOKE CREATE ON SCHEMA public FROM PUBLIC, lukla_app;
-- Existing triggers consult other protected tables; execute their internal
-- checks as the migration owner, with a fixed trusted search path.
DO $$
DECLARE f text;
BEGIN
    FOREACH f IN ARRAY ARRAY[
        'check_snapshot_source_unit','check_assembly_component',
        'guard_assembly_component_delete','enforce_qc_transition',
        'payroll_record_eligibility','payroll_monetary_guard',
        'payroll_period_transition','payroll_run_transition',
        'payroll_commit_run_credits','payroll_child_guard',
        'payroll_run_credit_update','payroll_payment_guard',
        'payroll_rule_approval_guard','sewing_tally_verification_guard'
    ] LOOP
        EXECUTE format('ALTER FUNCTION public.%I() SECURITY DEFINER SET search_path = pg_catalog, public, pg_temp', f);
    END LOOP;
END $$;
REVOKE UPDATE ON payroll_periods FROM lukla_app;
GRANT UPDATE ON job_runs TO lukla_app;
-- M007's QC transition updates assembly/unit status under the application role.
GRANT UPDATE (status) ON garment_assemblies TO lukla_app;
GRANT UPDATE (status, updated_at) ON garment_units TO lukla_app;
GRANT UPDATE (status, verified_by, verified_at) ON sewing_tallies TO lukla_app;
REVOKE UPDATE, DELETE ON wage_credits, qc_bonus_accruals, payroll_items, payroll_payments,
    payroll_adjustments, overhead_events, overhead_periods FROM lukla_app;
