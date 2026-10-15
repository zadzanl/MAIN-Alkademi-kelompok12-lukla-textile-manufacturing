import sqlite3
import uuid
import json
import base64
import time

def stress_test_pagination():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE tallies (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        interval_start TEXT NOT NULL,
        data TEXT
    )
    ''')
    c.execute('CREATE INDEX idx_tallies ON tallies (tenant_id, interval_start DESC, id DESC)')

    tenant_id = 't1'
    total_records = 10000
    distinct_timestamps = 100  # 100 records per timestamp!
    print(f"Generating {total_records} records with {distinct_timestamps} timestamps (100 records per duplicate timestamp)...")

    rows = []
    expected_tuples = []
    for i in range(distinct_timestamps):
        ts = f"2026-10-15T{i // 60:02d}:{i % 60:02d}:00.123456Z"
        for _ in range(total_records // distinct_timestamps):
            uid = str(uuid.uuid4())
            rows.append((uid, tenant_id, ts, f"row_{i}"))
            expected_tuples.append((ts, uid))

    c.executemany('INSERT INTO tallies VALUES (?, ?, ?, ?)', rows)
    conn.commit()

    # Sort descending by ts DESC, id DESC
    expected_order = sorted(expected_tuples, key=lambda x: (x[0], x[1]), reverse=True)
    expected_ids = [x[1] for x in expected_order]

    print("Data populated. Starting keyset pagination stress test...")

    for page_size in [10, 50, 100]:
        t0 = time.perf_counter()
        collected_ids = []
        cursor_token = None
        pages = 0

        while True:
            pages += 1
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
                next_payload = {'v': last[0], 'id': last[1]}
                cursor_token = base64.urlsafe_b64encode(json.dumps(next_payload).encode()).decode()
            else:
                items = res
                cursor_token = None

            collected_ids.extend([r[1] for r in items])
            if cursor_token is None:
                break

        duration = time.perf_counter() - t0
        print(f"\n[PageSize={page_size:3d}] Fetched {len(collected_ids)} items across {pages} pages in {duration*1000:.2f}ms")
        assert len(collected_ids) == total_records, f"Mismatch in count: {len(collected_ids)} vs {total_records}"
        assert len(collected_ids) == len(set(collected_ids)), "Duplicate items detected in pagination!"
        assert collected_ids == expected_ids, "Collected items order does not match expected exact order!"
        print(f"PASSED: Strict determinism, 0 duplicates, 0 skips, 0 loops!")

if __name__ == '__main__':
    stress_test_pagination()
