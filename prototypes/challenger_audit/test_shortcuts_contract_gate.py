#!/usr/bin/env python3
"""
Empirical Verification Test Harness: Action Shortcuts, Route Correctness & Contract Blueprint Gate
Challenger Gate Iteration 1 for `ai-ops-copilot-scaffold`

Validates:
1. Action Shortcut Regex Precision & Disambiguation:
   - Order ID extraction: "Order SO-2026-001", "order #1234", "Order-5678", uppercase normalization.
   - Negative lookbehinds: "(?<!\\bin\\s)\\border" rejecting English idioms ("in order to fix", "in order to check") and word boundary rejects ("reorder kain", "border 12").
   - Line ID extraction & two-digit padding: "line 1" -> "LINE-01", "jalur 2" -> "LINE-02", "line 4" -> "LINE-04", "jalur #5" -> "LINE-05", "line 14" -> "LINE-14". Rejection of "online now", "guideline 2".
   - Serial code extraction: "ASM-2026-001", "SN-9999", "barcode: 12345", "barcode #5544", "serial: 778899". Rejection of "serials in process".
   - Bare keyword suppression: Bare "kain" does NOT trigger cutting; bare "jahit" does NOT trigger sewing tally.
   - Disambiguation precedence:
     * "terima kain" triggers receiving, NOT cutting.
     * Receiving verbs ("terima", "receive", "masuk", "kedatangan") suppress cutting even if "potong" is mentioned.
     * Defect markers ("cacat", "defect", "repair", "reject", "inspeksi", "qc") take absolute precedence over sewing tally even if containing "jahit"/"jahitan".
     * "cacat jahit" triggers QC defect (/app/quality), NOT sewing tally.
   - Canonical route mapping to VIEW-01 through VIEW-06:
     * VIEW-01 Operations Dashboard (/app/overview)
     * VIEW-02 Sample & Tech Pack (/app/samples)
     * VIEW-03 Warehouse & Cutting (/app/materials?action=cutting | ?action=receive)
     * VIEW-04 Sewing Floor Terminal (/terminal/tally)
     * VIEW-05 QC Station (/app/quality)
     * VIEW-06 Finance & Ledger (/app/finance?tab=journals | ?tab=payroll)
   - Dynamic UUID v4 generation on ActionShortcut (default_factory=uuid4).
   - Parameter isolation (e.g. payroll approval does NOT append orderId).

2. Delta OpenAPI 3.1 Contract Blueprint Validation:
   - Validates contracts/copilot-openapi.yaml via validate-blueprint.py (exit code 0, CUSTOM_CONTRACT_CHECKS=PASS).
   - Schema adherence for ChatTurnRequest, ChatTurnResponse, ActionShortcut, and Problem (including GATEWAY_TIMEOUT enum).
   - Negative schema controls: invalid payloads, out-of-range bounds, malformed UUIDs, unknown error codes.
   - Blueprint negative control: tampered contract rejected.
"""

import copy
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional
import uuid

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import BaseModel, Field
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012


# ==============================================================================
# SECTION 1: Action Shortcut Domain Implementation & Regex Engine
# ==============================================================================

