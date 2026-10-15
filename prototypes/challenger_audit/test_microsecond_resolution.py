import sqlite3
import uuid
import json
import base64
import time
from datetime import datetime, timezone

def run_microsecond_resolution_audit():
    print("=================================================================")
    print("EMPIRICAL TEST 1: MICROSECOND RESOLUTION AUDIT (.ffffffZ)")
    print("=================================================================\n")

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE tallies (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        interval_start TEXT NOT NULL,
        operator_id TEXT NOT NULL
    )
    ''')
    c.execute('CREATE INDEX idx_tallies ON tallies (tenant_id, interval_start DESC, id DESC)')

    tenant_id = 'tenant-test-001'

    # Generate test dataset:
    # 1. 200 rows with exact same timestamp down to microsecond: "2026-10-15T08:00:00.123456Z"
    # 2. 200 rows with timestamps differing ONLY in microseconds: "2026-10-15T08:00:00.123455Z", ...454Z, etc.
    # 3. 200 rows with timestamps differing across millisecond boundaries: "2026-10-15T08:00:00.124000Z", etc.
    rows = []
    expected_tuples = []

    # Cluster 1: 200 rows with identical microsecond timestamp
    ts_cluster1 = "2026-10-15T08:30:00.123456Z"
    for i in range(200):
        uid = str(uuid.uuid4())
        rows.append((uid, tenant_id, ts_cluster1, f"op_cluster1_{i}"))
        expected_tuples.append((ts_cluster1, uid))

    # Cluster 2: 200 rows with varying microsecond timestamps within same millisecond
    for i in range(200):
        ts_cluster2 = f"2026-10-15T08:20:00.123{i:03d}Z"
        uid = str(uuid.uuid4())
        rows.append((uid, tenant_id, ts_cluster2, f"op_cluster2_{i}"))
        expected_tuples.append((ts_cluster2, uid))

    # Cluster 3: 200 rows across different seconds
    for i in range(200):
        ts_cluster3 = f"2026-10-15T08:10:{i//60:02d}.{i%60:06d}Z"
        uid = str(uuid.uuid4())
        rows.append((uid, tenant_id, ts_cluster3, f"op_cluster3_{i}"))
        expected_tuples.append((ts_cluster3, uid))

    c.executemany('INSERT INTO tallies VALUES (?, ?, ?, ?)', rows)
    conn.commit()

    total_records = len(rows)
    print(f"Populated {total_records} test rows into SQLite database.")

    # Sort descending by ts DESC, id DESC
    expected_order = sorted(expected_tuples, key=lambda x: (x[0], x[1]), reverse=True)
    expected_ids = [x[1] for x in expected_order]

    # -------------------------------------------------------------
    # SUB-TEST A: With Millisecond Truncation (Iteration 1 Flaw)
    # -------------------------------------------------------------
    print("\n--- Sub-Test A: Keyset Pagination with MILLISECOND TRUNCATION (.3fZ) ---")
    page_size = 25
    collected_ids_ms = []
    cursor_token = None
    pages_ms = 0

    while True:
        pages_ms += 1
        if cursor_token is None:
            query = '''
            SELECT interval_start, id FROM tallies
            WHERE tenant_id = ?
            ORDER BY interval_start DESC, id DESC
            LIMIT ?
            '''
            params = (tenant_id, page_size + 1)
        else:
            payload = json.loads(base64.urlsafe_b64decode(cursor_token.encode()))
            cv, cid = payload['v'], payload['id']
            query = '''
            SELECT interval_start, id FROM tallies
            WHERE tenant_id = ?
              AND (
                interval_start < ?
                OR (interval_start = ? AND id < ?)
              )
            ORDER BY interval_start DESC, id DESC
            LIMIT ?
            '''
            params = (tenant_id, cv, cv, cid, page_size + 1)

        res = c.execute(query, params).fetchall()
        if len(res) > page_size:
            items = res[:page_size]
            last = items[-1]
            # TRUNCATE to 3-digit milliseconds: e.g. "2026-10-15T08:30:00.123000Z"
            ts_val = last[0]
            # Truncate microsecond string to 3 decimals: .123456Z -> .123000Z
            if '.' in ts_val:
                prefix, frac = ts_val.split('.')
                ms_frac = frac[:3] + "000Z"
                truncated_ts = f"{prefix}.{ms_frac}"
            else:
                truncated_ts = ts_val

            next_payload = {'v': truncated_ts, 'id': last[1]}
            cursor_token = base64.urlsafe_b64encode(json.dumps(next_payload).encode()).decode()
        else:
            items = res
            cursor_token = None

        collected_ids_ms.extend([r[1] for r in items])
        if cursor_token is None or len(items) == 0:
            break

    dropped_count_ms = total_records - len(collected_ids_ms)
    print(f"Total Expected Rows: {total_records}")
    print(f"Total Rows Retrieved with Millisecond Truncation: {len(collected_ids_ms)}")
    print(f"DROPPED ROWS DETECTED: {dropped_count_ms}")
    print(f"Vulnerability Reproduced? {'YES (CRITICAL DATA LOSS)' if dropped_count_ms > 0 else 'NO'}")

    # -------------------------------------------------------------
    # SUB-TEST B: With 6-Digit Microsecond Resolution (Section 1.3 Remediation)
    # -------------------------------------------------------------
    print("\n--- Sub-Test B: Keyset Pagination with MICROSECOND RESOLUTION (.ffffffZ) ---")
    for test_page_size in [10, 25, 50, 100]:
        collected_ids_us = []
        cursor_token = None
        pages_us = 0
        t0 = time.perf_counter()

        while True:
            pages_us += 1
            if cursor_token is None:
                query = '''
                SELECT interval_start, id FROM tallies
                WHERE tenant_id = ?
                ORDER BY interval_start DESC, id DESC
                LIMIT ?
                '''
                params = (tenant_id, test_page_size + 1)
            else:
                payload = json.loads(base64.urlsafe_b64decode(cursor_token.encode()))
                cv, cid = payload['v'], payload['id']
                query = '''
                SELECT interval_start, id FROM tallies
                WHERE tenant_id = ?
                  AND (
                    interval_start < ?
                    OR (interval_start = ? AND id < ?)
                  )
                ORDER BY interval_start DESC, id DESC
                LIMIT ?
                '''
                params = (tenant_id, cv, cv, cid, test_page_size + 1)

            res = c.execute(query, params).fetchall()
            if len(res) > test_page_size:
                items = res[:test_page_size]
                last = items[-1]
                # FULL 6-digit microsecond string
                full_ts = last[0]
                next_payload = {'v': full_ts, 'id': last[1]}
                cursor_token = base64.urlsafe_b64encode(json.dumps(next_payload).encode()).decode()
            else:
                items = res
                cursor_token = None

            collected_ids_us.extend([r[1] for r in items])
            if cursor_token is None:
                break

        elapsed = (time.perf_counter() - t0) * 1000
        print(f"[PageSize={test_page_size:3d}] Pages: {pages_us:3d} | Retrieved: {len(collected_ids_us)}/{total_records} rows in {elapsed:.2f}ms")
        assert len(collected_ids_us) == total_records, f"FAIL: Expected {total_records}, got {len(collected_ids_us)}"
        assert len(collected_ids_us) == len(set(collected_ids_us)), "FAIL: Duplicate rows detected!"
        assert collected_ids_us == expected_ids, "FAIL: Output order mismatch!"
        print(f"  -> VERIFIED: 0 dropped rows, 0 duplicates, 100% deterministic order match.")

    print("\n>>> CONCLUSION FOR TEST 1: Section 1.3 microsecond resolution requirement (.ffffffZ) 100% eliminates sibling row dropping.")
    return True

if __name__ == '__main__':
    run_microsecond_resolution_audit()
