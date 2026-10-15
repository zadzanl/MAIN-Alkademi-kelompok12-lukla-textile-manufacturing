-- Requires M001. This phase owns sewing_tallies until the production module is migrated.
-- Apply each migration in a single transaction; retry a failed migration after rollback.
-- Upgrade path: add composite order/cut-batch/operator FKs when their owners ship.
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE rate_cards (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    order_beneficiary_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    article_code text NOT NULL,
    component_code text NOT NULL,
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL,
    rule_version text NOT NULL,
    effective_from timestamptz NOT NULL,
    effective_through timestamptz,
    locked_at timestamptz,
    PRIMARY KEY (tenant_id, id),
    CHECK (effective_through IS NULL OR effective_from < effective_through),
    CONSTRAINT rate_cards_no_overlap EXCLUDE USING gist (
        tenant_id WITH =, order_beneficiary_id WITH =,
        article_code WITH =, component_code WITH =,
        tstzrange(effective_from, effective_through, '[)') WITH &&
    )
);
CREATE INDEX rate_cards_lookup ON rate_cards (tenant_id, order_beneficiary_id, article_code, component_code);

CREATE TABLE piece_rate_snapshots (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    rate_card_id uuid NOT NULL,
    amount_minor bigint NOT NULL CHECK (amount_minor >= 0),
    currency char(3) NOT NULL,
    rule_version text NOT NULL,
    captured_at timestamptz NOT NULL DEFAULT now(),
    source_unit_id uuid,
    PRIMARY KEY (tenant_id, id),
    FOREIGN KEY (tenant_id, rate_card_id) REFERENCES rate_cards(tenant_id, id) ON DELETE RESTRICT,
    UNIQUE (tenant_id, source_unit_id)
);
CREATE INDEX piece_rate_snapshots_rate ON piece_rate_snapshots (tenant_id, rate_card_id);

CREATE TABLE sewing_tallies (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    order_id uuid NOT NULL,
    component_code text NOT NULL,
    operator_id uuid NOT NULL,
    quantity integer NOT NULL CHECK (quantity > 0),
    status text NOT NULL CHECK (status IN ('RECORDED','VERIFIED')),
    verified_by uuid REFERENCES actors(id) ON DELETE RESTRICT,
    verified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, id, operator_id, order_id, component_code),
    CHECK ((status = 'VERIFIED') = (verified_by IS NOT NULL AND verified_at IS NOT NULL))
);
CREATE INDEX sewing_tallies_order ON sewing_tallies (tenant_id, order_id);
CREATE INDEX sewing_tallies_operator ON sewing_tallies (tenant_id, operator_id);

CREATE TABLE garment_units (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    order_id uuid NOT NULL,
    component_code text NOT NULL,
    source_tally_id uuid NOT NULL,
    operator_id uuid NOT NULL,
    status text NOT NULL DEFAULT 'MENUNGGU_QC'
        CHECK (status IN ('MENUNGGU_QC','QC_PASS','REWORK','REJECT_SCRAP','ASSEMBLED')),
    piece_rate_snapshot_id uuid NOT NULL,
    wage_credited_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    UNIQUE (tenant_id, piece_rate_snapshot_id),
    FOREIGN KEY (tenant_id, source_tally_id, operator_id, order_id, component_code)
        REFERENCES sewing_tallies(tenant_id, id, operator_id, order_id, component_code) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, piece_rate_snapshot_id)
        REFERENCES piece_rate_snapshots(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX garment_units_tally ON garment_units (tenant_id, source_tally_id);
CREATE INDEX garment_units_order ON garment_units (tenant_id, order_id);
CREATE INDEX garment_units_operator ON garment_units (tenant_id, operator_id);
ALTER TABLE piece_rate_snapshots ADD CONSTRAINT snapshot_source_unit
    FOREIGN KEY (tenant_id, source_unit_id) REFERENCES garment_units(tenant_id, id) ON DELETE RESTRICT;

-- The unit's NOT NULL snapshot FK and UNIQUE snapshot ID are the authoritative
-- one-to-one link. A nullable reverse source link must never disagree with it.
CREATE FUNCTION check_snapshot_source_unit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.source_unit_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM garment_units u WHERE (u.tenant_id, u.id, u.piece_rate_snapshot_id)
            = (NEW.tenant_id, NEW.source_unit_id, NEW.id)
    ) THEN
        RAISE EXCEPTION 'SNAPSHOT_UNIT_MISMATCH' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;
CREATE CONSTRAINT TRIGGER snapshot_source_matches_unit
    AFTER INSERT ON piece_rate_snapshots DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_snapshot_source_unit();

-- A snapshot cannot be edited after capture. Correct rates with a new card and new snapshot.
CREATE FUNCTION payroll_snapshot_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'SNAPSHOT_IMMUTABLE' USING ERRCODE = '55000';
END $$;
CREATE TRIGGER snapshot_immutable BEFORE UPDATE OR DELETE ON piece_rate_snapshots
    FOR EACH ROW EXECUTE FUNCTION payroll_snapshot_immutable();
