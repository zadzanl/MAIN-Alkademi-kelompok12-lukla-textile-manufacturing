-- Migration 007: Assemblies, Component Allocations, and Quality Inspections (MOD-04)
--
-- Prerequisites, all applied earlier in the frozen sequence (11-database-schema-spec.md):
--   M001 identities -> tenants, actors, set_request_context
--   M004 orders     -> orders
--   M006 shop floor -> garment_units
-- M004 and M006 are owned by the warehouse and shop-floor modules and are not authored here.
-- The composite foreign keys below rely on the schema spec's composite-key rule: every
-- referenced table carries PRIMARY KEY (tenant_id, id), which is what rejects a cross-tenant
-- reference at the relational layer.
--
-- What this migration owns: the inspection log, the assembly status machine, the component
-- allocation uniqueness, and the append-only guarantees. What it does not own: the bonus
-- accrual, eligibility event, and wage credit rows a first pass produces -- those tables are
-- the payroll migration M009, and the routine that writes them lands with it.

-- ---------------------------------------------------------------------------
-- Assemblies
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS garment_assemblies (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    order_id uuid NOT NULL,
    serial_code text NOT NULL,
    status text NOT NULL DEFAULT 'ASSEMBLING'
        CHECK (status IN ('ASSEMBLING', 'MENUNGGU_QC', 'QC_PASS', 'REWORK', 'REJECT_SCRAP')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT uq_garment_assemblies_serial UNIQUE (tenant_id, serial_code),
    CONSTRAINT fk_garment_assemblies_order FOREIGN KEY (tenant_id, order_id)
        REFERENCES orders (tenant_id, id) ON DELETE RESTRICT
);

-- The QC queue reads one tenant's assemblies by status, newest first.
CREATE INDEX IF NOT EXISTS idx_garment_assemblies_queue
ON garment_assemblies (tenant_id, status, created_at DESC, id);

-- ---------------------------------------------------------------------------
-- Component allocations
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS assembly_components (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    assembly_id uuid NOT NULL,
    garment_unit_id uuid NOT NULL,
    component_code text NOT NULL,
    allocated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT fk_assembly_components_assembly FOREIGN KEY (tenant_id, assembly_id)
        REFERENCES garment_assemblies (tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_assembly_components_unit FOREIGN KEY (tenant_id, garment_unit_id)
        REFERENCES garment_units (tenant_id, id) ON DELETE RESTRICT,
    -- One component piece belongs to exactly one assembly, ever. This is what stops two
    -- assemblies from claiming the same piece and therefore two wage credits for it.
    CONSTRAINT uq_assembly_components_unit UNIQUE (tenant_id, garment_unit_id)
);

CREATE INDEX IF NOT EXISTS idx_assembly_components_assembly
ON assembly_components (tenant_id, assembly_id);

-- ---------------------------------------------------------------------------
-- Quality inspections (append-only)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS qc_inspections (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    assembly_id uuid NOT NULL,
    inspector_id uuid NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    disposition text NOT NULL CHECK (disposition IN ('PASS', 'REPAIR', 'REJECT')),
    sequence_no integer NOT NULL CHECK (sequence_no > 0),
    idempotency_key text NOT NULL CHECK (length(btrim(idempotency_key)) > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT fk_qc_inspections_assembly FOREIGN KEY (tenant_id, assembly_id)
        REFERENCES garment_assemblies (tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT uq_qc_inspections_sequence UNIQUE (tenant_id, assembly_id, sequence_no)
);

CREATE INDEX IF NOT EXISTS idx_qc_inspections_assembly
ON qc_inspections (tenant_id, assembly_id, sequence_no);

CREATE TABLE IF NOT EXISTS qc_defects (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    inspection_id uuid NOT NULL,
    garment_unit_id uuid NOT NULL,
    defect_code text NOT NULL CHECK (length(btrim(defect_code)) > 0),
    notes text NULL,
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT fk_qc_defects_inspection FOREIGN KEY (tenant_id, inspection_id)
        REFERENCES qc_inspections (tenant_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_qc_defects_unit FOREIGN KEY (tenant_id, garment_unit_id)
        REFERENCES garment_units (tenant_id, id) ON DELETE RESTRICT,
    -- A piece carries at most one defect in one inspection.
    CONSTRAINT uq_qc_defects_piece UNIQUE (tenant_id, inspection_id, garment_unit_id)
);

CREATE INDEX IF NOT EXISTS idx_qc_defects_inspection
ON qc_defects (tenant_id, inspection_id);

-- ---------------------------------------------------------------------------
-- Inspection insert: serialize on the assembly, assign the sequence, refuse a
-- state the disposition cannot leave.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION trg_fn_qc_inspection_prepare()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_status text;
BEGIN
    -- Row lock on the assembly: concurrent inspections of one assembly are serialized
    -- here, which is also what makes the sequence assignment below race-free.
    SELECT status INTO v_status
    FROM garment_assemblies
    WHERE tenant_id = NEW.tenant_id AND id = NEW.assembly_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'QC_ASSEMBLY_NOT_FOUND'
        USING ERRCODE = '02000',
        DETAIL = 'The assembly does not exist in this tenant';
    END IF;

    IF v_status = 'ASSEMBLING' THEN
        RAISE EXCEPTION 'QC_ASSEMBLY_NOT_READY'
        USING ERRCODE = '55000',
        DETAIL = 'An assembly that is still assembling cannot be inspected';
    END IF;

    IF v_status IN ('QC_PASS', 'REJECT_SCRAP') THEN
        RAISE EXCEPTION 'QC_DISPOSITION_TERMINAL'
        USING ERRCODE = '55000',
        DETAIL = 'A final pass or reject cannot be overridden in this release';
    END IF;

    IF NEW.sequence_no IS NULL THEN
        SELECT COALESCE(MAX(sequence_no), 0) + 1 INTO NEW.sequence_no
        FROM qc_inspections
        WHERE tenant_id = NEW.tenant_id AND assembly_id = NEW.assembly_id;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_qc_inspections_prepare ON qc_inspections;
CREATE TRIGGER trg_qc_inspections_prepare
BEFORE INSERT ON qc_inspections
FOR EACH ROW
EXECUTE FUNCTION trg_fn_qc_inspection_prepare();

-- ---------------------------------------------------------------------------
-- Inspection insert: move the assembly and its pieces to the disposition's state.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION trg_fn_qc_apply_disposition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_status text;
BEGIN
    v_status := CASE NEW.disposition
        WHEN 'PASS' THEN 'QC_PASS'
        WHEN 'REPAIR' THEN 'REWORK'
        ELSE 'REJECT_SCRAP'
    END;

    UPDATE garment_assemblies
    SET status = v_status, updated_at = now()
    WHERE tenant_id = NEW.tenant_id AND id = NEW.assembly_id;

    -- The pieces follow the assembly, because the payroll engine reads eligible output as
    -- garment_units in QC_PASS. A rejected piece earns nothing and is never deducted (OQ-7).
    UPDATE garment_units
    SET status = v_status, updated_at = now()
    WHERE tenant_id = NEW.tenant_id
      AND id IN (
          SELECT garment_unit_id
          FROM assembly_components
          WHERE tenant_id = NEW.tenant_id AND assembly_id = NEW.assembly_id
      );

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_qc_inspections_apply_disposition ON qc_inspections;
CREATE TRIGGER trg_qc_inspections_apply_disposition
AFTER INSERT ON qc_inspections
FOR EACH ROW
EXECUTE FUNCTION trg_fn_qc_apply_disposition();

-- ---------------------------------------------------------------------------
-- Append-only inspection log
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION trg_fn_prevent_qc_modification()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'QC_INSPECTION_IMMUTABLE'
    USING ERRCODE = '55000',
    DETAIL = 'Direct update or delete on quality inspections and defects is prohibited';
END;
$$;

DROP TRIGGER IF EXISTS trg_qc_inspections_immutable ON qc_inspections;
CREATE TRIGGER trg_qc_inspections_immutable
BEFORE UPDATE OR DELETE ON qc_inspections
FOR EACH ROW
EXECUTE FUNCTION trg_fn_prevent_qc_modification();

DROP TRIGGER IF EXISTS trg_qc_defects_immutable ON qc_defects;
CREATE TRIGGER trg_qc_defects_immutable
BEFORE UPDATE OR DELETE ON qc_defects
FOR EACH ROW
EXECUTE FUNCTION trg_fn_prevent_qc_modification();

-- ---------------------------------------------------------------------------
-- A defect names a piece of the inspected assembly, never a piece of another one.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION trg_fn_qc_defect_verify_piece()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_assembly_id uuid;
    v_allocated boolean;
BEGIN
    SELECT assembly_id INTO v_assembly_id
    FROM qc_inspections
    WHERE tenant_id = NEW.tenant_id AND id = NEW.inspection_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'QC_INSPECTION_NOT_FOUND'
        USING ERRCODE = '02000',
        DETAIL = 'The inspection does not exist in this tenant';
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM assembly_components
        WHERE tenant_id = NEW.tenant_id
          AND assembly_id = v_assembly_id
          AND garment_unit_id = NEW.garment_unit_id
    ) INTO v_allocated;

    IF NOT v_allocated THEN
        RAISE EXCEPTION 'QC_DEFECT_FOREIGN_COMPONENT'
        USING ERRCODE = '23514',
        DETAIL = 'The defect names a component piece that is not allocated to this assembly';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_qc_defects_verify_piece ON qc_defects;
CREATE TRIGGER trg_qc_defects_verify_piece
BEFORE INSERT ON qc_defects
FOR EACH ROW
EXECUTE FUNCTION trg_fn_qc_defect_verify_piece();

-- ---------------------------------------------------------------------------
-- A repair or a reject must name a defect; a pass must not. Evaluated at COMMIT,
-- because the defect rows follow the inspection row in the same transaction.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION trg_fn_verify_qc_defects()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_defect_count int;
BEGIN
    SELECT COUNT(*) INTO v_defect_count
    FROM qc_defects
    WHERE tenant_id = NEW.tenant_id AND inspection_id = NEW.id;

    IF NEW.disposition = 'PASS' AND v_defect_count > 0 THEN
        RAISE EXCEPTION 'QC_DEFECT_NOT_ALLOWED'
        USING ERRCODE = '23514',
        DETAIL = 'A pass disposition must not carry a defect category';
    END IF;

    IF NEW.disposition IN ('REPAIR', 'REJECT') AND v_defect_count = 0 THEN
        RAISE EXCEPTION 'QC_DEFECT_REQUIRED'
        USING ERRCODE = '23514',
        DETAIL = 'A repair or reject disposition must select a defect category';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_qc_inspections_defect_rules ON qc_inspections;
CREATE CONSTRAINT TRIGGER trg_qc_inspections_defect_rules
AFTER INSERT ON qc_inspections
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION trg_fn_verify_qc_defects();

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

ALTER TABLE garment_assemblies ENABLE ROW LEVEL SECURITY;
ALTER TABLE garment_assemblies FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON garment_assemblies;
CREATE POLICY tenant_isolation_policy ON garment_assemblies
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE assembly_components ENABLE ROW LEVEL SECURITY;
ALTER TABLE assembly_components FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON assembly_components;
CREATE POLICY tenant_isolation_policy ON assembly_components
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE qc_inspections ENABLE ROW LEVEL SECURITY;
ALTER TABLE qc_inspections FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON qc_inspections;
CREATE POLICY tenant_isolation_policy ON qc_inspections
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE qc_defects ENABLE ROW LEVEL SECURITY;
ALTER TABLE qc_defects FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_policy ON qc_defects;
CREATE POLICY tenant_isolation_policy ON qc_defects
    FOR ALL
    TO PUBLIC
    USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

-- ---------------------------------------------------------------------------
-- Permissions for the runtime role
-- ---------------------------------------------------------------------------

GRANT SELECT, INSERT ON garment_assemblies TO lukla_app;
GRANT SELECT, INSERT ON assembly_components TO lukla_app;
GRANT SELECT, INSERT ON qc_inspections TO lukla_app;
GRANT SELECT, INSERT ON qc_defects TO lukla_app;

-- The disposition trigger moves the assembly and its pieces; the runtime role therefore
-- needs exactly those two columns, not a general UPDATE on the shop-floor tables.
GRANT UPDATE (status, updated_at) ON garment_assemblies TO lukla_app;
GRANT SELECT, UPDATE (status, updated_at) ON garment_units TO lukla_app;

-- The inspection log is append-only: the runtime role cannot rewrite a recorded decision.
REVOKE UPDATE, DELETE ON qc_inspections FROM lukla_app;
REVOKE UPDATE, DELETE ON qc_defects FROM lukla_app;
