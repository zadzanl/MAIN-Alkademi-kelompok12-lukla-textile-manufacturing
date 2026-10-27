import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.problem import ProblemException
from backend.app.copilot.config import CopilotSettings, copilot_settings
from backend.app.copilot.schemas import ToolDefinition
from backend.app.copilot.registry import filter_tools_for_roles, READ_TOOL_CATALOG
from backend.app.copilot.shortcuts import match_action_shortcut
from backend.app.copilot.executor import ReadOnlyToolExecutor

@pytest.fixture(autouse=True)
def ensure_mock_provider(monkeypatch):
    monkeypatch.setattr(copilot_settings, "COPILOT_DEFAULT_PROVIDER", "mock")

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
    assert "Lukla Intelligence" in html
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

def test_openrouter_provider_requires_api_key(client, monkeypatch):
    """
    Test 9: Verifies that configuring OpenRouter without an API key produces
    a clean HTTP 500 RFC 7807 problem with clear remediation message.
    """
    monkeypatch.setattr(copilot_settings, "COPILOT_DEFAULT_PROVIDER", "openrouter")
    monkeypatch.setattr(copilot_settings, "COPILOT_API_KEY", "")

    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Berapa stok kain fleece?"}
    )
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert "OpenRouter API key is missing" in data["detail"]

