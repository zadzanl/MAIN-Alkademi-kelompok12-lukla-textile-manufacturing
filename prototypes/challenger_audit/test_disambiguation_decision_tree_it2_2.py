#!/usr/bin/env python3
"""
Empirical Disambiguation & Decision Tree Test Harness
Challenger IT2-2 (Disambiguation Challenger)

Validates Section 2.4 of:
openspec/changes/ai-ops-copilot-scaffold/artifacts/reference-grounding-report.md

Focus:
1. Rule 1 (Fabric Material Disambiguation): Cutting vs. Warehouse Intake
   - Standalone 'kain' forbidden from triggering cutting
   - Receiving verbs ('terima', 'masuk', 'receive') suppress cutting
2. Rule 2 (Sewing vs. Quality Defect Disambiguation):
   - Standalone 'jahit' forbidden from triggering sewing tally
   - Defect markers ('cacat', 'defect', 'repair', 'reject', 'inspeksi', 'qc') take absolute precedence
3. Rule 3 (Finance & Ledger Disambiguation):
   - Journal vs. Payroll isolation and permitted query parameters
4. Entity Extractors:
   - Order ID: (?<!\\bin\\s)\\border\\s*#?\\s*([A-Za-z0-9\\-]*\\d[A-Za-z0-9\\-]*)
   - Line ID: \\b(?:line|jalur)\\s*#?\\s*([A-Za-z0-9\\-]+)
   - Serial Code: \\b((?:ASM|SN)-[A-Za-z0-9\\-]+)|\\b(?:barcode|serial)\\s*[-:#]?\\s*([A-Za-z0-9\\-]*\\d[A-Za-z0-9\\-]*)
5. Mandatory Test Queries:
   - Query 1: "Terima kain di gudang bahan untuk Order SO-2026-001" -> /app/materials?action=receive&orderId=SO-2026-001 (NOT cutting)
   - Query 2: "Inspeksi QC ada cacat jahitan pada barcode ASM-8910" -> /app/quality?serialCode=ASM-8910 (NOT sewing tally)
   - Query 3: "Input tally jahit 30 menit line 2" -> /terminal/tally?lineId=LINE-02
"""

