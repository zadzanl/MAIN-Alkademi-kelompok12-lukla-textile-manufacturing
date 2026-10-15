import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.problem import ProblemException
from backend.app.copilot.config import copilot_settings
from backend.app.copilot.schemas import ToolDefinition
from backend.app.copilot.registry import filter_tools_for_roles, READ_TOOL_CATALOG
from backend.app.copilot.shortcuts import match_action_shortcut
from backend.app.copilot.executor import ReadOnlyToolExecutor

@pytest.fixture
def client():
    return TestClient(app)

def test_copilot_inquiry_stock_returns_200_and_tools_used(client):
    """
    Test 1: POST /api/v1/copilot/chat with inquiry ("Berapa stok kain fleece?")
    returns HTTP 200 with reply and tools used.
    """
    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Berapa stok kain fleece?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "stok kain fleece" in data["reply"].lower()
    assert "get_stock_balances" in data["tools_used"]
    assert "usage" in data
    assert data["usage"]["total_tokens"] > 0

def test_copilot_mutation_intent_returns_action_shortcut(client):
    """
    Test 2: POST /api/v1/copilot/chat with mutation intent ("Tolong potong kain order ORD-104")
    returns Action Shortcut to /cutting/new?orderId=ORD-104.
    """
    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Tolong potong kain order ORD-104"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "shortcuts" in data
    assert len(data["shortcuts"]) > 0
    shortcut = data["shortcuts"][0]
    assert shortcut["url"] == "/cutting/new?orderId=ORD-104"
    assert "Catat Hasil Pemotongan" in shortcut["title"]
    assert shortcut["icon"] == "scissors"

def test_rejection_of_non_get_tool_execution_api_rfc7807(client):
    """
    Test 3 (Integration): Rejection of non-GET tool execution raises HTTP 403 Forbidden RFC 7807 problem.
    """
    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "force_non_get_mutation"}
    )
    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    problem = response.json()
    assert problem["code"] == "FORBIDDEN"
    assert "LLM autonomous state mutations are forbidden" in problem["detail"]
    assert problem["status"] == 403

def test_rejection_of_non_get_tool_execution_unit():
    """
    Test 3 (Unit): Direct verification of physical method == 'GET' barrier in ReadOnlyToolExecutor.
    """
    import asyncio
    executor = ReadOnlyToolExecutor()
    non_get_tool = ToolDefinition(
        name="post_cut_batch",
        description="Mutate cutting batch",
        endpoint_path="/cutting/batches",
        method="POST",
        allowed_roles=["Owner"],
        parameters={}
    )
    with pytest.raises(ProblemException) as exc_info:
        asyncio.run(executor.execute_tool("post_cut_batch", tool_def=non_get_tool))

    assert exc_info.value.status == 403
    assert exc_info.value.code == "FORBIDDEN"
    assert exc_info.value.detail == "LLM autonomous state mutations are forbidden"


def test_role_filtering_prevents_maklon_client_from_seeing_ledger_tools(client):
    """
    Test 4: Role filtering prevents MaklonClient from seeing ledger tools.
    """
    # 1. Direct registry unit verification
    maklon_tools = filter_tools_for_roles(["MaklonClient"])
    maklon_tool_names = [t["name"] for t in maklon_tools]
    assert "get_ledger_entries" not in maklon_tool_names
    assert "get_stock_balances" in maklon_tool_names

    owner_tools = filter_tools_for_roles(["Owner"])
    owner_tool_names = [t["name"] for t in owner_tools]
    assert "get_ledger_entries" in owner_tool_names

    # 2. Endpoint verification with MaklonClient role header / body
    response = client.post(
        "/api/v1/copilot/chat",
        json={
            "message": "Cek buku kas dan transaksi ledger",
            "roles": ["MaklonClient"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "get_ledger_entries" not in data["tools_used"]

def test_action_shortcut_variations():
    """Verify regex disambiguation across all 6 core workflows."""
    # Cutting
    sc_cut = match_action_shortcut("Tolong potong kain untuk order SO-2026-001")
    assert sc_cut is not None
    assert sc_cut.url == "/cutting/new?orderId=SO-2026-001"

    # Warehouse receive
    sc_wh = match_action_shortcut("Ada kedatangan kain masuk di gudang bahan")
    assert sc_wh is not None
    assert sc_wh.url == "/warehouse/receive"

    # Sewing Tally
    sc_sew = match_action_shortcut("Catat input tally 30 menit jalur 2")
    assert sc_sew is not None
    assert sc_sew.url == "/sewing/tally?lineId=LINE-02"

    # QC Inspection (takes precedence over sewing even with 'jahitan')
    sc_qc = match_action_shortcut("Ada cacat jahitan pada barcode ASM-8910")
    assert sc_qc is not None
    assert sc_qc.url == "/qc/inspect?serialCode=ASM-8910"

    # Ledger
    sc_ledger = match_action_shortcut("Posting jurnal penyesuaian baru")
    assert sc_ledger is not None
    assert sc_ledger.url == "/ledger/transactions/new"

    # Payroll
    sc_payroll = match_action_shortcut("Rekap payroll upah borongan sabtu ini")
    assert sc_payroll is not None
    assert sc_payroll.url == "/payroll/weekly"

def test_copilot_disabled_guard(client, monkeypatch):
    """Verify that disabling copilot returns HTTP 503."""
    monkeypatch.setattr(copilot_settings, "AI_COPILOT_ENABLED", False)
    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Berapa stok kain?"}
    )
    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    problem = response.json()
    assert problem["code"] == "SERVICE_SCOPE_REQUIRED"

def test_copilot_web_ui_returns_200_html(client):
    """
    Test 8: GET /copilot and GET /api/v1/copilot return HTTP 200 with HTML content
    and required testid anchors for browser/Playwright verification.
    """
    # 1. Test root mounted route /copilot
    resp_root = client.get("/copilot")
    assert resp_root.status_code == 200
    assert "text/html" in resp_root.headers.get("content-type", "")
    html = resp_root.text
    assert "Lukla Operations Copilot" in html
    assert 'data-testid="copilot-chat"' in html
    assert 'data-testid="copilot-role-select"' in html
    assert 'data-testid="copilot-input"' in html
    assert 'data-testid="copilot-send"' in html
    assert 'data-testid="copilot-message"' in html
    assert 'data-testid="action-shortcut-card"' in html

    # 2. Test api/v1 mounted route /api/v1/copilot
    resp_api = client.get("/api/v1/copilot")
    assert resp_api.status_code == 200
    assert "text/html" in resp_api.headers.get("content-type", "")

