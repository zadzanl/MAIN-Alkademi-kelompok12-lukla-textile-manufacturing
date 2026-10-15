import re
from typing import List, Optional
from .schemas import ActionShortcut

# Catalog of direct UI shortcuts corresponding to state-mutating views
SHORTCUT_ROUTES = [
    {
        "id": "cutting-record",
        "title": "Catat Hasil Pemotongan (Cutting)",
        "description": "Buka formulir input pemotongan kain dan input buangan.",
        "url_template": "/cutting/new",
        "keywords": ["potong", "cutting", "buangan", "pemotongan", "kain"],
        "icon": "scissors"
    },
    {
        "id": "sewing-tally",
        "title": "Input Hasil Jahit (Tally 30 Menit)",
        "description": "Buka form input hitungan per operator jalur jahit.",
        "url_template": "/sewing/tally",
        "keywords": ["jahit", "tally", "operator", "output", "sewing"],
        "icon": "needle"
    },
    {
        "id": "qc-inspection",
        "title": "Formulir Inspeksi QC",
        "description": "Input klasifikasi cacat (Pass, Repair, Reject).",
        "url_template": "/qc/inspect",
        "keywords": ["qc", "cacat", "defect", "inspeksi", "repair", "reject"],
        "icon": "check-circle"
    },
    {
        "id": "warehouse-receive",
        "title": "Penerimaan Bahan Baku (Warehouse)",
        "description": "Buka form pencatatan kain masuk maklon atau Snøhund.",
        "url_template": "/warehouse/receive",
        "keywords": ["terima", "gudang", "receive", "kedatangan", "kain masuk"],
        "icon": "box"
    },
    {
        "id": "ledger-entry",
        "title": "Jurnal Double-Entry Baru",
        "description": "Buka form posting jurnal akuntansi berimbang dengan idempotency key.",
        "url_template": "/ledger/transactions/new",
        "keywords": ["jurnal", "ledger", "transaksi", "reversal", "kredit", "debit"],
        "icon": "book"
    },
    {
        "id": "payroll-approval",
        "title": "Halaman Rekap Payroll Mingguan",
        "description": "Hitung dan setujui penggajian borongan Sabtu.",
        "url_template": "/payroll/weekly",
        "keywords": ["payroll", "gaji", "upah", "borongan", "uang makan", "sabtu"],
        "icon": "dollar-sign"
    }
]

def detect_action_shortcuts(user_message: str, model_reply: str) -> List[ActionShortcut]:
    """
    Detects user intent for actions and surfaces actionable UI hyperlinks.
    Ensures users can execute tasks quickly while keeping the AI assistant 100% read-only.
    """
    combined_text = f"{user_message} {model_reply}".lower()
    matched_shortcuts: List[ActionShortcut] = []

    # Attempt to extract order ID or line ID if present
    order_id_match = re.search(r"order\s*#?([a-zA-Z0-9\-]+)", combined_text)
    order_param = f"?orderId={order_id_match.group(1)}" if order_id_match else ""

    for route in SHORTCUT_ROUTES:
        if any(keyword in combined_text for keyword in route["keywords"]):
            url = f"{route['url_template']}{order_param}"
            matched_shortcuts.append(
                ActionShortcut(
                    title=route["title"],
                    description=route["description"],
                    url=url,
                    icon=route.get("icon", "external-link")
                )
            )

    return matched_shortcuts
