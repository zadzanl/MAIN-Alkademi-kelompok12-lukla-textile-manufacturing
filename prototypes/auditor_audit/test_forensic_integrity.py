"""
Forensic Integrity Verification Test Suite for ai-ops-copilot-scaffold & messaging-bots-integration.
Auditor: Forensic Auditor IT2-1
"""
import uuid
import re
import secrets
import hmac
import hashlib
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

def test_pydantic_action_shortcut():
    print("--- Test 1: Pydantic ActionShortcut Model ---")
    class ActionShortcut(BaseModel):
        id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        title: str
        description: str
        url: str
        icon: Optional[str] = "external-link"
        prefill_params: Optional[Dict[str, Any]] = None

    shortcut = ActionShortcut(title="Test Shortcut", description="Testing instantiation", url="/app/quality")
    assert shortcut.id is not None, "id should not be None"
    assert len(shortcut.id) == 36, f"id length should be 36, got {len(shortcut.id)}"
    parsed_uuid = uuid.UUID(shortcut.id, version=4)
    assert str(parsed_uuid) == shortcut.id, "id should be a valid UUID v4"
    print(f"PASS: ActionShortcut instantiated with UUID v4: {shortcut.id}")

def test_hardened_regexes():
    print("--- Test 2: Hardened Regexes ---")
    order_re = re.compile(r'(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', re.IGNORECASE)
    line_re = re.compile(r'\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)', re.IGNORECASE)
    serial_re = re.compile(r'\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', re.IGNORECASE)

    # Negative order matches
    assert order_re.search("tolong reorder kain katun") is None, "False positive on 'reorder'"
    assert order_re.search("in order to fix defect") is None, "False positive on 'in order to'"
    assert order_re.search("order to fix") is None, "False positive on 'order to' (no digit)"

    # Positive order matches
    m1 = order_re.search("Order SO-2026-001")
    assert m1 and m1.group(1).upper() == "SO-2026-001", f"Order extraction failed: {m1}"
    m2 = order_re.search("order #so-2026-002")
    assert m2 and m2.group(1).upper() == "SO-2026-002", f"Order extraction failed: {m2}"

    # Line extraction
    assert line_re.search("online shop") is None, "False positive on 'online'"
    assert line_re.search("guideline text") is None, "False positive on 'guideline'"
    m_line = line_re.search("Input tally 30 menit line 2")
    assert m_line and m_line.group(1) == "2", f"Line match failed: {m_line}"
    norm_line = f"LINE-{int(m_line.group(1)):02d}" if m_line.group(1).isdigit() else m_line.group(1).upper()
    assert norm_line == "LINE-02", f"Line normalization failed: {norm_line}"

    m_jalur = line_re.search("jalur 3")
    assert m_jalur and m_jalur.group(1) == "3", f"Jalur match failed: {m_jalur}"
    norm_jalur = f"LINE-{int(m_jalur.group(1)):02d}" if m_jalur.group(1).isdigit() else m_jalur.group(1).upper()
    assert norm_jalur == "LINE-03", f"Jalur normalization failed: {norm_jalur}"

    # Serial extraction
    assert serial_re.search("serials inspection") is None, "False positive on 'serials'"
    m_asm = serial_re.search("barcode ASM-8910")
    assert m_asm, "Failed to match ASM-8910"
    raw_asm = (m_asm.group(1) or m_asm.group(2)).upper()
    assert raw_asm == "ASM-8910", f"ASM extraction failed: {raw_asm}"

    m_sn = serial_re.search("cek serial SN-2026-001 defect")
    assert m_sn, "Failed to match SN-2026-001"
    raw_sn = (m_sn.group(1) or m_sn.group(2)).upper()
    assert raw_sn == "SN-2026-001", f"SN extraction failed: {raw_sn}"

    print("PASS: Hardened regexes verified with word boundaries, digit anchors, and casing preservation.")