class ActionShortcut(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    url: str
    icon: str
    prefill_params: Optional[Dict[str, Any]] = None


# Entity extraction regular expressions per design.md §4 and spec.md §3
ORDER_REGEX = re.compile(
    r'(?<!\bin\s)\border[-:\s#]*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)',
    re.IGNORECASE
)
LINE_REGEX = re.compile(
    r'\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)',
    re.IGNORECASE
)
SERIAL_REGEX = re.compile(
    r'\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)',
    re.IGNORECASE
)
PERIOD_REGEX = re.compile(
    r'\b(?:period|periode)\s*#?\s*([A-Za-z0-9\-]+)|\b(\d{4}-W\d{2})\b',
    re.IGNORECASE
)

# Canonical keywords & exclusion markers per design.md Table 4
CUTTING_KEYWORDS = [
    "potong kain", "hasil potong", "cutting", "pemotongan kain",
    "catat potong", "buangan kain"
]
RECEIVING_KEYWORDS = [
    "terima kain", "penerimaan bahan", "kain masuk", "gudang bahan",
    "receive material", "kedatangan kain"
]
RECEIVING_SUPPRESSION_VERBS = ["terima", "receive", "masuk", "kedatangan"]
CUTTING_SUPPRESSION_VERBS = ["potong", "cutting", "buangan"]

SEWING_TALLY_KEYWORDS = [
    "tally", "tally jahit", "input tally", "hasil jahit",
    "sewing tally", "output jahit", "jalur jahit"
]
DEFECT_QC_MARKERS = ["cacat", "defect", "repair", "reject", "inspeksi", "qc"]
QC_KEYWORDS = ["qc", "cacat", "defect", "inspeksi qc", "repair", "reject", "cacat jahitan"]

JOURNAL_KEYWORDS = ["jurnal", "ledger", "transaksi baru", "jurnal penyesuaian", "posting jurnal"]
PAYROLL_KEYWORDS = ["payroll", "gaji borongan", "upah sabtu", "rekap payroll", "penggajian"]
ORDER_ACTION_KEYWORDS = ["konfirmasi order", "batal order", "order baru", "pesanan baru", "buat order"]
SAMPLE_TRACKER_KEYWORDS = ["buat sample", "revisi sample", "setujui sample", "input time study", "tech pack"]


def extract_entities(text: str) -> Dict[str, Optional[str]]:
    """Extract and normalize operational entities from prompt text."""
    # 1. Order ID
    m_order = ORDER_REGEX.search(text)
    order_id = None
    if m_order:
        raw_order = m_order.group(1).lstrip("-#: ").strip()
        if raw_order:
            order_id = raw_order.upper()

    # 2. Line ID
    m_line = LINE_REGEX.search(text)
    line_id = None
    if m_line:
        raw_line = m_line.group(1).lstrip("#: ").strip()
        if raw_line.isdigit():
            line_id = f"LINE-{int(raw_line):02d}"
        else:
            line_id = raw_line.upper()

    # 3. Serial Code
    m_serial = SERIAL_REGEX.search(text)
    serial_code = None
    if m_serial:
        raw_serial = m_serial.group(1) or m_serial.group(2)
        if raw_serial:
            serial_code = raw_serial.lstrip("-:# ").strip().upper()

    # 4. Period ID
    m_period = PERIOD_REGEX.search(text)
    period_id = None
    if m_period:
        raw_period = m_period.group(1) or m_period.group(2)
        if raw_period:
            period_id = raw_period.lstrip("-:# ").strip().upper()

    return {
        "orderId": order_id,
        "lineId": line_id,
        "serialCode": serial_code,
        "periodId": period_id,
    }


def classify_action_shortcut(raw_text: str) -> Optional[ActionShortcut]:
    """
    Deterministic intent classification & parameter binding.
    Returns pre-filled ActionShortcut or None if purely conversational/read query.
    """
    text_lower = raw_text.lower()
    entities = extract_entities(raw_text)

    # ------------------------------------------------------------------
    # RULE 2: SEWING VS. QC DEFECT DISAMBIGUATION
    # Defect markers take absolute precedence over sewing tally even if containing 'jahit'/'jahitan'
    # ------------------------------------------------------------------
    has_defect_marker = any(marker in text_lower for marker in DEFECT_QC_MARKERS)
    if has_defect_marker and any(kw in text_lower for kw in QC_KEYWORDS):
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
            icon="alert-triangle",
            prefill_params={"serialCode": entities["serialCode"], "orderId": entities["orderId"]}
        )

    # If no defect markers, evaluate sewing tally
    has_sewing_tally_kw = any(kw in text_lower for kw in SEWING_TALLY_KEYWORDS)
    # Standalone 'jahit' without tally phrase is suppressed
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
            icon="clipboard-list",
            prefill_params={"lineId": entities["lineId"], "orderId": entities["orderId"]}
        )

    # ------------------------------------------------------------------
    # RULE 1: FABRIC MATERIAL DISAMBIGUATION (Cutting vs. Warehouse Intake)
    # ------------------------------------------------------------------
    has_receiving_kw = any(kw in text_lower for kw in RECEIVING_KEYWORDS)
    has_receiving_suppression = any(verb in text_lower for verb in RECEIVING_SUPPRESSION_VERBS)
    has_cutting_kw = any(kw in text_lower for kw in CUTTING_KEYWORDS)

    # Standalone 'kain' is forbidden from triggering cutting
    if has_receiving_kw or (has_receiving_suppression and "kain" in text_lower):
        order_qs = f"?orderId={entities['orderId']}" if entities["orderId"] else ""
        return ActionShortcut(
            title="Penerimaan Bahan Baku (Warehouse)",
            description="Buka form pencatatan kain masuk maklon atau Snøhund.",
            url=f"/app/materials?action=receive{('&' + order_qs[1:]) if order_qs else ''}",
            icon="package",
            prefill_params={"orderId": entities["orderId"]}
        )

    if has_cutting_kw and not has_receiving_suppression:
        order_qs = f"?orderId={entities['orderId']}" if entities["orderId"] else ""
        return ActionShortcut(
            title="Catat Hasil Pemotongan (Cutting)",
            description="Buka formulir input pemotongan kain dan input buangan.",
            url=f"/app/materials?action=cutting{('&' + order_qs[1:]) if order_qs else ''}",
            icon="scissors",
            prefill_params={"orderId": entities["orderId"]}
        )

    # ------------------------------------------------------------------
    # RULE 3: FINANCE & LEDGER DISAMBIGUATION
    # ------------------------------------------------------------------
    has_payroll_kw = any(kw in text_lower for kw in PAYROLL_KEYWORDS)
    if has_payroll_kw:
        period_qs = f"&periodId={entities['periodId']}" if entities["periodId"] else ""
        return ActionShortcut(
            title="Halaman Rekap Payroll Mingguan",
            description="Hitung dan setujui penggajian borongan Sabtu.",
            url=f"/app/finance?tab=payroll{period_qs}",
            icon="dollar-sign",
            prefill_params={"periodId": entities["periodId"]}
        )

    has_journal_kw = any(kw in text_lower for kw in JOURNAL_KEYWORDS)
    if has_journal_kw:
        order_qs = f"&orderId={entities['orderId']}" if entities["orderId"] else ""
        return ActionShortcut(
            title="Jurnal Double-Entry Baru",
            description="Buka form posting jurnal akuntansi berimbang dengan idempotency key.",
            url=f"/app/finance?tab=journals{order_qs}",
            icon="book-open",
            prefill_params={"orderId": entities["orderId"]}
        )

    # ------------------------------------------------------------------
    # RULE 4: ORDER LIFECYCLE & SAMPLE TRACKER
    # ------------------------------------------------------------------
    has_order_action_kw = any(kw in text_lower for kw in ORDER_ACTION_KEYWORDS)
    if has_order_action_kw:
        order_qs = f"?orderId={entities['orderId']}" if entities["orderId"] else ""
        return ActionShortcut(
            title="Manajemen Pesanan (Order Action)",
            description="Buka form tindakan pesanan konfirmasi atau pembatalan.",
            url=f"/app/overview{order_qs}",
            icon="file-text",
            prefill_params={"orderId": entities["orderId"]}
        )

    has_sample_kw = any(kw in text_lower for kw in SAMPLE_TRACKER_KEYWORDS)
    if has_sample_kw:
        return ActionShortcut(
            title="Pelacak Sample & Tech Pack",
            description="Buka form pembuatan atau revisi sample dan time study.",
            url="/app/samples",
            icon="layers",
            prefill_params=None
        )

    return None


