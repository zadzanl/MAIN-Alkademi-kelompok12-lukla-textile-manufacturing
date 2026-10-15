import base64
import json
import uuid
import datetime

def parse_and_validate_cursor(token: str):
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        payload = json.loads(raw)
    except Exception:
        return False, 'Invalid base64 or JSON'
    
    if not isinstance(payload, dict):
        return False, 'Cursor payload must be JSON object'
    if 'v' not in payload or 'id' not in payload:
        return False, 'Missing cursor fields v or id'
    
    # Validate UUID
    try:
        uuid_val = uuid.UUID(payload['id'])
    except Exception:
        return False, 'Invalid UUID in cursor id'
    
    return True, (payload['v'], str(uuid_val))

def run_tests():
    valid_token = base64.urlsafe_b64encode(json.dumps({
        "v": "2026-10-15T08:00:00.123456Z",
        "id": "8e29f69c-01f2-4c99-81b2-5bcae1f4a723"
    }).encode()).decode()

    tests = [
        ('not_base64_???', False),
        (base64.urlsafe_b64encode(b'not json').decode(), False),
        (base64.urlsafe_b64encode(json.dumps({"v": "2026-10-15"}).encode()).decode(), False),
        (base64.urlsafe_b64encode(json.dumps({"v": "2026-10-15", "id": "not-a-uuid"}).encode()).decode(), False),
        (valid_token, True),
    ]

    for t, expected in tests:
        valid, res = parse_and_validate_cursor(t)
        print(f"Token {t[:25]:25} -> Valid: {valid:5} (Expected: {expected:5}), Detail: {res}")
        assert valid == expected

    print("\nALL CURSOR VALIDATION TESTS PASSED!")

if __name__ == '__main__':
    run_tests()
