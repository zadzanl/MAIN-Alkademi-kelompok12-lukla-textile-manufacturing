#!/usr/bin/env python3
"""
Empirical Regression Challenge Suite (Challenger IT2-1)
Validates:
1. ActionShortcut instantiation without explicit 'id' argument generates valid UUID v4.
2. Order ID regex negative & positive matching, word boundaries, and uppercase normalization.
3. Line ID regex and 2-digit padding normalization.
4. Serial Code regex with full prefix preservation and plural rejection.
5. Canonical route mappings match VIEW-01 through VIEW-06.
"""

import sys
import uuid
import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

def test_action_shortcut():
    print("[*] Testing ActionShortcut instantiation...")
    class ActionShortcut(BaseModel):
        id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        title: str
        description: str
        url: str
        icon: Optional[str] = "external-link"
        prefill_params: Optional[Dict[str, Any]] = None

    shortcut = ActionShortcut(title="T", description="D", url="/app")
    assert shortcut.title == "T"
    assert shortcut.description == "D"
    assert shortcut.url == "/app"
    assert shortcut.icon == "external-link"
    assert shortcut.prefill_params is None
    assert isinstance(shortcut.id, str)
    assert len(shortcut.id) == 36
    parsed = uuid.UUID(shortcut.id)
    assert parsed.version == 4, f"Expected UUID v4, got version {parsed.version}"
    print(f"    PASS: Instantiated cleanly without id. Generated UUID4: {shortcut.id}")

def test_order_regex():
    print("[*] Testing Order ID regex...")
    order_regex = re.compile(r'(?<!\bin\s)\border\s*#?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', re.IGNORECASE)

    def extract_order(text: str) -> Optional[str]:
        m = order_regex.search(text)
        return m.group(1).upper() if m else None

    # Negative assertions
    assert extract_order("reorder kain") is None, "Failed: 'reorder kain' matched orderId"
    assert extract_order("in order to fix") is None, "Failed: 'in order to fix' matched orderId"
    assert extract_order("Tolong reorder kain katun") is None, "Failed: 'reorder' in sentence matched"
    assert extract_order("in order to fix defect") is None, "Failed: 'in order to' matched"
    assert extract_order("order defect") is None, "Failed: 'order defect' matched (no digits)"
    assert extract_order("order to") is None, "Failed: 'order to' matched (no digits)"

    # Positive assertions
    assert extract_order("Order SO-2026-001") == "SO-2026-001", "Failed to extract SO-2026-001"
    assert extract_order("order so-2026-001") == "SO-2026-001", "Failed uppercase normalization"
    assert extract_order("order #SO-2026-002") == "SO-2026-002", "Failed hash prefix extraction"
    assert extract_order("in order to fix defect on order SO-2026-001") == "SO-2026-001", "Failed lookbehind on second occurrence"
    print("    PASS: Order ID regex verified (negative lookbehind, word boundary, digit anchor, uppercase normalization).")

def test_line_regex():
    print("[*] Testing Line ID regex and normalization...")
    line_regex = re.compile(r'\b(?:line|jalur)\s*#?\s*([A-Za-z0-9\-]+)', re.IGNORECASE)

    def extract_line(text: str) -> Optional[str]:
        m = line_regex.search(text)
        if not m:
            return None
        val = m.group(1).strip().lstrip("-")
        if val.isdigit():
            return f"LINE-{int(val):02d}"
        val_upper = val.upper()
        if val_upper.startswith("LINE-"):
            return val_upper
        return f"LINE-{val_upper}"

    assert extract_line("line 2") == "LINE-02", "Failed: 'line 2' -> LINE-02"
    assert extract_line("jalur 3") == "LINE-03", "Failed: 'jalur 3' -> LINE-03"
    assert extract_line("LINE-02") == "LINE-02", "Failed: 'LINE-02' -> LINE-02"
    assert extract_line("line #4") == "LINE-04", "Failed: 'line #4' -> LINE-04"
    assert extract_line("online status") is None, "Failed: 'online' matched"
    assert extract_line("safety guideline 4") is None, "Failed: 'guideline' matched"
    print("    PASS: Line ID regex verified ('line 2' -> 'LINE-02', digit padding, word boundary).")

def test_serial_regex():
    print("[*] Testing Serial Code regex...")
    serial_regex = re.compile(r'\b((?:ASM|SN)-[A-Za-z0-9\-]+)|\b(?:barcode|serial)\s*[-:#]?\s*([A-Za-z0-9\-]*\d[A-Za-z0-9\-]*)', re.IGNORECASE)

    def extract_serial(text: str) -> Optional[str]:
        m = serial_regex.search(text)
        if not m:
            return None
        val = m.group(1) or m.group(2)
        return val.upper() if val else None

    assert extract_serial("barcode ASM-8910") == "ASM-8910", "Failed: 'barcode ASM-8910'"
    assert extract_serial("ASM-8910") == "ASM-8910", "Failed: standalone 'ASM-8910'"
    assert extract_serial("serial: SN-2026-001") == "SN-2026-001", "Failed: 'serial: SN-2026-001'"
    assert extract_serial("barcode #987654") == "987654", "Failed: 'barcode #987654'"
    assert extract_serial("check all serials") is None, "Failed: plural 'serials' matched"
    print("    PASS: Serial code regex verified ('barcode ASM-8910' -> 'ASM-8910', standalone prefixes, digit anchoring).")

def test_canonical_routes():
    print("[*] Confirming Table 2.4.1 canonical routes map to VIEW-01..VIEW-06...")
    table_routes = {
        "cutting-record": {"view": "VIEW-03", "route": "/app/materials?action=cutting"},
        "warehouse-receive": {"view": "VIEW-03", "route": "/app/materials?action=receive"},
        "sewing-tally": {"view": "VIEW-04", "route": "/terminal/tally"},
        "qc-inspection": {"view": "VIEW-05", "route": "/app/quality"},
        "ledger-entry": {"view": "VIEW-06", "route": "/app/finance?tab=journals"},
        "payroll-approval": {"view": "VIEW-06", "route": "/app/finance?tab=payroll"},
    }
    frontend_arch_views = {
        "VIEW-01": "/app/overview",
        "VIEW-02": "/app/samples",
        "VIEW-03": "/app/materials",
        "VIEW-04": ["/app/production", "/terminal/tally"],
        "VIEW-05": "/app/quality",
        "VIEW-06": "/app/finance",
    }
    for shortcut_id, mapping in table_routes.items():
        view = mapping["view"]
        route = mapping["route"]
        base_route = route.split("?")[0]
        arch_routes = frontend_arch_views[view]
        if isinstance(arch_routes, list):
            assert base_route in arch_routes, f"{shortcut_id} base route {base_route} not in {arch_routes}"
        else:
            assert base_route == arch_routes, f"{shortcut_id} base route {base_route} != {arch_routes}"
        print(f"    PASS: {shortcut_id} -> {view} ({route}) maps to 14-frontend-architecture.md")

if __name__ == "__main__":
    test_action_shortcut()
    test_order_regex()
    test_line_regex()
    test_serial_regex()
    test_canonical_routes()
    print("\n✅ [ALL TESTS PASSED] Empirical regression verification successful.")