# ==============================================================================
# SECTION 2: Empirical Test Cases
# ==============================================================================

CANONICAL_VIEW_ROUTES = {
    "VIEW-01": "/app/overview",
    "VIEW-02": "/app/samples",
    "VIEW-03": "/app/materials",
    "VIEW-04": "/terminal/tally",
    "VIEW-05": "/app/quality",
    "VIEW-06": "/app/finance",
}


# --- Suite 1: Regex Precision, Extraction & Disambiguation ---

def test_order_id_regex_precision():
    """Verify Order ID extraction across formats and uppercase normalization."""
    # 1. "Order SO-2026-001"
    e1 = extract_entities("Order SO-2026-001")
    assert e1["orderId"] == "SO-2026-001", f"Expected SO-2026-001, got {e1['orderId']}"

    # 2. "order #1234"
    e2 = extract_entities("tolong cek pesanan order #1234 sekarang")
    assert e2["orderId"] == "1234", f"Expected 1234, got {e2['orderId']}"

    # 3. "Order-5678"
    e3 = extract_entities("proses Order-5678 segera")
    assert e3["orderId"] == "5678", f"Expected 5678, got {e3['orderId']}"

    # 4. Mixed case lowercase normalization
    e4 = extract_entities("order so-2026-xyz9")
    assert e4["orderId"] == "SO-2026-XYZ9", f"Expected uppercase SO-2026-XYZ9, got {e4['orderId']}"


