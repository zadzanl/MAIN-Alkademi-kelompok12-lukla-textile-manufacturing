import sqlite3
import uuid
import json
import base64
import time

def run_asc_keyset_audit():
    print("=================================================================")
    print("EMPIRICAL TEST 3: ASCENDING KEYSET CURSOR PAGINATION AUDIT")
    print("=================================================================\n")

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    # 1. Test entity A: ledger_accounts (code ASC, id ASC)
    c.execute('''
    CREATE TABLE ledger_accounts (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        account_class TEXT NOT NULL,
        active INTEGER NOT NULL
    )
    ''')
    c.execute('CREATE INDEX idx_ledger_accounts_active_code ON ledger_accounts (tenant_id, active, code ASC, id ASC)')

    # 2. Test entity B: garment_assemblies (created_at ASC, id ASC)
    c.execute('''
    CREATE TABLE garment_assemblies (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        serial_code TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    c.execute('CREATE INDEX idx_garment_assemblies_qc_queue ON garment_assemblies (tenant_id, status, created_at ASC, id ASC)')

    tenant_id = 't1'

    # -------------------------------------------------------------
    # Test 3.1: Boundary Tests on ledger_accounts
    # -------------------------------------------------------------
    print("--- Test 3.1: Boundary Cases (0 rows, 1 row, exact page_size, page_size+1) ---")

    def paginate_asc_ledger(active_flag, page_size, max_pages=1000):
        collected = []
        cursor_token = None
        pages = 0

        while True:
            pages += 1
            if pages > max_pages:
                raise RuntimeError(f"INFINITE LOOP DETECTED! Exceeded {max_pages} pages.")

            if cursor_token is None:
                query = '''
                SELECT code, id, name FROM ledger_accounts
                WHERE tenant_id = ? AND active = ?
                ORDER BY code ASC, id ASC
                LIMIT ?
                '''
                params = (tenant_id, active_flag, page_size + 1)
            else:
                payload = json.loads(base64.urlsafe_b64decode(cursor_token.encode()))
                cv, cid = payload['v'], payload['id']
                query = '''
                SELECT code, id, name FROM ledger_accounts
                WHERE tenant_id = ? AND active = ?
                  AND (
                    code > ?
                    OR (code = ? AND id > ?)
                  )
                ORDER BY code ASC, id ASC
                LIMIT ?
                '''
                params = (tenant_id, active_flag, cv, cv, cid, page_size + 1)

            res = c.execute(query, params).fetchall()
            if len(res) > page_size:
                items = res[:page_size]
                last = items[-1]
                next_payload = {'v': last[0], 'id': last[1]}
                cursor_token = base64.urlsafe_b64encode(json.dumps(next_payload).encode()).decode()
            else:
                items = res
                cursor_token = None

            collected.extend(items)
            if cursor_token is None:
                break

        return collected, pages

    # Case A: 0 records
    items, pages = paginate_asc_ledger(active_flag=1, page_size=10)
    assert len(items) == 0 and pages == 1, f"Empty table failed: items={len(items)}, pages={pages}"
    print("  [Pass] 0 rows -> 0 items, 1 page, nextCursor=null")

    # Case B: 1 record
    uid_single = str(uuid.uuid4())
    c.execute("INSERT INTO ledger_accounts VALUES (?, ?, '1000-CASH', 'Cash on Hand', 'ASSET', 1)", (uid_single, tenant_id))
    items, pages = paginate_asc_ledger(active_flag=1, page_size=10)
    assert len(items) == 1 and pages == 1, f"Single row failed: items={len(items)}, pages={pages}"
    print("  [Pass] 1 row -> 1 item, 1 page, nextCursor=null")

    # Case C: Exactly page_size records (10 rows with page_size=10)
    c.execute("DELETE FROM ledger_accounts")
    for i in range(10):
        c.execute("INSERT INTO ledger_accounts VALUES (?, ?, ?, ?, 'ASSET', 1)",
                  (str(uuid.uuid4()), tenant_id, f"100{i}-CODE", f"Account {i}"))
    items, pages = paginate_asc_ledger(active_flag=1, page_size=10)
    assert len(items) == 10 and pages == 1, f"Exact page_size failed: items={len(items)}, pages={pages}"
    print("  [Pass] Exactly 10 rows (page_size=10) -> 10 items, 1 page, nextCursor=null (no phantom page)")

    # Case D: page_size + 1 records (11 rows with page_size=10)
    c.execute("INSERT INTO ledger_accounts VALUES (?, ?, '1010-CODE', 'Account 10', 'ASSET', 1)",
              (str(uuid.uuid4()), tenant_id))
    items, pages = paginate_asc_ledger(active_flag=1, page_size=10)
    assert len(items) == 11 and pages == 2, f"page_size+1 failed: items={len(items)}, pages={pages}"
    print("  [Pass] Exactly 11 rows (page_size=10) -> 11 items, 2 pages, nextCursor terminates properly")

    # -------------------------------------------------------------
    # Test 3.2: High-Density Collision Stress Test on ledger_accounts
    # 500 rows with IDENTICAL code: "1050-PETTY-CASH"
    # -------------------------------------------------------------
    print("\n--- Test 3.2: High-Density Duplicate Sort Key Collisions (500 identical codes) ---")
    c.execute("DELETE FROM ledger_accounts")
    expected_tuples = []
    identical_code = "1050-PETTY-CASH"
    for i in range(500):
        uid = str(uuid.uuid4())
        c.execute("INSERT INTO ledger_accounts VALUES (?, ?, ?, ?, 'ASSET', 1)",
                  (uid, tenant_id, identical_code, f"Petty Cash Box {i}"))
        expected_tuples.append((identical_code, uid))

    # Add 100 rows with different codes
    for i in range(100):
        code = f"{2000 + i}-AP-VENDOR"
        uid = str(uuid.uuid4())
        c.execute("INSERT INTO ledger_accounts VALUES (?, ?, ?, ?, 'LIABILITY', 1)",
                  (uid, tenant_id, code, f"Vendor AP {i}"))
        expected_tuples.append((code, uid))

    expected_sorted = sorted(expected_tuples, key=lambda x: (x[0], x[1]))
    expected_ids = [x[1] for x in expected_sorted]
    total_ledger = len(expected_tuples)

    for ps in [7, 25, 50, 100]:
        t0 = time.perf_counter()
        items, pages = paginate_asc_ledger(active_flag=1, page_size=ps)
        elapsed = (time.perf_counter() - t0) * 1000
        got_ids = [r[1] for r in items]
        print(f"  [PageSize={ps:3d}] Pages: {pages:3d} | Fetched: {len(got_ids)}/{total_ledger} in {elapsed:.2f}ms")
        assert len(got_ids) == total_ledger, f"Mismatch: {len(got_ids)} vs {total_ledger}"
        assert len(got_ids) == len(set(got_ids)), "Duplicate accounts detected!"
        assert got_ids == expected_ids, "Strict ASC code+id ordering failed!"
        print(f"    -> VERIFIED: Tie-breaker id > :cursor_id correctly handled 500 collisions across {pages} pages.")

    # -------------------------------------------------------------
    # Test 3.3: QC Arrival Queue on garment_assemblies (created_at ASC, id ASC)
    # 5,000 records with microsecond timestamps and duplicate timestamps
    # -------------------------------------------------------------
    print("\n--- Test 3.3: FIFO QC Arrival Queue Benchmark (5,000 assemblies, created_at ASC, id ASC) ---")
    c.execute("DELETE FROM garment_assemblies")
    qc_tuples = []
    qc_rows = []

    # 50 clusters of 100 assemblies arriving at identical microsecond timestamps
    for cluster_idx in range(50):
        ts = f"2026-10-15T09:{cluster_idx//60:02d}:{cluster_idx%60:02d}.{cluster_idx*12345 % 1000000:06d}Z"
        for item_idx in range(100):
            uid = str(uuid.uuid4())
            serial = f"GARMENT-{cluster_idx:03d}-{item_idx:03d}"
            qc_rows.append((uid, tenant_id, serial, 'MENUNGGU_QC', ts))
            qc_tuples.append((ts, uid))

    c.executemany("INSERT INTO garment_assemblies VALUES (?, ?, ?, ?, ?)", qc_rows)
    conn.commit()

    expected_qc_sorted = sorted(qc_tuples, key=lambda x: (x[0], x[1]))
    expected_qc_ids = [x[1] for x in expected_qc_sorted]
    total_qc = len(qc_tuples)
    print(f"Populated {total_qc} QC queue assemblies.")

    def paginate_asc_assemblies(page_size):
        collected = []
        cursor_token = None
        pages = 0

        while True:
            pages += 1
            if cursor_token is None:
                query = '''
                SELECT created_at, id, serial_code FROM garment_assemblies
                WHERE tenant_id = ? AND status = ?
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                '''
                params = (tenant_id, 'MENUNGGU_QC', page_size + 1)
            else:
                payload = json.loads(base64.urlsafe_b64decode(cursor_token.encode()))
                cv, cid = payload['v'], payload['id']
                query = '''
                SELECT created_at, id, serial_code FROM garment_assemblies
                WHERE tenant_id = ? AND status = ?
                  AND (
                    created_at > ?
                    OR (created_at = ? AND id > ?)
                  )
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                '''
                params = (tenant_id, 'MENUNGGU_QC', cv, cv, cid, page_size + 1)

            res = c.execute(query, params).fetchall()
            if len(res) > page_size:
                items = res[:page_size]
                last = items[-1]
                next_payload = {'v': last[0], 'id': last[1]}
                cursor_token = base64.urlsafe_b64encode(json.dumps(next_payload).encode()).decode()
            else:
                items = res
                cursor_token = None

            collected.extend(items)
            if cursor_token is None:
                break

        return collected, pages

    for ps in [20, 50, 100, 250]:
        t0 = time.perf_counter()
        items, pages = paginate_asc_assemblies(page_size=ps)
        elapsed = (time.perf_counter() - t0) * 1000
        got_ids = [r[1] for r in items]
        print(f"  [PageSize={ps:3d}] Pages: {pages:3d} | Fetched: {len(got_ids)}/{total_qc} in {elapsed:.2f}ms")
        assert len(got_ids) == total_qc, f"Mismatch: {len(got_ids)} vs {total_qc}"
        assert len(got_ids) == len(set(got_ids)), "Duplicate QC garments detected!"
        assert got_ids == expected_qc_ids, "Strict FIFO ASC created_at+id ordering failed!"
        print(f"    -> VERIFIED: Strict FIFO ordering, 0 duplicate, 0 skips, zero infinite loops.")

    print("\n=================================================================")
    print(">>> CONCLUSION FOR TEST 3: ASC Keyset Template functions with 100% mathematical precision (0 loops, 0 skips, 0 duplicates).")
    print("=================================================================")
    return True

if __name__ == '__main__':
    run_asc_keyset_audit()
