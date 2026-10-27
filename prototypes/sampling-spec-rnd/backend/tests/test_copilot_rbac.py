"""RBAC soft-gate tests for the sampling-app Copilot mount.

Covers server-derived role resolution, prompt-injected role tags, execution-time
authorization, forged-claim rejection, and client scope binding. These tests are
scoped to the sampling app only; the root mount and Telegram adapter are covered
by their own suites.

Run from ``prototypes/sampling-spec-rnd/backend``:
    pytest -q tests/test_copilot_rbac.py
"""

from __future__ import annotations

import sys
import uuid

import pytest
from fastapi.testclient import TestClient

from src.api import auth_deps
from src.main import app
from src.services.auth_store import get_store

from backend.app.copilot.config import copilot_settings
from backend.app.copilot.provider import LLMResponse
from backend.app.copilot.schemas import ToolCallRequest, ToolCallResult, TokenUsage

CHAT = "/api/v1/copilot/chat"
DEMO_CHAT = "/api/v1/copilot/demo/chat"


def _copilot_module():
    """Return the shared Copilot route module imported by the sampling app."""
    return sys.modules["backend.app.api.v1.copilot"]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def pin_copilot_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(copilot_settings, "AI_COPILOT_ENABLED", True)
    monkeypatch.setattr(copilot_settings, "COPILOT_DEFAULT_PROVIDER", "mock")