def test_order_id_negative_lookbehinds_and_boundaries():
    """Verify negative lookbehinds (?<!\\bin\\s) and word boundary rejections."""
    # 1. "in order to fix" - English idiom must NOT match
    assert extract_entities("In order to fix the needle, stop the machine.")["orderId"] is None
    assert extract_entities("in order to check inventory")["orderId"] is None

    # 2. "reorder kain" - Word boundary failure on 'reorder'
    assert extract_entities("Tolong reorder kain katun untuk gudang")["orderId"] is None

    # 3. "border 12" - Word boundary failure on 'border'
    assert extract_entities("Periksa border 12 pada pola pakaian")["orderId"] is None

    # 4. Standalone "order" without digit anchor
    assert extract_entities("Tolong buatkan order baru tanpa nomor")["orderId"] is None


def test_line_id_extraction_and_two_digit_padding():
    """Verify Line ID extraction, numeric two-digit padding, and boundary safety."""
    # "line 1" -> "LINE-01"
    assert extract_entities("Input tally line 1")["lineId"] == "LINE-01"

    # "jalur 2" -> "LINE-02"
    assert extract_entities("Jalur 2 selesai 50 pcs")["lineId"] == "LINE-02"

    # "line 4" -> "LINE-04"
    assert extract_entities("Pemeriksaan line 4")["lineId"] == "LINE-04"

    # "jalur #5" -> "LINE-05"
    assert extract_entities("Input jalur #5")["lineId"] == "LINE-05"

    # "line 14" -> "LINE-14" (double digit remains intact)
    assert extract_entities("Line 14 target tercapai")["lineId"] == "LINE-14"

    # Non-digit line identifiers
    assert extract_entities("Line LINE-03")["lineId"] == "LINE-03"

    # Negative checks: boundary safety
    assert extract_entities("User is online now")["lineId"] is None
    assert extract_entities("Read the guideline 2 carefully")["lineId"] is None


def test_serial_code_extraction():
    """Verify Garment Assembly serial code and barcode extraction."""
    # "ASM-2026-001"
    assert extract_entities("Cacat pada barcode ASM-2026-001")["serialCode"] == "ASM-2026-001"

    # "SN-9999"
    assert extract_entities("Periksa unit SN-9999 di QC")["serialCode"] == "SN-9999"

    # "barcode: 12345"
    assert extract_entities("Pindai barcode: 12345")["serialCode"] == "12345"

    # "barcode #5544"
    assert extract_entities("Hasil scan barcode #5544")["serialCode"] == "5544"

    # "serial: 778899"
    assert extract_entities("Defect pada serial: 778899")["serialCode"] == "778899"

    # Negative check
    assert extract_entities("Several serials in process")["serialCode"] is None


def test_bare_keyword_suppression():
    """Verify standalone 'kain' and 'jahit' never trigger shortcuts."""
    # Bare 'kain' alone must NOT trigger cutting
    sc_kain = classify_action_shortcut("Berapa sisa stok kain katun di gudang?")
    assert sc_kain is None or "action=cutting" not in sc_kain.url, "Bare 'kain' triggered cutting!"

    # Bare 'jahit' alone must NOT trigger sewing tally
    sc_jahit = classify_action_shortcut("Berapa banyak operator jahit yang hadir hari ini?")
    assert sc_jahit is None, f"Bare 'jahit' triggered shortcut: {sc_jahit}"


def test_fabric_material_disambiguation_receiving_vs_cutting():
    """Verify receiving verbs suppress cutting and trigger warehouse intake."""
    # "terima kain" triggers receiving
    sc1 = classify_action_shortcut("Terima kain di gudang bahan untuk Order SO-2026-001")
    assert sc1 is not None
    assert "/app/materials?action=receive" in sc1.url
    assert "action=cutting" not in sc1.url
    assert "orderId=SO-2026-001" in sc1.url
    assert sc1.icon == "package"

    # Receiving verb ("masuk", "terima") explicitly suppresses cutting when both appear
    sc2 = classify_action_shortcut("Kain drill sudah masuk, tolong potong kain untuk Order SO-2026-002 tapi terima kain dulu")
    assert sc2 is not None
    assert "/app/materials?action=receive" in sc2.url
    assert "action=cutting" not in sc2.url

    # Unambiguous cutting action
    sc3 = classify_action_shortcut("Catat hasil potong 500 pcs untuk Order SO-2026-003")
    assert sc3 is not None
    assert sc3.url == "/app/materials?action=cutting&orderId=SO-2026-003"
    assert sc3.icon == "scissors"