import re
import sys
import uuid
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# 1. Pydantic Model from Section 5.2
# ----------------------------------------------------------------------
class ActionShortcut(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    url: str
    icon: Optional[str] = "external-link"
    prefill_params: Optional[Dict[str, Any]] = None


# ----------------------------------------------------------------------
# 2. Section 2.4 Disambiguation Engine Implementation
# ----------------------------------------------------------------------
ORDER_REGEX = re.compile(r'(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', re.IGNORECASE)
LINE_REGEX = re.compile(r'\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)', re.IGNORECASE)
SERIAL_REGEX = re.compile(r'\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', re.IGNORECASE)

# Keywords per Table 2.4.1
CUTTING_KEYWORDS = ["potong kain", "hasil potong", "cutting", "pemotongan kain", "catat potong", "buangan kain"]
RECEIVING_KEYWORDS = ["terima kain", "penerimaan bahan", "kain masuk", "gudang bahan", "receive material", "kedatangan kain"]
RECEIVING_SUPPRESSION_VERBS = ["terima", "receive", "masuk", "kedatangan"]
CUTTING_SUPPRESSION_VERBS = ["potong", "cutting", "buangan"]

SEWING_TALLY_KEYWORDS = ["tally", "tally jahit", "input tally", "hasil jahit", "sewing tally", "output jahit", "jalur jahit"]
DEFECT_QC_MARKERS = ["cacat", "defect", "repair", "reject", "inspeksi", "qc"]
QC_KEYWORDS = ["qc", "cacat", "defect", "inspeksi qc", "repair", "reject", "cacat jahitan"]

JOURNAL_KEYWORDS = ["jurnal", "ledger", "transaksi baru", "jurnal penyesuaian", "posting jurnal"]
PAYROLL_KEYWORDS = ["payroll", "gaji borongan", "upah sabtu", "rekap payroll", "penggajian"]


def extract_entities(text: str) -> Dict[str, Optional[str]]:
    # Order ID
    m_order = ORDER_REGEX.search(text)
    order_id = m_order.group(1).upper() if m_order else None

    # Line ID
    m_line = LINE_REGEX.search(text)
    line_id = None
    if m_line:
        raw_line = m_line.group(1)
        if raw_line.isdigit():
            line_id = f"LINE-{int(raw_line):02d}"
        else:
            line_id = raw_line.upper()

    # Serial Code
    m_serial = SERIAL_REGEX.search(text)
    serial_code = None
    if m_serial:
        raw_serial = m_serial.group(1) or m_serial.group(2)
        if raw_serial:
            serial_code = raw_serial.upper()

    return {
        "orderId": order_id,
        "lineId": line_id,
        "serialCode": serial_code,
    }


def classify_action_shortcut(raw_text: str) -> Optional[ActionShortcut]:
    text_lower = raw_text.lower()
    entities = extract_entities(raw_text)

    # 1. RULE 2: SEWING VS. QC DEFECT DISAMBIGUATION
    # Defect markers take absolute precedence over sewing tally even if containing 'jahit'/'jahitan'
    has_defect_marker = any(marker in text_lower for marker in DEFECT_QC_MARKERS)
    if has_defect_marker:
        if any(kw in text_lower for kw in QC_KEYWORDS):
            # QC Inspection
            params = []
            if entities["serialCode"]:
                params.append(f"serialCode={entities['serialCode']}")
            if entities["orderId"]:
                params.append(f"orderId={entities['orderId']}")
            qs = f"?{'&'.join(params)}" if params else ""
            return ActionShortcut(
                title="Formulir Inspeksi QC",
                description="Buka formulir klasifikasi cacat (Pass, Repair, Reject).",
                url=f"/app/quality{qs}",
                icon="check-circle",
                prefill_params={"serialCode": entities["serialCode"], "orderId": entities["orderId"]}
            )

    # If no defect markers, check sewing tally
    has_sewing_tally_kw = any(kw in text_lower for kw in SEWING_TALLY_KEYWORDS)
    # Standalone 'jahit' without tally phrase is forbidden
    if has_sewing_tally_kw and not has_defect_marker:
        params = []
        if entities["lineId"]:
            params.append(f"lineId={entities['lineId']}")
        if entities["orderId"]:
            params.append(f"orderId={entities['orderId']}")
        qs = f"?{'&'.join(params)}" if params else ""
        return ActionShortcut(
            title="Input Hasil Jahit (Tally 30 Menit)",
            description="Buka form input hitungan per operator jalur jahit.",
            url=f"/terminal/tally{qs}",
            icon="needle",
            prefill_params={"lineId": entities["lineId"], "orderId": entities["orderId"]}
        )

    # 2. RULE 1: FABRIC MATERIAL DISAMBIGUATION (Cutting vs. Warehouse Intake)
    has_receiving_kw = any(kw in text_lower for kw in RECEIVING_KEYWORDS)
    has_receiving_suppression = any(verb in text_lower for verb in RECEIVING_SUPPRESSION_VERBS)
    has_cutting_kw = any(kw in text_lower for kw in CUTTING_KEYWORDS)

    # Standalone 'kain' is forbidden from triggering cutting
    if has_receiving_kw or (has_receiving_suppression and "kain" in text_lower):
        # Warehouse Receiving
        order_qs = f"?orderId={entities['orderId']}" if entities["orderId"] else ""
        return ActionShortcut(
            title="Penerimaan Bahan Baku (Warehouse)",
            description="Buka form pencatatan kain masuk maklon atau Snøhund.",
            url=f"/app/materials?action=receive{('&' + order_qs[1:]) if order_qs else ''}",
            icon="box",
            prefill_params={"orderId": entities["orderId"]}
        )

    if has_cutting_kw and not has_receiving_suppression:
        # Cutting Record
        order_qs = f"?orderId={entities['orderId']}" if entities["orderId"] else ""
        return ActionShortcut(
            title="Catat Hasil Pemotongan (Cutting)",
            description="Buka formulir input pemotongan kain dan input buangan.",
            url=f"/app/materials?action=cutting{('&' + order_qs[1:]) if order_qs else ''}",
            icon="scissors",
            prefill_params={"orderId": entities["orderId"]}
        )

    # 3. RULE 3: FINANCE & LEDGER DISAMBIGUATION
    has_payroll_kw = any(kw in text_lower for kw in PAYROLL_KEYWORDS)
    if has_payroll_kw:
        # Payroll approval allows NO query params per Table 2.4.1
        return ActionShortcut(
            title="Halaman Rekap Payroll Mingguan",
            description="Hitung dan setujui penggajian borongan Sabtu.",
            url="/app/finance?tab=payroll",
            icon="dollar-sign",
            prefill_params=None
        )

    has_journal_kw = any(kw in text_lower for kw in JOURNAL_KEYWORDS)
    if has_journal_kw:
        order_qs = f"?orderId={entities['orderId']}" if entities["orderId"] else ""
        return ActionShortcut(
            title="Jurnal Double-Entry Baru",
            description="Buka form posting jurnal akuntansi berimbang dengan idempotency key.",
            url=f"/app/finance?tab=journals{('&' + order_qs[1:]) if order_qs else ''}",
            icon="book",
            prefill_params={"orderId": entities["orderId"]}
        )

    return None


# ----------------------------------------------------------------------
# 3. Test Runner
# ----------------------------------------------------------------------
def run_test(name: str, fn):
    print(f"[*] Running: {name} ...", end=" ")
    try:
        fn()
        print("✅ PASS")
        return True
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        return False
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False


def test_mandatory_query_1_warehouse_receiving():
    query = "Terima kain di gudang bahan untuk Order SO-2026-001"
    shortcut = classify_action_shortcut(query)
    assert shortcut is not None, "Failed to classify shortcut"
    assert "/app/materials?action=receive" in shortcut.url, f"Expected warehouse receiving route, got: {shortcut.url}"
    assert "action=cutting" not in shortcut.url, f"Incorrectly routed to cutting: {shortcut.url}"
    assert "orderId=SO-2026-001" in shortcut.url, f"Missing or incorrect orderId parameter in {shortcut.url}"
    assert shortcut.title == "Penerimaan Bahan Baku (Warehouse)"


def test_mandatory_query_2_qc_inspection():
    query = "Inspeksi QC ada cacat jahitan pada barcode ASM-8910"
    shortcut = classify_action_shortcut(query)
    assert shortcut is not None, "Failed to classify shortcut"
    assert shortcut.url.startswith("/app/quality"), f"Expected /app/quality route, got: {shortcut.url}"
    assert "terminal/tally" not in shortcut.url, f"Incorrectly routed to sewing tally: {shortcut.url}"
    assert "serialCode=ASM-8910" in shortcut.url, f"Missing serialCode parameter in {shortcut.url}"
    assert shortcut.title == "Formulir Inspeksi QC"


def test_mandatory_query_3_sewing_floor_terminal():
    query = "Input tally jahit 30 menit line 2"
    shortcut = classify_action_shortcut(query)
    assert shortcut is not None, "Failed to classify shortcut"
    assert shortcut.url == "/terminal/tally?lineId=LINE-02", f"Expected /terminal/tally?lineId=LINE-02, got: {shortcut.url}"
    assert shortcut.title == "Input Hasil Jahit (Tally 30 Menit)"


def test_bare_kain_prohibition():
    # Standalone 'kain' must NOT trigger cutting
    query = "Berapa sisa kain katun di gudang?"
    # Note: does not contain receiving action phrases or cutting action phrases
    shortcut = classify_action_shortcut(query)
    assert shortcut is None or "action=cutting" not in shortcut.url, "Bare kain triggered cutting!"


def test_bare_jahit_prohibition():
    # Standalone 'jahit' must NOT trigger sewing tally
    query = "Berapa operator jahit yang hadir hari ini?"
    shortcut = classify_action_shortcut(query)
    assert shortcut is None, f"Bare jahit incorrectly triggered shortcut: {shortcut}"


def test_defect_precedence_over_sewing_tally():
    # Contains 'hasil jahit' and 'tally' but also 'cacat' -> MUST route to QC
    query = "Ada cacat jahitan pada hasil jahit line 2"
    shortcut = classify_action_shortcut(query)
    assert shortcut is not None
    assert "/app/quality" in shortcut.url
    assert "/terminal/tally" not in shortcut.url


def test_receiving_suppresses_cutting():
    # Mixed collision: 'potong kain' + 'terima kain'
    query = "Terima kain katun untuk jadwal potong kain Order SO-2026-002"
    shortcut = classify_action_shortcut(query)
    assert shortcut is not None
    assert "/app/materials?action=receive" in shortcut.url
    assert "action=cutting" not in shortcut.url
    assert "orderId=SO-2026-002" in shortcut.url


def test_cutting_positive_trigger():
    query = "Catat hasil potong 500 pcs untuk Order SO-2026-003"
    shortcut = classify_action_shortcut(query)
    assert shortcut is not None
    assert shortcut.url == "/app/materials?action=cutting&orderId=SO-2026-003"


def test_entity_extractor_order_id():
    # False positive negative cases
    assert ORDER_REGEX.search("Tolong reorder kain katun") is None
    assert ORDER_REGEX.search("in order to maintain sewing quality") is None
    assert ORDER_REGEX.search("order kain") is None

    # Positive cases with uppercase normalization
    m1 = ORDER_REGEX.search("Order SO-2026-001")
    assert m1 and m1.group(1).upper() == "SO-2026-001"

    m2 = ORDER_REGEX.search("order #9944")
    assert m2 and m2.group(1).upper() == "9944"


def test_entity_extractor_line_id():
    # Word boundary negative checks
    assert LINE_REGEX.search("User is online now") is None
    assert LINE_REGEX.search("Read the guideline carefully") is None

    # Positive numeric padding checks
    entities1 = extract_entities("Input tally line 2")
    assert entities1["lineId"] == "LINE-02"

    entities2 = extract_entities("Jalur 14 input tally")
    assert entities2["lineId"] == "LINE-14"

    entities3 = extract_entities("Input tally line LINE-05")
    assert entities3["lineId"] == "LINE-05"


def test_entity_extractor_serial_code():
    entities1 = extract_entities("Cacat pada barcode ASM-8910")
    assert entities1["serialCode"] == "ASM-8910"

    entities2 = extract_entities("Inspeksi barcode SN-2026-009")
    assert entities2["serialCode"] == "SN-2026-009"

    entities3 = extract_entities("Defect pada serial: 778899")
    assert entities3["serialCode"] == "778899"

    assert extract_entities("serials in process")["serialCode"] is None


def test_finance_and_payroll_isolation():
    # Journal entry
    q_journal = "Jurnal penyesuaian baru untuk Order SO-2026-010"
    sc_journal = classify_action_shortcut(q_journal)
    assert sc_journal is not None
    assert sc_journal.url == "/app/finance?tab=journals&orderId=SO-2026-010"

    # Payroll entry (must NOT append orderId)
    q_payroll = "Rekap payroll mingguan gaji borongan sabtu untuk Order SO-2026-010"
    sc_payroll = classify_action_shortcut(q_payroll)
    assert sc_payroll is not None
    assert sc_payroll.url == "/app/finance?tab=payroll"
    assert "orderId" not in sc_payroll.url


def test_action_shortcut_schema_default_factory():
    sc = ActionShortcut(
        title="Test Shortcut",
        description="Test Desc",
        url="/app/test"
    )
    assert sc.id is not None
    assert len(sc.id) == 36
    # Verify valid UUID v4
    uuid_obj = uuid.UUID(sc.id, version=4)
    assert str(uuid_obj) == sc.id


def main():
    print("=" * 70)
    print("EMPIRICAL CHALLENGER IT2-2: DISAMBIGUATION & DECISION TREE SUITE")
    print("=" * 70)

    tests = [
        ("Mandatory Query 1: Warehouse Receiving (not cutting)", test_mandatory_query_1_warehouse_receiving),
        ("Mandatory Query 2: QC Inspection (not sewing tally)", test_mandatory_query_2_qc_inspection),
        ("Mandatory Query 3: Sewing Floor Terminal (LINE-02 padding)", test_mandatory_query_3_sewing_floor_terminal),
        ("Rule 1: Bare 'kain' forbidden from triggering cutting", test_bare_kain_prohibition),
        ("Rule 2: Bare 'jahit' forbidden from triggering sewing tally", test_bare_jahit_prohibition),
        ("Rule 2: Defect markers take absolute precedence over sewing tally", test_defect_precedence_over_sewing_tally),
        ("Rule 1: Receiving verbs explicitly suppress cutting", test_receiving_suppresses_cutting),
        ("Rule 1: Positive cutting action triggers cutting-record", test_cutting_positive_trigger),
        ("Extractor: Order ID boundary and digit anchor", test_entity_extractor_order_id),
        ("Extractor: Line ID boundary and 2-digit padding", test_entity_extractor_line_id),
        ("Extractor: Serial code prefix preservation and validation", test_entity_extractor_serial_code),
        ("Rule 3: Finance vs. Payroll route isolation and query parameter limits", test_finance_and_payroll_isolation),
        ("Schema: ActionShortcut auto-generates valid UUID v4 without explicit id", test_action_shortcut_schema_default_factory),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        if run_test(name, fn):
            passed += 1
        else:
            failed += 1

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests.")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