def test_copilot_api_key_uses_runtime_alias_precedence(monkeypatch):
    """Configuration accepts either runtime alias without an embedded fallback."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "alias-test-key")
    monkeypatch.delenv("COPILOT_API_KEY", raising=False)
    assert CopilotSettings().COPILOT_API_KEY == "alias-test-key"

    monkeypatch.setenv("COPILOT_API_KEY", "primary-test-key")
    assert CopilotSettings().COPILOT_API_KEY == "primary-test-key"

    monkeypatch.delenv("COPILOT_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert CopilotSettings().COPILOT_API_KEY == ""

def test_demo_endpoint_requires_configured_key(client, monkeypatch):
    """The demo route must not bypass missing runtime OpenRouter configuration."""
    monkeypatch.setattr(copilot_settings, "COPILOT_API_KEY", "")
    response = client.post(
        "/api/v1/copilot/demo/chat",
        json={"message": "Berapa stok kain fleece?"},
    )
    assert response.status_code == 500
    assert "OpenRouter API key is missing" in response.json()["detail"]

def test_openrouter_provider_mocked_turn(monkeypatch):
    """
    Test 10: Unit verification of OpenRouter provider chat_turn with httpx AsyncClient mocked.
    """
    import asyncio
    from unittest.mock import AsyncMock, MagicMock
    import httpx
    from backend.app.copilot.provider import OpenRouterLLMProvider
    from backend.app.copilot.config import CopilotSettings

    settings = CopilotSettings(
        COPILOT_DEFAULT_PROVIDER="openrouter",
        COPILOT_API_KEY="sk-or-v1-testkey12345",
        COPILOT_MODEL_NAME="meta-llama/llama-3.3-70b-instruct:free",
        COPILOT_BASE_URL="https://openrouter.ai/api/v1"
    )
    provider = OpenRouterLLMProvider(settings=settings)

    mock_resp_json = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Stok kain fleece saat ini 850 roll di warehouse A."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 12,
            "total_tokens": 27
        }
    }

    mock_http_response = MagicMock(spec=httpx.Response)
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = mock_resp_json
    mock_http_response.raise_for_status = MagicMock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_http_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    monkeypatch.setattr(httpx, "AsyncClient", lambda *args, **kwargs: mock_client)

    result = asyncio.run(provider.chat_turn(message="Cek stok kain fleece"))
    assert result.reply == "Stok kain fleece saat ini 850 roll di warehouse A."
    assert result.usage.total_tokens == 27
    assert mock_client.post.called
    call_args = mock_client.post.call_args
    assert "https://openrouter.ai/api/v1/chat/completions" in call_args[0][0]
    assert call_args[1]["headers"]["Authorization"] == "Bearer sk-or-v1-testkey12345"

def test_copilot_stock_inquiry_clean_synthesis_without_json_error(client):
    """
    Test 11: Inquiry about fleece stock invokes /api/v1/stock via ASGI transport,
    synthesizes real available lot quantities, and contains NO raw JSON problem dumps.
    """
    response = client.post(
        "/api/v1/copilot/chat",
        json={"message": "Berapa stok kain fleece saat ini?"}
    )
    assert response.status_code == 200
    data = response.json()
    reply = data["reply"]

    # Verify no raw JSON or RFC 7807 404 dumps leaked into response
    assert "VALIDATION_ERROR" not in reply
    assert "Not Found" not in reply
    assert '{"type"' not in reply
    assert "/api/v1/warehouse/stock" not in reply

    # Verify real synthesized data from /stock route
    assert "1,250" in reply
    assert "LOT-2026-105" in reply
    assert "get_stock_balances" in data["tools_used"]

def test_copilot_tool_error_degradation_notice():
    """
    Test 12: When a tool returns a non-200 error payload, provider returns an honest
    operational degradation notice and never claims inventory is verified or sufficient.
    """
    import asyncio
    from backend.app.copilot.provider import MockLLMProvider

    provider = MockLLMProvider()
    error_tool_results = [
        {
            "tool_name": "get_stock_balances",
            "status_code": 404,
            "data": {
                "type": "about:blank",
                "title": "Not Found",
                "status": 404,
                "code": "VALIDATION_ERROR",
                "detail": "Not Found",
                "instance": "/api/v1/warehouse/stock"
            }
        }
    ]

    res = asyncio.run(provider.chat_turn(
        message="Berapa sisa kain fleece?",
        tool_results=error_tool_results
    ))

    # Must NOT claim verified or sufficient when tool returned 404
    assert "terverifikasi" not in res.reply.lower()
    assert "mencukupi" not in res.reply.lower()
    assert "tidak dapat diambil" in res.reply.lower() or "galat" in res.reply.lower()

def test_copilot_demo_ui_endpoints(client):
    """
    Test 13: GET /copilot/demo and GET /api/v1/copilot/demo render the interactive
    zero-build demo UI configured for the spare redundant chat endpoint.
    """
    resp1 = client.get("/copilot/demo")
    assert resp1.status_code == 200
    assert "Spare / Redundant Demo Endpoint" in resp1.text
    assert "/api/v1/copilot/demo/chat" in resp1.text

    resp2 = client.get("/api/v1/copilot/demo")
    assert resp2.status_code == 200
    assert "Spare / Redundant Demo Endpoint" in resp2.text
    assert "/api/v1/copilot/demo/chat" in resp2.text

def test_copilot_demo_chat_endpoint(client):
    """
    Test 14: POST /api/v1/copilot/demo/chat processes inquiries with hardcoded fallback configuration.
    """
    resp = client.post(
        "/api/v1/copilot/demo/chat",
        json={"message": "Berapa stok kain fleece?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "reply" in data
    assert "stok kain fleece" in data["reply"].lower()
    assert "get_stock_balances" in data["tools_used"]

def test_copilot_provider_query_param_override(client):
    """
    Test 15: Passing ?provider=mock forces MockLLMProvider execution regardless of environment.
    """
    resp = client.post(
        "/api/v1/copilot/chat?provider=mock",
        json={"message": "Tolong potong kain order ORD-104"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["shortcuts"]) > 0
    assert data["shortcuts"][0]["url"] == "/cutting/new?orderId=ORD-104"

def test_bedrock_provider_initialization_and_mock(monkeypatch):
    """
    Test 16: BedrockLLMProvider instantiates properly and handles converse responses.
    """
    import asyncio
    from backend.app.copilot.provider import BedrockLLMProvider, get_llm_provider

    provider = get_llm_provider("bedrock")
    assert isinstance(provider, BedrockLLMProvider)
    assert provider.region_name == "us-east-1"
    assert provider.model_id == "us.amazon.nova-micro-v1:0"

    class MockBedrockClient:
        def converse(self, **kwargs):
            return {
                "output": {
                    "message": {
                        "content": [{"text": "Halo dari Bedrock Nova Micro!"}]
                    }
                },
                "usage": {
                    "inputTokens": 15,
                    "outputTokens": 8,
                    "totalTokens": 23
                }
            }

    provider._client = MockBedrockClient()
    loop = asyncio.new_event_loop()
    try:
        res = loop.run_until_complete(provider.chat_turn("Halo!"))
        assert res.reply == "Halo dari Bedrock Nova Micro!"
        assert res.usage.total_tokens == 23

        # Verify history with leading assistant message and duplicate user messages coalesces cleanly
        from backend.app.copilot.schemas import ChatMessage
        history = [
            ChatMessage(id="1", sender="assistant", text="Welcome"),
            ChatMessage(id="2", sender="user", text="First question"),
            ChatMessage(id="3", sender="user", text="Second question"),
        ]
        res2 = loop.run_until_complete(
            provider.chat_turn(
                "Berapa stok kain fleece?",
                history=history,
                tool_results=[{"tool_name": "get_stock_balances", "status_code": 200, "data": {"items": [{"sku": "FAB-FLEECE", "quantity": 1250}]}}]
            )
        )
        assert res2.reply == "Halo dari Bedrock Nova Micro!"
    finally:
        loop.close()


def test_boss_system_prompt_contains_date_rules_kpis_and_safeguards():
    """
    Test 17: Verify build_boss_system_prompt injects WIB current date/time,
    Boss-first persona, Lukla domain rules, garment KPIs, and security safeguards.
    """
    from datetime import datetime, timezone, timedelta
    from backend.app.copilot.provider import build_boss_system_prompt, DEFAULT_BOSS_SYSTEM_PROMPT

    fixed_dt = datetime(2026, 10, 16, 10, 0, tzinfo=timezone(timedelta(hours=7)))
    prompt = build_boss_system_prompt(now=fixed_dt)

    assert "Jumat, 2026-10-16 10:00 WIB (Periode: 2026-W42)" in prompt
    assert "Factory Boss" in prompt
    assert "Snøhund" in prompt
    assert "CMT" in prompt and "Semi-CMT" in prompt and "Full Package" in prompt
    assert "SMV/SAM" in prompt and "DHU" in prompt
    assert "Mandor 1, Mandor 2, and Kepala Operasional" in prompt
    assert "Read-Only Physical Barrier" in prompt
    assert "Prompt-Injection & Redaction Safeguard" in prompt
    assert len(DEFAULT_BOSS_SYSTEM_PROMPT) > 500