def test_defect_precedence_over_sewing_tally():
    """Verify defect markers take absolute precedence over sewing tally even with 'jahit'."""
    # Query contains 'jahit' / 'jahitan' AND defect marker 'cacat' -> MUST route to /app/quality
    sc1 = classify_action_shortcut("Ada cacat jahit pada jalur 2 barcode ASM-2026-001 order SO-2026-001")
    assert sc1 is not None
    assert sc1.url.startswith("/app/quality"), f"Expected /app/quality, got: {sc1.url}"
    assert "/terminal/tally" not in sc1.url
    assert "serialCode=ASM-2026-001" in sc1.url
    assert "orderId=SO-2026-001" in sc1.url
    assert sc1.icon == "alert-triangle"

    # Query with 'inspeksi qc' and 'cacat jahitan'
    sc2 = classify_action_shortcut("Inspeksi QC ada cacat jahitan pada barcode ASM-8910")
    assert sc2 is not None
    assert sc2.url == "/app/quality?serialCode=ASM-8910"
    assert sc2.icon == "alert-triangle"

    # Unambiguous sewing tally
    sc3 = classify_action_shortcut("Input tally jahit 30 menit line 2 order SO-2026-008")
    assert sc3 is not None
    assert sc3.url == "/terminal/tally?lineId=LINE-02&orderId=SO-2026-008"
    assert sc3.icon == "clipboard-list"


def test_canonical_route_mapping_view01_to_view06():
    """Verify that all Action Shortcut targets map strictly to VIEW-01 through VIEW-06."""
    test_cases = [
        ("VIEW-01 (Confirm)", "Konfirmasi order SO-2026-001", "/app/overview?orderId=SO-2026-001", "file-text"),
        ("VIEW-01 (Create)", "Buat order baru untuk klien", "/app/overview", "file-text"),
        ("VIEW-02", "Buat sample baru untuk kemeja katun", "/app/samples", "layers"),
        ("VIEW-03 (Cutting)", "Catat hasil potong kain Order SO-2026-005", "/app/materials?action=cutting&orderId=SO-2026-005", "scissors"),
        ("VIEW-03 (Receive)", "Terima kain masuk untuk Order SO-2026-006", "/app/materials?action=receive&orderId=SO-2026-006", "package"),
        ("VIEW-04", "Input hasil jahit tally line 3", "/terminal/tally?lineId=LINE-03", "clipboard-list"),
        ("VIEW-05", "QC defect ada cacat pada barcode ASM-007", "/app/quality?serialCode=ASM-007", "alert-triangle"),
        ("VIEW-06 (Journal)", "Posting jurnal penyesuaian Order SO-2026-009", "/app/finance?tab=journals&orderId=SO-2026-009", "book-open"),
        ("VIEW-06 (Payroll)", "Rekap payroll mingguan upah sabtu", "/app/finance?tab=payroll", "dollar-sign"),
    ]

    for view_label, query, expected_url, expected_icon in test_cases:
        shortcut = classify_action_shortcut(query)
        assert shortcut is not None, f"Failed to classify shortcut for {view_label}: '{query}'"
        assert shortcut.url == expected_url, f"{view_label} URL mismatch: expected {expected_url}, got {shortcut.url}"
        assert shortcut.icon == expected_icon, f"{view_label} Icon mismatch: expected {expected_icon}, got {shortcut.icon}"

        # Verify base path maps to one of canonical VIEW-01..VIEW-06 routes
        base_path = shortcut.url.split("?")[0]
        assert base_path in CANONICAL_VIEW_ROUTES.values(), f"Base path {base_path} not in VIEW-01..VIEW-06 routes!"


def test_action_shortcut_schema_uuid_and_isolation():
    """Verify ActionShortcut auto-generates dynamic UUID v4 and parameter isolation."""
    sc1 = ActionShortcut(
        title="Shortcut 1",
        description="Desc 1",
        url="/app/materials?action=cutting",
        icon="scissors"
    )
    sc2 = ActionShortcut(
        title="Shortcut 2",
        description="Desc 2",
        url="/app/materials?action=cutting",
        icon="scissors"
    )
    # Check distinct dynamic UUIDs
    assert sc1.id != sc2.id, "UUIDs must be distinct across instances"
    uuid1 = uuid.UUID(sc1.id, version=4)
    uuid2 = uuid.UUID(sc2.id, version=4)
    assert str(uuid1) == sc1.id
    assert str(uuid2) == sc2.id

    # Check payroll parameter isolation (must not leak orderId)
    sc_payroll = classify_action_shortcut("Rekap payroll mingguan gaji borongan sabtu untuk Order SO-2026-010")
    assert sc_payroll is not None
    assert "orderId" not in sc_payroll.url, f"OrderId leaked into payroll url: {sc_payroll.url}"