@pytest.fixture()
def demo_mode(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> bool:
    value = request.param
    monkeypatch.setattr(copilot_settings, "COPILOT_DEMO_MODE", value)
    return value


def _seed_session(*, role: str, client_id: str | None = None) -> str:
    unique = uuid.uuid4().hex[:10]
    user = get_store().seed_user(
        email=f"rbac.{unique}@luka.local",
        password="Rahasia123",
        employee_id=f"RBAC-{unique.upper()}",
        full_name="RBAC Test User",
        role=role,
        client_id=client_id,
    )
    token, _ = get_store().create_session(user.user_id, 3600)
    return token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class _ForcedToolProvider:
    """Deterministic provider that always emits one chosen tool call."""

    def __init__(self, tool_name: str, arguments: dict | None = None) -> None:
        self.tool_name = tool_name
        self.arguments = arguments or {}

    async def chat_turn(
        self,
        message: str,
        history=None,
        tools=None,
        system_prompt=None,
        tool_results=None,
    ) -> LLMResponse:
        if tool_results:
            return LLMResponse(reply="Selesai.", tool_calls=[], usage=TokenUsage())
        return LLMResponse(
            reply="Menjalankan alat.",
            tool_calls=[
                ToolCallRequest(
                    id="forced-call-1",
                    tool_name=self.tool_name,
                    arguments=dict(self.arguments),
                )
            ],
            usage=TokenUsage(total_tokens=1),
        )


def _force_tool(
    monkeypatch: pytest.MonkeyPatch, tool_name: str, arguments: dict | None = None
) -> _ForcedToolProvider:
    provider = _ForcedToolProvider(tool_name, arguments)
    monkeypatch.setattr(_copilot_module(), "get_llm_provider", lambda _name: provider)
    return provider


# ─── Authentication ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("demo_mode", [True, False], indirect=True)
def test_chat_requires_bearer_session(client: TestClient, demo_mode: bool):
    resp = client.post(CHAT, json={"message": "Halo"})
    assert resp.status_code == 401
    assert resp.json()["detail"]


@pytest.mark.parametrize("demo_mode", [True, False], indirect=True)
def test_demo_chat_requires_bearer_session(client: TestClient, demo_mode: bool):
    resp = client.post(DEMO_CHAT, json={"message": "Halo"})
    assert resp.status_code == 401
    assert resp.json()["detail"]


def test_chat_rejects_malformed_authorization(client: TestClient):
    resp = client.post(
        CHAT,
        headers={"Authorization": "Token abc"},
        json={"message": "Halo"},
    )
    assert resp.status_code == 401


# ─── Roleless / unknown session → customer level ─────────────────────────────


@pytest.mark.parametrize("demo_mode", [True, False], indirect=True)
def test_roleless_session_is_restricted_to_customer_level(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, demo_mode: bool
):
    token = _seed_session(role="employee")

    # A greeting needs no tool, so the turn succeeds at customer level.
    resp = client.post(CHAT, headers=_auth(token), json={"message": "Halo"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tools_used"] == []
    assert "get_ledger_entries" not in data["tools_used"]

    # A model-emitted Owner-only tool is refused at execution time.
    _force_tool(monkeypatch, "get_ledger_entries")
    resp = client.post(CHAT, headers=_auth(token), json={"message": "Cek ledger"})
    assert resp.status_code == 403
    assert resp.json()["code"] == "FORBIDDEN"
    assert "may not call tool" in resp.json()["detail"]


# ─── Forged X-Roles is ignored ───────────────────────────────────────────────


@pytest.mark.parametrize("demo_mode", [True, False], indirect=True)
def test_forged_x_roles_header_is_ignored(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, demo_mode: bool
):
    token = _seed_session(role="employee")
    _force_tool(monkeypatch, "get_ledger_entries")

    headers = _auth(token)
    headers["X-Roles"] = "Owner"
    resp = client.post(CHAT, headers=headers, json={"message": "Cek ledger"})
    assert resp.status_code == 403
    assert resp.json()["code"] == "FORBIDDEN"


# ─── Unknown tool is rejected before execution ───────────────────────────────


@pytest.mark.parametrize("demo_mode", [True, False], indirect=True)
def test_unknown_tool_is_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, demo_mode: bool
):
    token = _seed_session(role="Owner")
    _force_tool(monkeypatch, "delete_everything")

    resp = client.post(CHAT, headers=_auth(token), json={"message": "Hapus semua"})
    assert resp.status_code == 403
    assert resp.json()["code"] == "FORBIDDEN"
    assert "not in the approved read-only catalog" in resp.json()["detail"]


# ─── MaklonClient document search is denied ──────────────────────────────────


@pytest.mark.parametrize("demo_mode", [True, False], indirect=True)
def test_maklon_client_document_search_is_denied(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, demo_mode: bool
):
    monkeypatch.setattr(
        auth_deps, "SUPPORTED_CLIENT_IDS", frozenset({"client-alpha", "client-beta"})
    )
    token = _seed_session(role="client", client_id="client-alpha")
    _force_tool(monkeypatch, "search_operational_documents", {"q": "spesifikasi"})

    resp = client.post(CHAT, headers=_auth(token), json={"message": "Cari dokumen"})
    assert resp.status_code == 403
    assert resp.json()["code"] == "FORBIDDEN"
    assert resp.json()["detail"] == "Document search is not available for client scope."


# ─── Owner and admin tool access ─────────────────────────────────────────────


@pytest.mark.parametrize("demo_mode", [True, False], indirect=True)
def test_owner_session_can_use_owner_tools(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, demo_mode: bool
):
    token = _seed_session(role="Owner")
    _force_tool(monkeypatch, "get_ledger_entries")

    resp = client.post(CHAT, headers=_auth(token), json={"message": "Cek ledger"})
    assert resp.status_code == 200
    assert "get_ledger_entries" in resp.json()["tools_used"]


@pytest.mark.parametrize("demo_mode", [True, False], indirect=True)
def test_admin_session_maps_to_owner_tools(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, demo_mode: bool
):
    token = _seed_session(role="admin")
    _force_tool(monkeypatch, "get_ledger_entries")

    resp = client.post(CHAT, headers=_auth(token), json={"message": "Cek ledger"})
    assert resp.status_code == 200
    assert "get_ledger_entries" in resp.json()["tools_used"]


# ─── Client scope binding (Client A cannot read Client B) ────────────────────


def test_client_scope_binding_forces_session_client(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(copilot_settings, "COPILOT_DEMO_MODE", False)
    monkeypatch.setattr(
        auth_deps, "SUPPORTED_CLIENT_IDS", frozenset({"client-alpha", "client-beta"})
    )
    token = _seed_session(role="client", client_id="client-alpha")
    _seed_session(role="client", client_id="client-beta")

    captured: dict = {}

    class _RecordingExecutor:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        async def execute_tool(self, tool_name, arguments=None, **_kwargs) -> ToolCallResult:
            captured["tool_name"] = tool_name
            captured["arguments"] = dict(arguments or {})
            return ToolCallResult(
                tool_call_id=tool_name, tool_name=tool_name, status_code=200, data={"items": []}
            )

    monkeypatch.setattr(_copilot_module(), "ReadOnlyToolExecutor", _RecordingExecutor)
    _force_tool(monkeypatch, "get_order_status", {"clientId": "client-beta"})

    resp = client.post(CHAT, headers=_auth(token), json={"message": "Cek order"})
    assert resp.status_code == 200
    assert captured["tool_name"] == "get_order_status"
    assert captured["arguments"]["clientId"] == "client-alpha"
    assert captured["arguments"]["legalOwnerId"] == "client-alpha"


def test_client_without_supported_scope_is_denied(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(copilot_settings, "COPILOT_DEMO_MODE", True)
    monkeypatch.setattr(auth_deps, "SUPPORTED_CLIENT_IDS", frozenset())
    token = _seed_session(role="client", client_id="client-alpha")
    _force_tool(monkeypatch, "get_stock_balances")

    resp = client.post(CHAT, headers=_auth(token), json={"message": "Cek stok"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Client scope is unavailable."


# ─── Demo fixtures respect client scope ──────────────────────────────────────


def test_demo_fixture_is_scoped_to_client():
    module = _copilot_module()

    scoped = module._demo_tool_result(
        "get_order_status",
        {"tenant_id": "tenant-001", "client_id": "client-alpha"},
        "MaklonClient",
    )
    assert scoped.data["items"]
    assert all(item["clientId"] == "client-alpha" for item in scoped.data["items"])

    empty = module._demo_tool_result(
        "get_order_status",
        {"tenant_id": "tenant-001", "client_id": None},
        "MaklonClient",
    )
    assert empty.data == {"items": [], "source": "demo-fixture"}

    owner = module._demo_tool_result(
        "get_order_status",
        {"tenant_id": "tenant-001", "client_id": None},
        "Owner",
    )
    assert len(owner.data["items"]) == 2


def test_forged_default_key_jwt_is_rejected(client):
    """F-01: the sampling gate must not accept a root-backend JWT (default key)."""
    import jwt

    from backend.app.core.config import settings

    forged = jwt.encode(
        {"roles": ["Owner"], "tenant_id": "tenant-001", "client_id": None},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    resp = client.post(
        CHAT,
        json={"message": "stok", "history": [], "roles": ["Owner"]},
        headers=_auth(forged),
    )
    assert resp.status_code == 401, resp.text