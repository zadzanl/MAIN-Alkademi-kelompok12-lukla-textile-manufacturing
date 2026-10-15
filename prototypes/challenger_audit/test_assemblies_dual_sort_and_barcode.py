import sqlite3
import uuid
import time

def run_assemblies_audit():
    print("=================================================================")
    print("EMPIRICAL TEST 4: ASSEMBLIES DUAL SORT & FUNCTIONAL INDEX AUDIT")
    print("=================================================================\n")

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE garment_assemblies (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        serial_code TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')

    # Functional unique index for normalized serial code
    c.execute('''
    CREATE UNIQUE INDEX uq_garment_assemblies_norm_serial 
      ON garment_assemblies (tenant_id, UPPER(TRIM(serial_code)))
    ''')

    # Dual Sort Indexes
    c.execute('''
    CREATE INDEX idx_garment_assemblies_recent 
      ON garment_assemblies (tenant_id, status, created_at DESC, id DESC)
    ''')
    c.execute('''
    CREATE INDEX idx_garment_assemblies_qc_queue 
      ON garment_assemblies (tenant_id, status, created_at ASC, id ASC)
    ''')

    tenant_id = 't1'

    # 1. Barcode normalization & uniqueness test
    print("--- 4.1: Barcode Normalization & Uniqueness Guard ---")
    c.execute("INSERT INTO garment_assemblies VALUES (?, ?, 'ord-1', 'ASMB-0001', 'COMPLETED', '2026-10-15T08:00:00.000000Z')",
              (str(uuid.uuid4()), tenant_id))
    conn.commit()

    # Attempt inserting case variation or dirty whitespace variation
    duplicate_trapped = False
    try:
        c.execute("INSERT INTO garment_assemblies VALUES (?, ?, 'ord-1', '  asmb-0001  ', 'COMPLETED', '2026-10-15T08:05:00.000000Z')",
                  (str(uuid.uuid4()), tenant_id))
        conn.commit()
    except sqlite3.IntegrityError as e:
        duplicate_trapped = True
        print(f"  [Pass] Trapped duplicate dirty scanner input via unique functional index: {e}")

    assert duplicate_trapped, "FAILED: Duplicate scanner variation was not trapped by functional unique index!"

    # 2. Execution plan for normalized barcode lookup
    print("\n--- 4.2: Normalized Barcode Lookup Execution Plan ---")
    plan = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM garment_assemblies
    WHERE tenant_id = ? AND UPPER(TRIM(serial_code)) = UPPER(TRIM(?))
    ''', (tenant_id, "  asmb-0001 \r\n")).fetchall()
    print("  Plan:", plan)
    uses_func_index = any('uq_garment_assemblies_norm_serial' in str(p) for p in plan)
    print(f"  Uses functional unique index? {uses_func_index}")
    assert uses_func_index, "FAILED: Barcode lookup did not use uq_garment_assemblies_norm_serial index!"

    # 3. Execution plan for Dual Sorting
    print("\n--- 4.3: Dual Sorting Execution Plans ---")
    # Plan A: Recent discovery (DESC)
    plan_desc = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM garment_assemblies
    WHERE tenant_id = ? AND status = 'COMPLETED'
    ORDER BY created_at DESC, id DESC
    LIMIT 20
    ''', (tenant_id,)).fetchall()
    print("  Recent (DESC) Plan:", plan_desc)
    has_temp_desc = any('TEMP B-TREE' in str(p) for p in plan_desc)
    uses_index_desc = any('INDEX' in str(p) for p in plan_desc)
    print(f"  DESC uses B-tree index without temp sort? {uses_index_desc and not has_temp_desc}")
    assert uses_index_desc and not has_temp_desc, "FAILED: Recent DESC sort used temp b-tree!"

    # Plan B: FIFO QC Queue (ASC)
    plan_asc = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM garment_assemblies
    WHERE tenant_id = ? AND status = 'MENUNGGU_QC'
    ORDER BY created_at ASC, id ASC
    LIMIT 20
    ''', (tenant_id,)).fetchall()
    print("  QC Queue (ASC) Plan:", plan_asc)
    has_temp_asc = any('TEMP B-TREE' in str(p) for p in plan_asc)
    uses_index_asc = any('INDEX' in str(p) for p in plan_asc)
    print(f"  ASC uses B-tree index without temp sort? {uses_index_asc and not has_temp_asc}")
    assert uses_index_asc and not has_temp_asc, "FAILED: QC Queue ASC sort used temp b-tree!"

    print("\n=================================================================")
    print(">>> CONCLUSION FOR TEST 4: Barcode functional index and Dual Sort indexes operate optimally with 0 temp sorts.")
    print("=================================================================")
    return True

if __name__ == '__main__':
    run_assemblies_audit()