# --- Suite 2: OpenAPI 3.1 Contract Blueprint Validation ---

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACT_PATH = REPO_ROOT / "openspec" / "changes" / "ai-ops-copilot-scaffold" / "contracts" / "copilot-openapi.yaml"
VALIDATOR_SCRIPT = REPO_ROOT / "openspec" / "changes" / "lukla-ops-engine-planning" / "validate-blueprint.py"


def test_contract_blueprint_validation_via_script():
    """Verify copilot-openapi.yaml passes validate-blueprint.py with exit code 0."""
    assert CONTRACT_PATH.exists(), f"Contract file not found at {CONTRACT_PATH}"
    assert VALIDATOR_SCRIPT.exists(), f"Validator script not found at {VALIDATOR_SCRIPT}"

    res = subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT), str(CONTRACT_PATH)],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0, f"validate-blueprint.py failed with code {res.returncode}:\n{res.stderr}\n{res.stdout}"
    assert "CUSTOM_CONTRACT_CHECKS=PASS" in res.stdout, f"Expected PASS confirmation in output:\n{res.stdout}"


def test_contract_metadata_and_operations():
    """Verify OpenAPI 3.1 structure, security, operationId, 8-role mapping, and HTTP error envelopes."""
    raw_yaml = CONTRACT_PATH.read_text(encoding="utf-8")
    doc = yaml.safe_load(raw_yaml)

    assert doc.get("openapi") == "3.1.0", f"Expected OpenAPI 3.1.0, got {doc.get('openapi')}"
    paths = doc.get("paths", {})
    assert "/api/v1/copilot/chat" in paths, "Missing /api/v1/copilot/chat endpoint"

    chat_op = paths["/api/v1/copilot/chat"].get("post", {})
    assert chat_op.get("operationId") == "submitCopilotChatTurn", f"Wrong operationId: {chat_op.get('operationId')}"

    # Verify 8 roles are declared in x-roles
    expected_roles = {
        "Owner", "SampleTeam", "Warehouse", "ProductionHead",
        "Tailor", "QCInspector", "FinancePayroll", "MaklonClient"
    }
    roles = set(chat_op.get("x-roles", []))
    assert expected_roles.issubset(roles), f"Missing roles in x-roles: {expected_roles - roles}"

    # Verify x-invariant mentions read-only policy
    invariant = chat_op.get("x-invariant", "")
    assert "read-only" in invariant.lower() or "forbidden" in invariant.lower()

    # Verify response codes 200, 400, 401, 403, 422, 504
    responses = chat_op.get("responses", {})
    for code in ["200", "400", "401", "403", "422", "504"]:
        assert code in responses, f"Missing HTTP {code} response binding"


def _build_validator(doc: Dict[str, Any], schema_pointer: str) -> Draft202012Validator:
    uri = "urn:lukla:copilot"
    registry = Registry().with_resource(
        uri, Resource.from_contents(doc, default_specification=DRAFT202012)
    )
    return Draft202012Validator(
        {"$ref": f"{uri}#{schema_pointer}"}, registry=registry, format_checker=FormatChecker()
    )