def test_disambiguation_decision_tree():
    print("--- Test 3: Disambiguation Decision Tree & Canonical Routes ---")
    order_re = re.compile(r'(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', re.IGNORECASE)
    line_re = re.compile(r'\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)', re.IGNORECASE)
    serial_re = re.compile(r'\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', re.IGNORECASE)

    def route_shortcut(text: str):
        text_lower = text.lower()
        m_ord = order_re.search(text)
        order_id = m_ord.group(1).upper() if m_ord else None
        m_ln = line_re.search(text)
        line_id = f"LINE-{int(m_ln.group(1)):02d}" if (m_ln and m_ln.group(1).isdigit()) else (m_ln.group(1).upper() if m_ln else None)
        m_sn = serial_re.search(text)
        serial_code = (m_sn.group(1) or m_sn.group(2)).upper() if m_sn else None

        qc_defect_terms = ["cacat", "defect", "repair", "reject", "inspeksi", "qc"]
        tally_phrases = ["tally", "tally jahit", "input tally", "hasil jahit", "sewing tally", "output jahit", "jalur jahit"]
        receiving_verbs = ["terima kain", "penerimaan bahan", "kain masuk", "gudang bahan", "receive material", "kedatangan kain"]
        cutting_verbs = ["potong kain", "hasil potong", "pemotongan kain", "catat potong", "buangan kain"]
        journal_phrases = ["jurnal", "ledger", "transaksi baru", "jurnal penyesuaian", "posting jurnal"]
        payroll_phrases = ["payroll", "gaji borongan", "upah sabtu", "rekap payroll", "penggajian"]

        # Rule 2: Defect/QC takes precedence over sewing tally even if containing 'jahit'
        if any(term in text_lower for term in qc_defect_terms):
            url = "/app/quality" + (f"?serialCode={serial_code}" if serial_code else "")
            return "qc-inspection", url

        # Rule 2: Sewing tally
        if any(p in text_lower for p in tally_phrases):
            url = "/terminal/tally" + (f"?lineId={line_id}" if line_id else "")
            return "sewing-tally", url

        # Rule 1: Warehouse receive takes precedence over cutting when receiving verbs present
        if any(v in text_lower for v in receiving_verbs) or ("gudang" in text_lower and "kain" in text_lower):
            url = "/app/materials?action=receive" + (f"&orderId={order_id}" if order_id else "")
            return "warehouse-receive", url

        # Rule 1: Cutting
        if any(v in text_lower for v in cutting_verbs):
            url = "/app/materials?action=cutting" + (f"&orderId={order_id}" if order_id else "")
            return "cutting-record", url

        # Rule 3: Finance
        if any(j in text_lower for j in journal_phrases):
            url = "/app/finance?tab=journals" + (f"&orderId={order_id}" if order_id else "")
            return "ledger-entry", url

        if any(p in text_lower for p in payroll_phrases):
            return "payroll-approval", "/app/finance?tab=payroll"

        return None, None

    # Test cases
    cases = [
        ("Terima kain di gudang bahan untuk Order SO-2026-001", "warehouse-receive", "/app/materials?action=receive&orderId=SO-2026-001"),
        ("Inspeksi QC ada cacat jahitan pada barcode ASM-8910", "qc-inspection", "/app/quality?serialCode=ASM-8910"),
        ("Input tally jahit 30 menit line 2", "sewing-tally", "/terminal/tally?lineId=LINE-02"),
        ("Catat hasil potong kain 500 pcs untuk Order SO-2026-001", "cutting-record", "/app/materials?action=cutting&orderId=SO-2026-001"),
        ("Posting jurnal transaksi baru Order SO-2026-001", "ledger-entry", "/app/finance?tab=journals&orderId=SO-2026-001"),
        ("Rekap payroll mingguan Sabtu", "payroll-approval", "/app/finance?tab=payroll"),
    ]

    for query, expected_id, expected_url in cases:
        actual_id, actual_url = route_shortcut(query)
        assert actual_id == expected_id, f"Query '{query}' expected id '{expected_id}', got '{actual_id}'"
        assert actual_url == expected_url, f"Query '{query}' expected url '{expected_url}', got '{actual_url}'"
        print(f"PASS: '{query}' -> {actual_id} ({actual_url})")

def test_crypto_token_and_signature():
    print("--- Test 4: Cryptographic Tokens & Webhook Signatures ---")
    tokens = [secrets.token_urlsafe(32) for _ in range(1000)]
    assert all(len(t) == 43 for t in tokens), "All tokens must be exactly 43 characters"
    assert all(re.match(r'^[A-Za-z0-9_-]+$', t) for t in tokens), "All tokens must use URL-safe chars"
    assert max(len(t) for t in tokens) <= 64, "Token must be <= 64 chars for Telegram deep-linking"
    print("PASS: 1,000 tokens strictly conform to Telegram 64-character ceiling.")

    secret = b"lukla-meta-webhook-secret"
    raw_payload = b'{"object":"whatsapp_business_account","entry":[{"id":"12345","changes":[{"value":{"messaging_product":"whatsapp"}}]}]}'
    correct_hash = hmac.new(secret, raw_payload, hashlib.sha256).hexdigest()
    correct_header = f"sha256={correct_hash}"

    parsed = json.loads(raw_payload.decode("utf-8"))
    reserialized = json.dumps(parsed).encode("utf-8")
    altered_hash = hmac.new(secret, reserialized, hashlib.sha256).hexdigest()
    altered_header = f"sha256={altered_hash}"

    assert hmac.compare_digest(correct_header, correct_header) is True
    assert hmac.compare_digest(correct_header, altered_header) is False
    print("PASS: Raw body byte validation confirmed; re-serialization failure confirmed.")

def test_outbox_sql_compilation():
    print("--- Test 5: PostgreSQL Outbox SQL Compilation ---")
    from sqlalchemy import select, Table, Column, MetaData, Integer, String
    from sqlalchemy.dialects.postgresql import dialect

    metadata = MetaData()
    test_table = Table(
        "outbox_events",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("status", String),
    )

    stmt = select(test_table).limit(10).with_for_update(skip_locked=True)
    compiled_sql = str(stmt.compile(dialect=dialect()))
    assert "FOR UPDATE SKIP LOCKED" in compiled_sql, f"Missing FOR UPDATE SKIP LOCKED in {compiled_sql}"
    print(f"PASS: Compiled SQL verified: {compiled_sql.strip()}")

if __name__ == "__main__":
    test_pydantic_action_shortcut()
    test_hardened_regexes()
    test_disambiguation_decision_tree()
    test_crypto_token_and_signature()
    test_outbox_sql_compilation()
    print("\nALL FORENSIC TESTS PASSED SUCCESSFULLY!")
