import re
from typing import Optional, List, Dict, Any
from .schemas import ActionShortcut

SHORTCUT_ROUTES: List[Dict[str, Any]] = [
    {
        "id": "cutting-record",
        "title": "Catat Hasil Pemotongan (Cutting)",
        "description": "Buka formulir input pemotongan kain dan input buangan.",
        "url_template": "/cutting/new",
        "icon": "scissors"
    },
    {
        "id": "sewing-tally",
        "title": "Input Hasil Jahit (Tally 30 Menit)",
        "description": "Buka form input hitungan per operator jalur jahit.",
        "url_template": "/sewing/tally",
        "icon": "needle"
    },
    {
        "id": "qc-inspection",
        "title": "Formulir Inspeksi QC",
        "description": "Input klasifikasi cacat (Pass, Repair, Reject).",
        "url_template": "/qc/inspect",
        "icon": "check-circle"
    },
    {
        "id": "warehouse-receive",
        "title": "Penerimaan Bahan Baku (Warehouse)",
        "description": "Buka form pencatatan kain masuk maklon atau Snøhund.",
        "url_template": "/warehouse/receive",
        "icon": "box"
    },
    {
        "id": "ledger-entry",
        "title": "Jurnal Double-Entry Baru",
        "description": "Buka form posting jurnal akuntansi berimbang dengan idempotency key.",
        "url_template": "/ledger/transactions/new",
        "icon": "book"
    },
    {
        "id": "payroll-approval",
        "title": "Halaman Rekap Payroll Mingguan",
        "description": "Hitung dan setujui penggajian borongan Sabtu.",
        "url_template": "/payroll/weekly",
        "icon": "dollar-sign"
    }
]

def extract_order_id(text: str) -> Optional[str]:
    """Extract order ID with word boundary and digit anchor."""
    match = re.search(r'(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    direct_match = re.search(r'\b((?:ORD|SO)-[A-Za-z0-9\-]+)\b', text, re.IGNORECASE)
    if direct_match:
        return direct_match.group(1).upper()
    return None

def extract_line_id(text: str) -> Optional[str]:
    """Extract and normalize sewing line ID."""
    match = re.search(r'\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)', text, re.IGNORECASE)
    if match:
        raw = match.group(1)
        if raw.isdigit():
            return f"LINE-{int(raw):02d}"
        if raw.upper().startswith("LINE-"):
            return raw.upper()
        return raw.upper()
    return None

def extract_serial_code(text: str) -> Optional[str]:
    """Extract assembly barcode or serial code."""
    match = re.search(r'\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', text, re.IGNORECASE)
    if match:
        return (match.group(1) or match.group(2)).upper()
    return None

def match_action_shortcut(message: str) -> Optional[ActionShortcut]:
    """
    Evaluates message intent and surfaces a single high-confidence ActionShortcut
    using word-boundary regexes and strict domain disambiguation rules.
    """
    lower = message.lower()

    # Rule 2: QC Defect reports take absolute precedence over sewing floor tallies
    is_defect = bool(re.search(r'\b(qc|cacat|defect|inspeksi|repair|reject|cacat\s+jahitan)\b', lower))
    if is_defect:
        serial = extract_serial_code(message)
        url = f"/qc/inspect?serialCode={serial}" if serial else "/qc/inspect"
        return ActionShortcut(
            title="Formulir Inspeksi QC",
            description="Input klasifikasi cacat (Pass, Repair, Reject).",
            url=url,
            icon="check-circle"
        )

    # Rule 1: Fabric Material Disambiguation (Cutting vs. Warehouse Intake)
    has_receiving = bool(re.search(r'\b(terima\s+kain|penerimaan\s+bahan|kain\s+masuk|gudang\s+bahan|receive\s+material|kedatangan\s+kain|terima|receive|masuk|gudang)\b', lower))
    has_cutting = bool(re.search(r'\b(potong\s+kain|hasil\s+potong|pemotongan\s+kain|catat\s+potong|buangan\s+kain|potong|cutting|buangan|pemotongan)\b', lower))

    if has_receiving and not has_cutting:
        return ActionShortcut(
            title="Penerimaan Bahan Baku (Warehouse)",
            description="Buka form pencatatan kain masuk maklon atau Snøhund.",
            url="/warehouse/receive",
            icon="box"
        )

    if has_cutting and not has_receiving:
        order_id = extract_order_id(message)
        url = f"/cutting/new?orderId={order_id}" if order_id else "/cutting/new"
        return ActionShortcut(
            title="Catat Hasil Pemotongan (Cutting)",
            description="Buka formulir input pemotongan kain dan input buangan.",
            url=url,
            icon="scissors"
        )

    # Sewing Floor Tally Intent
    has_sewing_tally = bool(re.search(r'\b(tally\s+jahit|input\s+tally|hasil\s+jahit|sewing\s+tally|output\s+jahit|jalur\s+jahit|tally|sewing)\b', lower))
    if has_sewing_tally:
        line_id = extract_line_id(message)
        url = f"/sewing/tally?lineId={line_id}" if line_id else "/sewing/tally"
        return ActionShortcut(
            title="Input Hasil Jahit (Tally 30 Menit)",
            description="Buka form input hitungan per operator jalur jahit.",
            url=url,
            icon="needle"
        )

    # Rule 3: Finance & Payroll Disambiguation
    has_payroll = bool(re.search(r'\b(payroll|gaji\s+borongan|upah\s+sabtu|rekap\s+payroll|penggajian|gaji|upah|borongan)\b', lower))
    if has_payroll:
        return ActionShortcut(
            title="Halaman Rekap Payroll Mingguan",
            description="Hitung dan setujui penggajian borongan Sabtu.",
            url="/payroll/weekly",
            icon="dollar-sign"
        )

    has_ledger = bool(re.search(r'\b(jurnal|ledger|transaksi\s+baru|jurnal\s+penyesuaian|posting\s+jurnal)\b', lower))
    if has_ledger:
        return ActionShortcut(
            title="Jurnal Double-Entry Baru",
            description="Buka form posting jurnal akuntansi berimbang dengan idempotency key.",
            url="/ledger/transactions/new",
            icon="book"
        )

    # If fabric was mentioned with receiving verbs as fallback
    if has_receiving:
        return ActionShortcut(
            title="Penerimaan Bahan Baku (Warehouse)",
            description="Buka form pencatatan kain masuk maklon atau Snøhund.",
            url="/warehouse/receive",
            icon="box"
        )

    return None

def match_action_shortcuts(message: str) -> List[ActionShortcut]:
    """Helper returning a list of ActionShortcuts."""
    shortcut = match_action_shortcut(message)
    return [shortcut] if shortcut else []