def test_chat_turn_request_schema():
    """Verify ChatTurnRequest positive acceptance and negative boundary rejection."""
    raw_yaml = CONTRACT_PATH.read_text(encoding="utf-8")
    doc = yaml.safe_load(raw_yaml)
    v = _build_validator(doc, "/components/schemas/ChatTurnRequest")

    # Positive: valid request
    valid_req = {
        "message": "Berapa stok kain katun?",
        "history": [
            {"role": "user", "content": "Halo"},
            {"role": "assistant", "content": "Halo! Ada yang bisa saya bantu?"}
        ],
        "stream": False,
        "sessionId": "a0000000-0000-4000-8000-000000000001"
    }
    assert v.is_valid(valid_req), f"Valid ChatTurnRequest was rejected: {list(v.iter_errors(valid_req))}"

    # Negative 1: Missing required 'message'
    assert not v.is_valid({"stream": False})

    # Negative 2: Message length < 1 (empty string)
    assert not v.is_valid({"message": ""})

    # Negative 3: Message length > 4000 characters
    long_msg = "A" * 4001
    assert not v.is_valid({"message": long_msg})

    # Negative 4: History > 10 items (maxItems: 10)
    oversized_history = [{"role": "user", "content": f"msg {i}"} for i in range(11)]
    assert not v.is_valid({"message": "Test", "history": oversized_history})

    # Negative 5: Invalid role in ChatMessage
    bad_role_history = [{"role": "superadmin", "content": "hello"}]
    assert not v.is_valid({"message": "Test", "history": bad_role_history})


def test_chat_turn_response_schema():
    """Verify ChatTurnResponse positive acceptance and negative boundary rejection."""
    raw_yaml = CONTRACT_PATH.read_text(encoding="utf-8")
    doc = yaml.safe_load(raw_yaml)
    v = _build_validator(doc, "/components/schemas/ChatTurnResponse")

    valid_resp = {
        "sessionId": "a0000000-0000-4000-8000-000000000001",
        "reply": "Stok kain tersedia 1.250 meter.",
        "shortcuts": [
            {
                "id": "b0000000-0000-4000-8000-000000000001",
                "title": "Catat Cutting",
                "description": "Buka formulir cutting",
                "url": "/app/materials?action=cutting",
                "icon": "scissors"
            }
        ],
        "toolsUsed": ["getStock"],
        "usage": {
            "promptTokens": 450,
            "completionTokens": 55,
            "totalTokens": 505
        }
    }
    assert v.is_valid(valid_resp), f"Valid ChatTurnResponse rejected: {list(v.iter_errors(valid_resp))}"

    # Negative 1: Missing required sessionId
    bad_resp = copy.deepcopy(valid_resp)
    del bad_resp["sessionId"]
    assert not v.is_valid(bad_resp)

    # Negative 2: Malformed UUID in sessionId
    bad_resp2 = copy.deepcopy(valid_resp)
    bad_resp2["sessionId"] = "not-a-uuid"
    assert not v.is_valid(bad_resp2)

    # Negative 3: Missing required usage
    bad_resp3 = copy.deepcopy(valid_resp)
    del bad_resp3["usage"]
    assert not v.is_valid(bad_resp3)


def test_problem_schema_and_gateway_timeout_enum():
    """Verify RFC 7807 Problem schema binding, including GATEWAY_TIMEOUT enum value."""
    raw_yaml = CONTRACT_PATH.read_text(encoding="utf-8")
    doc = yaml.safe_load(raw_yaml)
    v = _build_validator(doc, "/components/schemas/Problem")

    # Positive 1: 504 GATEWAY_TIMEOUT Problem payload
    valid_504 = {
        "type": "https://api.lukla.invalid/errors/gateway-timeout",
        "title": "Gateway Timeout",
        "status": 504,
        "code": "GATEWAY_TIMEOUT",
        "detail": "Downstream LLM inference provider timed out after 15.0 seconds.",
        "instance": "/api/v1/copilot/chat",
        "requestId": "c0000000-0000-4000-8000-000000000005",
        "violations": []
    }
    assert v.is_valid(valid_504), f"Valid 504 Problem rejected: {list(v.iter_errors(valid_504))}"

    # Positive 2: 403 FORBIDDEN Problem payload
    valid_403 = {
        "type": "https://api.lukla.invalid/errors/forbidden",
        "title": "Forbidden",
        "status": 403,
        "code": "FORBIDDEN",
        "detail": "Execution of mutating method 'POST' is blocked by security policy.",
        "instance": "/api/v1/copilot/chat",
        "requestId": "c0000000-0000-4000-8000-000000000003",
        "violations": []
    }
    assert v.is_valid(valid_403), f"Valid 403 Problem rejected: {list(v.iter_errors(valid_403))}"

    # Negative 1: Unknown code enum
    bad_problem = copy.deepcopy(valid_504)
    bad_problem["code"] = "UNRECOGNIZED_CUSTOM_ERROR"
    assert not v.is_valid(bad_problem), "Problem schema accepted an invalid code enum"

    # Negative 2: Status out of range (< 400)
    bad_status = copy.deepcopy(valid_504)
    bad_status["status"] = 200
    assert not v.is_valid(bad_status), "Problem schema accepted status 200"

    # Negative 3: Missing requestId
    bad_req_id = copy.deepcopy(valid_504)
    del bad_req_id["requestId"]
    assert not v.is_valid(bad_req_id), "Problem schema accepted missing requestId"


