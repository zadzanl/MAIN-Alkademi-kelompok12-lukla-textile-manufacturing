import sqlite3

def run_base_cursor_indexing_audit():
    print("=================================================================")
    print("EMPIRICAL TEST 2: BASE KEYSET CURSOR INDEXING AUDIT")
    print("=================================================================\n")

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    # Define test entities
    tables = [
        {
            "name": "cut_batches",
            "schema": """
                CREATE TABLE cut_batches (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    component_code TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """,
            "filter_index": "CREATE INDEX idx_cut_batches_order_component ON cut_batches (tenant_id, order_id, component_code, created_at DESC, id DESC)",
            "base_index": "CREATE INDEX idx_cut_batches_base_cursor ON cut_batches (tenant_id, created_at DESC, id DESC)",
            "test_cases": [
                {
                    "name": "GET /cut-batches (unfiltered general discovery)",
                    "query": "SELECT * FROM cut_batches WHERE tenant_id = 't1' ORDER BY created_at DESC, id DESC LIMIT 20"
                },
                {
                    "name": "GET /cut-batches?componentCode=COLLAR (omitting orderId)",
                    "query": "SELECT * FROM cut_batches WHERE tenant_id = 't1' AND component_code = 'COLLAR' ORDER BY created_at DESC, id DESC LIMIT 20"
                },
                {
                    "name": "GET /cut-batches?orderId=ord-1&componentCode=COLLAR (all filters provided)",
                    "query": "SELECT * FROM cut_batches WHERE tenant_id = 't1' AND order_id = 'ord-1' AND component_code = 'COLLAR' ORDER BY created_at DESC, id DESC LIMIT 20"
                }
            ]
        },
        {
            "name": "sewing_tallies",
            "schema": """
                CREATE TABLE sewing_tallies (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    line_id TEXT NOT NULL,
                    operator_id TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    interval_start TEXT NOT NULL
                )
            """,
            "filter_index": """
                CREATE INDEX idx_sewing_tallies_mandor_queue ON sewing_tallies (tenant_id, line_id, status, interval_start DESC, id DESC);
                CREATE INDEX idx_sewing_tallies_order_operator ON sewing_tallies (tenant_id, order_id, operator_id, interval_start DESC, id DESC);
            """,
            "base_index": "CREATE INDEX idx_sewing_tallies_base_cursor ON sewing_tallies (tenant_id, interval_start DESC, id DESC)",
            "test_cases": [
                {
                    "name": "GET /sewing-tallies (unfiltered general discovery)",
                    "query": "SELECT * FROM sewing_tallies WHERE tenant_id = 't1' ORDER BY interval_start DESC, id DESC LIMIT 20"
                },
                {
                    "name": "GET /sewing-tallies?operatorId=op1 (omitting lineId and orderId)",
                    "query": "SELECT * FROM sewing_tallies WHERE tenant_id = 't1' AND operator_id = 'op1' ORDER BY interval_start DESC, id DESC LIMIT 20"
                },
                {
                    "name": "GET /sewing-tallies?lineId=line-1&status=RECORDED (mandor queue filters provided)",
                    "query": "SELECT * FROM sewing_tallies WHERE tenant_id = 't1' AND line_id = 'line-1' AND status = 'RECORDED' ORDER BY interval_start DESC, id DESC LIMIT 20"
                }
            ]
        },
        {
            "name": "purchase_orders",
            "schema": """
                CREATE TABLE purchase_orders (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """,
            "filter_index": "CREATE INDEX idx_purchase_orders_tenant_status ON purchase_orders (tenant_id, status, created_at DESC, id DESC)",
            "base_index": "CREATE INDEX idx_purchase_orders_base_cursor ON purchase_orders (tenant_id, created_at DESC, id DESC)",
            "test_cases": [
                {
                    "name": "GET /purchase-orders (unfiltered discovery omitting status)",
                    "query": "SELECT * FROM purchase_orders WHERE tenant_id = 't1' ORDER BY created_at DESC, id DESC LIMIT 20"
                },
                {
                    "name": "GET /purchase-orders?status=APPROVED (status filter provided)",
                    "query": "SELECT * FROM purchase_orders WHERE tenant_id = 't1' AND status = 'APPROVED' ORDER BY created_at DESC, id DESC LIMIT 20"
                }
            ]
        },
        {
            "name": "supplier_invoices",
            "schema": """
                CREATE TABLE supplier_invoices (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    purchase_order_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """,
            "filter_index": "CREATE INDEX idx_supplier_invoices_po_cursor ON supplier_invoices (tenant_id, purchase_order_id, created_at DESC, id DESC)",
            "base_index": "CREATE INDEX idx_supplier_invoices_base_cursor ON supplier_invoices (tenant_id, created_at DESC, id DESC)",
            "test_cases": [
                {
                    "name": "GET /supplier-invoices (unfiltered discovery omitting purchaseOrderId)",
                    "query": "SELECT * FROM supplier_invoices WHERE tenant_id = 't1' ORDER BY created_at DESC, id DESC LIMIT 20"
                },
                {
                    "name": "GET /supplier-invoices?purchaseOrderId=po-1 (PO filter provided)",
                    "query": "SELECT * FROM supplier_invoices WHERE tenant_id = 't1' AND purchase_order_id = 'po-1' ORDER BY created_at DESC, id DESC LIMIT 20"
                }
            ]
        },
        {
            "name": "time_studies",
            "schema": """
                CREATE TABLE time_studies (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    sample_revision_id TEXT NOT NULL,
                    component_code TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """,
            "filter_index": "CREATE INDEX idx_time_studies_revision_component_cursor ON time_studies (tenant_id, sample_revision_id, component_code, created_at DESC, id DESC)",
            "base_index": "CREATE INDEX idx_time_studies_base_cursor ON time_studies (tenant_id, created_at DESC, id DESC)",
            "test_cases": [
                {
                    "name": "GET /time-studies (unfiltered discovery omitting revision and component)",
                    "query": "SELECT * FROM time_studies WHERE tenant_id = 't1' ORDER BY created_at DESC, id DESC LIMIT 20"
                },
                {
                    "name": "GET /time-studies?sampleRevisionId=rev-1&componentCode=SLEEVE (all filters provided)",
                    "query": "SELECT * FROM time_studies WHERE tenant_id = 't1' AND sample_revision_id = 'rev-1' AND component_code = 'SLEEVE' ORDER BY created_at DESC, id DESC LIMIT 20"
                }
            ]
        }
    ]

    all_passed = True

    for t in tables:
        table_name = t["name"]
        print(f"-----------------------------------------------------------------")
        print(f"TABLE: {table_name}")
        print(f"-----------------------------------------------------------------")

        # Create table and initial filter-only indexes
        c.execute(f"DROP TABLE IF EXISTS {table_name}")
        c.execute(t["schema"])
        for stmt in t["filter_index"].strip().split(';'):
            if stmt.strip():
                c.execute(stmt)

        print("Phase A: Testing Execution Plans BEFORE Adding Base Keyset Index...")
        for tc in t["test_cases"]:
            plan = c.execute(f"EXPLAIN QUERY PLAN {tc['query']}").fetchall()
            has_temp_sort = any('TEMP B-TREE' in str(p) for p in plan)
            has_scan = any('SCAN' in str(p) for p in plan)
            print(f"  [Before] {tc['name']}")
            print(f"           Plan: {plan}")
            print(f"           Temporary B-Tree Sort? {has_temp_sort}")

        # Now add the remediated base keyset cursor index
        c.execute(t["base_index"])
        print("\nPhase B: Testing Execution Plans AFTER Adding Base Keyset Index...")
        for tc in t["test_cases"]:
            plan = c.execute(f"EXPLAIN QUERY PLAN {tc['query']}").fetchall()
            has_temp_sort = any('TEMP B-TREE' in str(p) for p in plan)
            used_index = any(t['name'] in str(p) and 'INDEX' in str(p) for p in plan)
            print(f"  [After]  {tc['name']}")
            print(f"           Plan: {plan}")
            print(f"           Temporary B-Tree Sort Eliminated? {not has_temp_sort}")

            # For unfiltered queries, temporary sort MUST be eliminated
            if "unfiltered" in tc['name'].lower():
                if has_temp_sort:
                    print(f"  ERROR: Unfiltered query {tc['name']} still uses TEMP B-TREE!")
                    all_passed = False
                else:
                    print(f"  SUCCESS: Unfiltered query uses index-backed sort without temp memory/disk sort.")

        print()

    print("=================================================================")
    if all_passed:
        print(">>> CONCLUSION FOR TEST 2: ALL BASE KEYSET INDEXES ELIMINATE TEMP B-TREE SORTS ON UNFILTERED QUERIES (100% PASS).")
    else:
        print(">>> CONCLUSION FOR TEST 2: FAILURES DETECTED IN INDEX AUDIT.")
    print("=================================================================")
    return all_passed

if __name__ == '__main__':
    run_base_cursor_indexing_audit()
