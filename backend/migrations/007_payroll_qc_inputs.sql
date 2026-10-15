-- M006 owns garment units and tallies. Upstream orders have no migrated owner yet.
CREATE TABLE garment_assemblies (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    order_id uuid NOT NULL,
    serial_code text NOT NULL,
    status text NOT NULL DEFAULT 'MENUNGGU_QC'
        CHECK (status IN ('ASSEMBLING','MENUNGGU_QC','QC_PASS','REWORK','REJECT_SCRAP')),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, serial_code),
    UNIQUE (tenant_id, id, order_id)
);
CREATE INDEX garment_assemblies_order ON garment_assemblies (tenant_id, order_id);

CREATE TABLE assembly_components (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    assembly_id uuid NOT NULL,
    garment_unit_id uuid NOT NULL,
    order_id uuid NOT NULL,
    component_code text NOT NULL,
    allocated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, garment_unit_id),
    UNIQUE (tenant_id, assembly_id, garment_unit_id),
    FOREIGN KEY (tenant_id, assembly_id, order_id)
        REFERENCES garment_assemblies(tenant_id, id, order_id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, garment_unit_id) REFERENCES garment_units(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX assembly_components_assembly ON assembly_components (tenant_id, assembly_id);

CREATE FUNCTION check_assembly_component() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM garment_assemblies a WHERE a.tenant_id = NEW.tenant_id
        AND a.id = NEW.assembly_id AND a.status IN ('ASSEMBLING','MENUNGGU_QC') FOR UPDATE) THEN
        RAISE EXCEPTION 'ASSEMBLY_FINAL' USING ERRCODE = '23514';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM garment_units u WHERE u.tenant_id = NEW.tenant_id
        AND u.id = NEW.garment_unit_id AND u.order_id = NEW.order_id
        AND u.component_code = NEW.component_code
    ) THEN
        RAISE EXCEPTION 'ASSEMBLY_COMPONENT_MISMATCH' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER assembly_component_match BEFORE INSERT OR UPDATE ON assembly_components
    FOR EACH ROW EXECUTE FUNCTION check_assembly_component();
CREATE FUNCTION guard_assembly_component_delete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM garment_assemblies a WHERE a.tenant_id = OLD.tenant_id
        AND a.id = OLD.assembly_id AND a.status IN ('ASSEMBLING','MENUNGGU_QC') FOR UPDATE) THEN
        RAISE EXCEPTION 'ASSEMBLY_FINAL' USING ERRCODE = '23514';
    END IF;
    RETURN OLD;
END $$;
CREATE TRIGGER assembly_component_delete BEFORE DELETE ON assembly_components
    FOR EACH ROW EXECUTE FUNCTION guard_assembly_component_delete();

CREATE TABLE qc_inspections (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    assembly_id uuid NOT NULL,
    inspector_id uuid NOT NULL REFERENCES actors(id) ON DELETE RESTRICT,
    disposition text NOT NULL CHECK (disposition IN ('PASS','REPAIR','REJECT')),
    sequence_no integer NOT NULL CHECK (sequence_no > 0),
    idempotency_key text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, assembly_id, sequence_no),
    UNIQUE (tenant_id, idempotency_key),
    UNIQUE (tenant_id, id, assembly_id),
    FOREIGN KEY (tenant_id, assembly_id) REFERENCES garment_assemblies(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX qc_inspections_assembly ON qc_inspections (tenant_id, assembly_id);
CREATE INDEX qc_inspections_inspector ON qc_inspections (inspector_id);

CREATE FUNCTION enforce_qc_transition() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_status text;
    v_sequence integer;
BEGIN
    SELECT status INTO v_status FROM garment_assemblies
    WHERE tenant_id = NEW.tenant_id AND id = NEW.assembly_id FOR UPDATE;
    IF v_status NOT IN ('MENUNGGU_QC','REWORK') THEN
        RAISE EXCEPTION 'QC_FINAL_OR_NOT_READY' USING ERRCODE = '23514';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM assembly_components c
        WHERE c.tenant_id = NEW.tenant_id AND c.assembly_id = NEW.assembly_id) THEN
        RAISE EXCEPTION 'QC_EMPTY_ASSEMBLY' USING ERRCODE = '23514';
    END IF;
    SELECT COALESCE(max(sequence_no), 0) + 1 INTO v_sequence FROM qc_inspections
    WHERE tenant_id = NEW.tenant_id AND assembly_id = NEW.assembly_id;
    IF NEW.sequence_no <> v_sequence THEN
        RAISE EXCEPTION 'QC_SEQUENCE_INVALID' USING ERRCODE = '23514';
    END IF;
    UPDATE garment_assemblies SET status = CASE NEW.disposition
        WHEN 'PASS' THEN 'QC_PASS' WHEN 'REPAIR' THEN 'REWORK' ELSE 'REJECT_SCRAP' END
    WHERE tenant_id = NEW.tenant_id AND id = NEW.assembly_id;
    UPDATE garment_units u SET status = CASE NEW.disposition
        WHEN 'PASS' THEN 'QC_PASS' WHEN 'REPAIR' THEN 'REWORK' ELSE 'REJECT_SCRAP' END,
        updated_at = now()
    FROM assembly_components c WHERE c.tenant_id = NEW.tenant_id
        AND c.assembly_id = NEW.assembly_id AND (u.tenant_id, u.id) = (c.tenant_id, c.garment_unit_id);
    RETURN NEW;
END $$;
CREATE TRIGGER qc_transition BEFORE INSERT ON qc_inspections
    FOR EACH ROW EXECUTE FUNCTION enforce_qc_transition();
CREATE TRIGGER qc_inspections_immutable BEFORE UPDATE OR DELETE ON qc_inspections
    FOR EACH ROW EXECUTE FUNCTION payroll_snapshot_immutable();

CREATE TABLE qc_defects (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    inspection_id uuid NOT NULL,
    assembly_id uuid NOT NULL,
    garment_unit_id uuid NOT NULL,
    defect_code text NOT NULL,
    notes text,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, inspection_id, assembly_id)
        REFERENCES qc_inspections(tenant_id, id, assembly_id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, assembly_id, garment_unit_id)
        REFERENCES assembly_components(tenant_id, assembly_id, garment_unit_id) ON DELETE RESTRICT
);
CREATE INDEX qc_defects_inspection ON qc_defects (tenant_id, inspection_id);
CREATE INDEX qc_defects_component ON qc_defects (tenant_id, garment_unit_id);
CREATE TRIGGER qc_defects_immutable BEFORE UPDATE OR DELETE ON qc_defects
    FOR EACH ROW EXECUTE FUNCTION payroll_snapshot_immutable();