def test_blueprint_negative_controls():
    """Verify blueprint validator detects synthetic corruptions."""
    raw_yaml = CONTRACT_PATH.read_text(encoding="utf-8")
    doc = yaml.safe_load(raw_yaml)

    # 1. Negative control: broken reference
    broken_doc = copy.deepcopy(doc)
    broken_doc["components"]["schemas"]["BrokenRef"] = {"$ref": "#/missing/schema"}
    broken_yaml = yaml.dump(broken_doc)

    tmp_path = REPO_ROOT / "prototypes" / "challenger_audit" / "_temp_broken_contract.yaml"
    try:
        tmp_path.write_text(broken_yaml, encoding="utf-8")
        res = subprocess.run(
            [sys.executable, str(VALIDATOR_SCRIPT), str(tmp_path)],
            capture_output=True,
            text=True
        )
        assert res.returncode != 0, "Validator failed to detect broken reference in negative control"
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


# ==============================================================================
# SECTION 3: Main Test Runner
# ==============================================================================

def run_test(name: str, fn) -> bool:
    print(f"[*] Running: {name} ...", end=" ")
    try:
        fn()
        print("✅ PASS")
        return True
    except AssertionError as e:
        print(f"❌ FAIL: {e}")
        return False
    except Exception as e:
        print(f"💥 ERROR: {type(e).__name__}: {e}")
        return False


def main():
    print("=" * 75)
    print("CHALLENGER GATE ITERATION 1: REGEX, ROUTING & CONTRACT TEST SUITE")
    print("Specification: ai-ops-copilot-scaffold")
    print("=" * 75)

    tests = [
        # Suite 1: Regex Precision, Extraction & Disambiguation
        ("1.1 Order ID Extraction Precision (SO-2026-001, #1234, -5678)", test_order_id_regex_precision),
        ("1.2 Negative Lookbehind & Word Boundaries (in order to, reorder, border)", test_order_id_negative_lookbehinds_and_boundaries),
        ("1.3 Line ID Extraction & Two-Digit Padding (LINE-01, LINE-02, line 14)", test_line_id_extraction_and_two_digit_padding),
        ("1.4 Serial Code Extraction (ASM-2026-001, SN-9999, barcode: 12345)", test_serial_code_extraction),
        ("1.5 Bare Keyword Suppression (standalone 'kain' & 'jahit' rejected)", test_bare_keyword_suppression),
        ("1.6 Fabric Material Disambiguation (receiving suppresses cutting)", test_fabric_material_disambiguation_receiving_vs_cutting),
        ("1.7 Defect Precedence Over Sewing Tally ('cacat jahit' -> /app/quality)", test_defect_precedence_over_sewing_tally),
        ("1.8 Canonical Route Mapping across VIEW-01 through VIEW-06", test_canonical_route_mapping_view01_to_view06),
        ("1.9 ActionShortcut Dynamic UUID v4 Generation & Parameter Isolation", test_action_shortcut_schema_uuid_and_isolation),

        # Suite 2: OpenAPI 3.1 Blueprint & Schema Validation
        ("2.1 Contract Blueprint Validation via validate-blueprint.py (Exit 0)", test_contract_blueprint_validation_via_script),
        ("2.2 OpenAPI 3.1 Operation, Security, 8-Role Mapping & Status Envelopes", test_contract_metadata_and_operations),
        ("2.3 ChatTurnRequest Schema Boundaries (minLength, maxLength, maxItems)", test_chat_turn_request_schema),
        ("2.4 ChatTurnResponse Schema Compliance & Token Usage", test_chat_turn_response_schema),
        ("2.5 Problem RFC 7807 Schema & GATEWAY_TIMEOUT Enum Adherence", test_problem_schema_and_gateway_timeout_enum),
        ("2.6 Blueprint Validator Negative Control (Corrupted Reference Detected)", test_blueprint_negative_controls),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        if run_test(name, fn):
            passed += 1
        else:
            failed += 1

    print("=" * 75)
    print(f"Summary: {passed} passed, {failed} failed out of {len(tests)} tests.")
    print("=" * 75)

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
