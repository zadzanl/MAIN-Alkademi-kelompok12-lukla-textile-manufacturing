import sqlite3
import uuid

def run_indexing_tests():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    print("=================================================================")
    print("EMPIRICAL INDEXING & TABLE SCAN AUDIT")
    print("=================================================================\n")

    # 1. cut_batches table
    c.execute('''
    CREATE TABLE cut_batches (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        component_code TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    # Proposed index from pre-implementation-hardening.md:148
    c.execute('''
    CREATE INDEX idx_cut_batches_order_component 
      ON cut_batches (tenant_id, order_id, component_code, created_at DESC, id DESC)
    ''')

    print("--- 1. cut_batches: GET /cut-batches?componentCode=COLLAR (omitting orderId) ---")
    plan = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM cut_batches
    WHERE tenant_id = 't1' AND component_code = 'COLLAR'
    ORDER BY created_at DESC, id DESC
    LIMIT 20
    ''').fetchall()
    print("PLAN:", plan)
    has_scan = any('SCAN' in str(p) or 'TEMP B-TREE' in str(p) for p in plan)
    print("VULNERABILITY: Full Table Scan or Temp B-tree?", has_scan)

    print("\n--- 2. cut_batches: GET /cut-batches (unfiltered) ---")
    plan = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM cut_batches
    WHERE tenant_id = 't1'
    ORDER BY created_at DESC, id DESC
    LIMIT 20
    ''').fetchall()
    print("PLAN:", plan)
    has_scan = any('SCAN' in str(p) or 'TEMP B-TREE' in str(p) for p in plan)
    print("VULNERABILITY: Full Table Scan or Temp B-tree?", has_scan)

    # 2. supplier_invoices table
    c.execute('''
    CREATE TABLE supplier_invoices (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        purchase_order_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    # Proposed index from pre-implementation-hardening.md:185
    c.execute('''
    CREATE INDEX idx_supplier_invoices_po_cursor 
      ON supplier_invoices (tenant_id, purchase_order_id, created_at DESC, id DESC)
    ''')

    print("\n--- 3. supplier_invoices: GET /supplier-invoices (omitting purchaseOrderId) ---")
    plan = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM supplier_invoices
    WHERE tenant_id = 't1'
    ORDER BY created_at DESC, id DESC
    LIMIT 20
    ''').fetchall()
    print("PLAN:", plan)
    has_scan = any('SCAN' in str(p) or 'TEMP B-TREE' in str(p) for p in plan)
    print("VULNERABILITY: Full Table Scan or Temp B-tree?", has_scan)

    # 3. purchase_orders table
    c.execute('''
    CREATE TABLE purchase_orders (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    # Proposed index from pre-implementation-hardening.md:181
    c.execute('''
    CREATE INDEX idx_purchase_orders_tenant_status 
      ON purchase_orders (tenant_id, status, created_at DESC, id DESC)
    ''')

    print("\n--- 4. purchase_orders: GET /purchase-orders (omitting status) ---")
    plan = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM purchase_orders
    WHERE tenant_id = 't1'
    ORDER BY created_at DESC, id DESC
    LIMIT 20
    ''').fetchall()
    print("PLAN:", plan)
    has_scan = any('SCAN' in str(p) or 'TEMP B-TREE' in str(p) for p in plan)
    print("VULNERABILITY: Full Table Scan or Temp B-tree?", has_scan)

    # 4. sewing_tallies table
    c.execute('''
    CREATE TABLE sewing_tallies (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        line_id TEXT NOT NULL,
        operator_id TEXT NOT NULL,
        order_id TEXT NOT NULL,
        status TEXT NOT NULL,
        interval_start TEXT NOT NULL
    )
    ''')
    # Proposed indexes from pre-implementation-hardening.md:153-164
    c.execute('''
    CREATE INDEX idx_sewing_tallies_mandor_queue 
      ON sewing_tallies (tenant_id, line_id, status, interval_start DESC, id DESC)
    ''')
    c.execute('''
    CREATE INDEX idx_sewing_tallies_order_operator 
      ON sewing_tallies (tenant_id, order_id, operator_id, interval_start DESC, id DESC)
    ''')

    print("\n--- 5. sewing_tallies: GET /sewing-tallies?operatorId=op1 (omitting orderId and lineId) ---")
    plan = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM sewing_tallies
    WHERE tenant_id = 't1' AND operator_id = 'op1'
    ORDER BY interval_start DESC, id DESC
    LIMIT 20
    ''').fetchall()
    print("PLAN:", plan)
    has_scan = any('SCAN' in str(p) or 'TEMP B-TREE' in str(p) for p in plan)
    print("VULNERABILITY: Full Table Scan or Temp B-tree?", has_scan)

    print("\n--- 6. sewing_tallies: GET /sewing-tallies?status=RECORDED (omitting lineId) ---")
    plan = c.execute('''
    EXPLAIN QUERY PLAN
    SELECT * FROM sewing_tallies
    WHERE tenant_id = 't1' AND status = 'RECORDED'
    ORDER BY interval_start DESC, id DESC
    LIMIT 20
    ''').fetchall()
    print("PLAN:", plan)
    has_scan = any('SCAN' in str(p) or 'TEMP B-TREE' in str(p) for p in plan)
    print("VULNERABILITY: Full Table Scan or Temp B-tree?", has_scan)

if __name__ == '__main__':
    run_indexing_tests()
