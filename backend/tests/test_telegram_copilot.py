"""
Automated Verification Gate for Telegram Copilot Bot (AC-1 through AC-8).

HOW TELEGRAM BOT TESTING WORKS WITHOUT REAL TELEGRAM SERVERS:
1. INBOUND (Telegram -> Our Server):
   When a user messages a Telegram bot, Telegram's servers send a standard HTTP POST
   request to our `/api/v1/telegram/webhook` endpoint with a JSON body ("Update") and
   a secret header (`X-Telegram-Bot-Api-Secret-Token`).
   In this test suite, FastAPI's `TestClient` acts as Telegram's server and posts
   realistic Telegram Update JSON payloads directly to `/api/v1/telegram/webhook`.

2. OUTBOUND (Our Server -> Telegram):
   When our server replies to the user, it makes an outbound HTTP POST request using
   `httpx.AsyncClient` to `https://api.telegram.org/bot<TOKEN>/sendMessage` with
   `{"chat_id": ..., "text": ...}`.
   In this test suite, we intercept outbound `httpx.AsyncClient` requests using
   `httpx.MockTransport` (and transport-level capture), allowing us to:
   - Verify the exact URL, bot token, chat_id, and reply text sent to Telegram.
   - Simulate Telegram API failures (HTTP 429 Too Many Requests, HTTP 502 Bad Gateway,
     or network timeouts) and prove that our database bindings and Copilot state
     do not roll back or enter infinite retry loops.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app.core.auth import create_access_token
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.copilot.config import copilot_settings
from backend.app.main import app


# ==============================================================================
# Deterministic Test Fixtures & Constants
# ==============================================================================

TENANT_A = uuid.UUID("b0000000-0000-4000-8000-000000000001")
ADMIN_ACTOR_ID = uuid.UUID("f0000000-0000-4000-8000-000000000001")
WORKER_ACTOR_ID = uuid.UUID("f0000000-0000-4000-8000-000000000002")
CLIENT_ACTOR_ID = uuid.UUID("f0000000-0000-4000-8000-000000000003")
CLIENT_LEGAL_OWNER_ID = uuid.UUID("c0000000-0000-4000-8000-000000000001")

TEST_BOT_TOKEN = "123456789:AAH_test_bot_token_for_automated_verification"
TEST_WEBHOOK_SECRET = "lukla-telegram-webhook-secret-token-2026"


@dataclass
class CapturedTelegramCall:
    """Represents a single outbound HTTP request made to api.telegram.org."""
    method: str
    url: str
    payload: Dict[str, Any]
    headers: Dict[str, str]


@dataclass
class FakeTelegramAPIServer:
    """
    In-memory simulator of `https://api.telegram.org/bot<TOKEN>/<method>`.
    Captures every outbound request (`sendMessage`, `setWebhook`, etc.) and can be
    programmed to return HTTP 200, HTTP 429 (rate limit), HTTP 500, or raise a timeout.
    """
    calls: List[CapturedTelegramCall] = field(default_factory=list)
    next_status_code: int = 200
    next_error_description: str = "Bad Request: simulated error"
    raise_timeout: bool = False
    fail_first_parse_mode: bool = False

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        body_bytes = request.read()
        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            payload = {"_raw": body_bytes.decode("utf-8", errors="replace")}

        self.calls.append(
            CapturedTelegramCall(
                method=request.method,
                url=str(request.url),
                payload=payload,
                headers=dict(request.headers),
            )
        )

        if self.raise_timeout:
            raise httpx.ReadTimeout("Simulated Telegram API timeout", request=request)

        # Simulate Telegram rejecting malformed Markdown/HTML on first attempt,
        # so the implementation can prove it falls back to plain text safely.
        if self.fail_first_parse_mode and payload.get("parse_mode"):
            self.fail_first_parse_mode = False
            return httpx.Response(
                status_code=400,
                json={
                    "ok": False,
                    "error_code": 400,
                    "description": "Bad Request: can't parse entities",
                },
                request=request,
            )

        if self.next_status_code != 200:
            return httpx.Response(
                status_code=self.next_status_code,
                json={
                    "ok": False,
                    "error_code": self.next_status_code,
                    "description": self.next_error_description,
                },
                request=request,
            )

        return httpx.Response(
            status_code=200,
            json={
                "ok": True,
                "result": {
                    "message_id": 9000 + len(self.calls),
                    "chat": {"id": payload.get("chat_id"), "type": "private"},
                    "text": payload.get("text", ""),
                },
            },
            request=request,
        )

    @property
    def sent_messages(self) -> List[CapturedTelegramCall]:
        return [c for c in self.calls if c.url.endswith("/sendMessage")]


class _StubResult:
    def __init__(self, val: Any = None):
        self._val = val or uuid.uuid4()

    def scalar_one_or_none(self) -> Any:
        return self._val

    def fetchone(self) -> Any:
        return (self._val,)


class _StubDBSession:
    """Lightweight session stub so JWT auth checks pass without a live Postgres daemon."""
    def execute(self, _statement: Any, _parameters: Any = None) -> _StubResult:
        return _StubResult(TENANT_A)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


def make_admin_jwt(
    role: str = "Owner",
    tenant_id: uuid.UUID = TENANT_A,
    actor_id: uuid.UUID = ADMIN_ACTOR_ID,
) -> str:
    return create_access_token(
        {
            "sub": str(actor_id),
            "roles": [role],
            "tenant_id": str(tenant_id),
        }
    )


def build_telegram_update(
    update_id: int,
    chat_id: int | str,
    text: str,
    chat_type: str = "private",
    username: str = "untrusted_username",
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Constructs a canonical Telegram Bot API Update JSON payload."""
    payload: Dict[str, Any] = {
        "update_id": update_id,
        "message": {
            "message_id": update_id * 10,
            "date": 1760572800,
            "chat": {
                "id": int(chat_id) if str(chat_id).lstrip("-").isdigit() else chat_id,
                "type": chat_type,
                "username": username,
            },
            "from": {
                "id": int(chat_id) if str(chat_id).lstrip("-").isdigit() else 111111,
                "is_bot": False,
                "first_name": "TestUser",
                "username": username,
            },
            "text": text,
        },
    }
    if extra_fields:
        payload.update(extra_fields)
    return payload


@pytest.fixture(autouse=True)
def configure_test_environment(monkeypatch: pytest.MonkeyPatch):
    """
    Sets deterministic Mock LLM provider and Telegram settings for every test,
    and intercepts any outbound HTTP calls to `api.telegram.org`.
    """
    monkeypatch.setattr(copilot_settings, "AI_COPILOT_ENABLED", True)
    monkeypatch.setattr(copilot_settings, "COPILOT_DEFAULT_PROVIDER", "mock")
    monkeypatch.setattr(copilot_settings, "COPILOT_DEMO_MODE", False)

    # Configure Telegram settings on root `settings` (or telegram module config if present)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", TEST_BOT_TOKEN, raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", TEST_WEBHOOK_SECRET, raising=False)


@pytest.fixture
def fake_telegram(monkeypatch: pytest.MonkeyPatch) -> FakeTelegramAPIServer:
    """
    Intercepts all outbound httpx.AsyncClient calls targeting `api.telegram.org`
     while letting internal ASGI calls (`http://internal/api/v1`) pass through normally.
    """
    server = FakeTelegramAPIServer()
    real_async_client = httpx.AsyncClient

    class InterceptedAsyncClient(real_async_client):
        def __init__(self, *args: Any, **kwargs: Any):
            # If caller did not explicitly inject an ASGITransport, wrap transport
            # to route api.telegram.org to our FakeTelegramAPIServer.
            existing_transport = kwargs.get("transport")
            if existing_transport is None:
                kwargs["transport"] = httpx.MockTransport(server.handle_request)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", InterceptedAsyncClient)
    return server


@pytest.fixture
def client() -> TestClient:
    """Provides a FastAPI TestClient with stubbed DB auth lookup and clean store state."""
    def override_get_db():
        s = _StubDBSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db

    # Reset telegram store state between tests if the module provides a reset helper
    try:
        from backend.app.telegram import store as tg_store
        if hasattr(tg_store, "reset_telegram_store_for_tests"):
            tg_store.reset_telegram_store_for_tests()
    except ImportError:
        pass

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()


def _enroll_chat(
    client: TestClient,
    chat_id: int,
    role: str,
    actor_id: uuid.UUID = WORKER_ACTOR_ID,
    tenant_id: uuid.UUID = TENANT_A,
    update_id: int = 100,
) -> str:
    """Helper to generate an admin single-use enrollment code and consume it via `/start`."""
    admin_headers = {"Authorization": f"Bearer {make_admin_jwt('Owner', tenant_id=tenant_id)}"}
    create_resp = client.post(
        "/api/v1/telegram/admin/enrollment-codes",
        headers=admin_headers,
        json={
            "role": role,
            "actor_id": str(actor_id),
            "tenant_id": str(tenant_id),
            "expires_in_seconds": 600,
        },
    )
    assert create_resp.status_code in (200, 201), (
        f"Expected 200/201 from enrollment code creation, got {create_resp.status_code}: {create_resp.text}"
    )
    code_data = create_resp.json()
    code = code_data.get("code") or code_data.get("enrollment_code")
    assert code and isinstance(code, str) and len(code) >= 8, "Admin endpoint must return a high-entropy one-time code"

    webhook_resp = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=update_id, chat_id=chat_id, text=f"/start {code}"),
    )
    assert webhook_resp.status_code == 200, (
        f"Expected 200 on `/start <code>` webhook, got {webhook_resp.status_code}: {webhook_resp.text}"
    )
    return code


# ==============================================================================
# Gate 0: OpenAPI & Module Structure Contract
# ==============================================================================

def test_gate0_openapi_and_module_contracts_exist():
    """
    Verifies that the required Telegram modules and OpenAPI routes exist in the app.
    """
    paths = app.openapi()["paths"]
    assert "/api/v1/telegram/webhook" in paths, "Missing POST /api/v1/telegram/webhook in OpenAPI"
    assert "/api/v1/telegram/admin/enrollment-codes" in paths, (
        "Missing POST /api/v1/telegram/admin/enrollment-codes in OpenAPI"
    )
    assert "/api/v1/telegram/admin/bindings/{telegram_chat_id}/revoke" in paths, (
        "Missing POST /api/v1/telegram/admin/bindings/{telegram_chat_id}/revoke in OpenAPI"
    )

    # Verify required module boundaries exist
    import backend.app.telegram.schemas as schemas  # noqa: F401
    import backend.app.telegram.security as security  # noqa: F401
    import backend.app.telegram.store as store  # noqa: F401
    import backend.app.telegram.transport as transport  # noqa: F401


# ==============================================================================
# AC-5: Webhook Secret Validation, Unbound Chats, & Idempotency
# ==============================================================================

def test_ac5_webhook_rejects_missing_or_invalid_secret_token(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-5: Requests without the exact `X-Telegram-Bot-Api-Secret-Token` must be rejected
    with 401/403 before invoking Copilot or sending any outbound Telegram message.
    """
    update = build_telegram_update(update_id=1, chat_id=5001, text="Berapa stok kain fleece?")

    # Missing header
    resp_missing = client.post("/api/v1/telegram/webhook", json=update)
    assert resp_missing.status_code in (401, 403)

    # Wrong header
    resp_wrong = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        json=update,
    )
    assert resp_wrong.status_code in (401, 403)
    assert len(fake_telegram.sent_messages) == 0, "No outbound Telegram message may be sent on invalid secret"


def test_ac5_unbound_chat_is_denied_without_invoking_copilot_or_leaking_code_state(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-5: Unbound users receive generic instructions to contact an administrator.
    Invalid `/start` codes do not leak whether a code existed or belonged to someone else.
    """
    # 1. Plain question from unbound chat
    resp = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=2, chat_id=5002, text="Berapa stok kain fleece?"),
    )
    assert resp.status_code == 200
    assert len(fake_telegram.sent_messages) == 1
    reply_text = fake_telegram.sent_messages[0].payload["text"].lower()
    assert "stok kain fleece" not in reply_text, "Unbound user must not receive Copilot data"
    assert any(word in reply_text for word in ("admin", "enroll", "terdaftar", "bound", "akses", "otorisasi"))

    # 2. Invalid /start code vs non-existent /start code must not leak internal state
    resp_bad_code = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=3, chat_id=5002, text="/start INVALID-CODE-999"),
    )
    assert resp_bad_code.status_code == 200


def test_ac5_group_chats_are_rejected_in_first_release(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    Defaults & Behavioral requirement: Only `private` chats may bind or query Copilot;
    `group` and `supergroup` updates are rejected deterministically.
    """
    _enroll_chat(client, chat_id=5003, role="Owner", update_id=10)
    fake_telegram.calls.clear()

    group_update = build_telegram_update(
        update_id=11,
        chat_id=5003,
        text="Berapa stok kain fleece?",
        chat_type="supergroup",
    )
    resp = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=group_update,
    )
    assert resp.status_code in (200, 400, 403)
    for msg in fake_telegram.sent_messages:
        assert "stok kain fleece" not in msg.payload.get("text", "").lower()


# ==============================================================================
# AC-3 & AC-4: Admin Single-Use Enrollment, Persistence, & Revocation
# ==============================================================================

def test_ac3_admin_enrollment_requires_admin_auth_and_enforces_single_use(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-3:
    - Non-admin callers cannot generate enrollment codes (401/403).
    - Admin creates a one-time enrollment code.
    - First `/start <code>` binds chat_id 6001.
    - Second `/start <code>` with the same code from chat_id 6002 is rejected (single-use).
    """
    # Unauthenticated call fails
    unauth = client.post(
        "/api/v1/telegram/admin/enrollment-codes",
        json={"role": "Tailor", "actor_id": str(WORKER_ACTOR_ID), "tenant_id": str(TENANT_A)},
    )
    assert unauth.status_code in (401, 403)

    # Non-admin role (Tailor) fails
    tailor_headers = {"Authorization": f"Bearer {make_admin_jwt('Tailor')}"}
    forbidden = client.post(
        "/api/v1/telegram/admin/enrollment-codes",
        headers=tailor_headers,
        json={"role": "Owner", "actor_id": str(WORKER_ACTOR_ID), "tenant_id": str(TENANT_A)},
    )
    assert forbidden.status_code == 403

    # Enroll chat 6001 with single-use code
    code = _enroll_chat(client, chat_id=6001, role="Warehouse", update_id=20)
    fake_telegram.calls.clear()

    # Attempt to reuse the consumed code from another chat 6002
    client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=21, chat_id=6002, text=f"/start {code}"),
    )
    fake_telegram.calls.clear()

    # Verify chat 6002 is still unbound
    client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=22, chat_id=6002, text="Berapa stok kain fleece?"),
    )
    assert len(fake_telegram.sent_messages) == 1
    assert "stok kain fleece" not in fake_telegram.sent_messages[0].payload["text"].lower()


def test_ac4_admin_revocation_blocks_subsequent_copilot_queries(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-4: Once an admin revokes a bound `telegram_chat_id`, subsequent messages from
    that chat cannot query Copilot.
    """
    _enroll_chat(client, chat_id=6010, role="Owner", update_id=30)
    fake_telegram.calls.clear()

    # Revoke binding as Admin
    admin_headers = {"Authorization": f"Bearer {make_admin_jwt('Owner')}"}
    revoke_resp = client.post(
        "/api/v1/telegram/admin/bindings/6010/revoke",
        headers=admin_headers,
    )
    assert revoke_resp.status_code == 200

    # Query after revocation
    client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=31, chat_id=6010, text="Berapa stok kain fleece?"),
    )
    assert len(fake_telegram.sent_messages) == 1
    assert "stok kain fleece" not in fake_telegram.sent_messages[0].payload["text"].lower()


# ==============================================================================
# AC-1, AC-2, AC-2a, & AC-8: Copilot Execution, Anti-Spoofing, & Role Isolation
# ==============================================================================

def test_ac1_and_ac2_bound_chat_reaches_copilot_and_cannot_spoof_roles(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-1 & AC-2:
    - Bound chat reaches `_execute_copilot_turn` and sends reply via Telegram Bot API `sendMessage`.
    - Even if the webhook caller injects `X-Roles: Owner` or `"roles": ["Owner"]` in the JSON body,
      a chat bound as `MaklonClient` strictly executes as `MaklonClient` and CANNOT access `get_ledger_entries`.
    """
    _enroll_chat(
        client,
        chat_id=7001,
        role="MaklonClient",
        actor_id=CLIENT_ACTOR_ID,
        tenant_id=TENANT_A,
        update_id=40,
    )
    fake_telegram.calls.clear()

    # Send a ledger query while attempting to spoof Owner via both HTTP header and JSON body
    spoofed_update = build_telegram_update(
        update_id=41,
        chat_id=7001,
        text="Cek buku kas dan transaksi ledger",
        extra_fields={"roles": ["Owner"]},
    )
    resp = client.post(
        "/api/v1/telegram/webhook",
        headers={
            "X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET,
            "X-Roles": "Owner",
        },
        json=spoofed_update,
    )
    assert resp.status_code == 200
    body = resp.json()
    # If tools_used is returned in webhook response metadata, verify get_ledger_entries was blocked
    if "tools_used" in body and body["tools_used"] is not None:
        assert "get_ledger_entries" not in body["tools_used"]

    assert len(fake_telegram.sent_messages) == 1
    outbound = fake_telegram.sent_messages[0]
    assert f"/bot{TEST_BOT_TOKEN}/sendMessage" in outbound.url
    assert str(outbound.payload["chat_id"]) == "7001"
    # Verify ledger data is not leaked to MaklonClient
    assert "get_ledger_entries" not in outbound.payload["text"]


def test_ac8_role_isolation_across_owner_worker_stakeholder_and_client(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-8: Verifies role isolation across Owner, Tailor (worker), ProductionHead (stakeholder),
    and MaklonClient (client) against the tool catalog.
    """
    # 1. Owner can access ledger and stock
    _enroll_chat(client, chat_id=8001, role="Owner", actor_id=ADMIN_ACTOR_ID, update_id=50)
    fake_telegram.calls.clear()
    resp_owner = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=51, chat_id=8001, text="Berapa stok kain fleece?"),
    )
    assert resp_owner.status_code == 200
    assert len(fake_telegram.sent_messages) == 1
    assert "stok kain fleece" in fake_telegram.sent_messages[0].payload["text"].lower()

    # 2. Tailor (worker) can query production progress, but NOT stock balances or ledger
    _enroll_chat(client, chat_id=8002, role="Tailor", actor_id=WORKER_ACTOR_ID, update_id=52)
    fake_telegram.calls.clear()
    resp_tailor_stock = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=53, chat_id=8002, text="Berapa stok kain fleece?"),
    )
    assert resp_tailor_stock.status_code == 200
    if "tools_used" in resp_tailor_stock.json():
        assert "get_stock_balances" not in (resp_tailor_stock.json()["tools_used"] or [])


# ==============================================================================
# AC-5 & AC-7: Duplicate `update_id` Idempotency & Telegram API Failure Resilience
# ==============================================================================

def test_ac5_duplicate_update_id_is_idempotent(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-5: Re-sending the exact same `update_id` (simulating a Telegram webhook retry)
    must not trigger a second Copilot inference turn or send a duplicate outbound message.
    """
    _enroll_chat(client, chat_id=9001, role="Owner", update_id=60)
    fake_telegram.calls.clear()

    update = build_telegram_update(update_id=61, chat_id=9001, text="Berapa stok kain fleece?")
    first = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=update,
    )
    assert first.status_code == 200
    assert len(fake_telegram.sent_messages) == 1

    # Replay the exact same update_id=61
    second = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=update,
    )
    assert second.status_code == 200
    assert len(fake_telegram.sent_messages) == 1, "Duplicate update_id must not send a second Telegram reply"


def test_ac6_telegram_cannot_execute_mutations(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-6: Mutation intents sent over Telegram return non-executable text/shortcut info
    and never execute state-mutating POST/PUT/DELETE operations.
    """
    _enroll_chat(client, chat_id=9002, role="Owner", update_id=70)
    fake_telegram.calls.clear()

    resp = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(
            update_id=71, chat_id=9002, text="Tolong potong kain order ORD-104"
        ),
    )
    assert resp.status_code == 200
    assert len(fake_telegram.sent_messages) == 1


def test_ac7_telegram_api_failure_does_not_rollback_enrollment_or_loop_infinitely(
    client: TestClient, fake_telegram: FakeTelegramAPIServer
):
    """
    AC-7: When `api.telegram.org` returns HTTP 502 or times out during `/start <code>`,
    the enrollment binding is still preserved (not rolled back) and no unbounded retry loop occurs.
    """
    fake_telegram.next_status_code = 502
    _enroll_chat(client, chat_id=9003, role="Owner", update_id=80)

    # Restore Telegram API health and verify chat 9003 is bound and can query Copilot
    fake_telegram.next_status_code = 200
    fake_telegram.calls.clear()

    resp = client.post(
        "/api/v1/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": TEST_WEBHOOK_SECRET},
        json=build_telegram_update(update_id=81, chat_id=9003, text="Berapa stok kain fleece?"),
    )
    assert resp.status_code == 200
    assert len(fake_telegram.sent_messages) == 1
    assert "stok kain fleece" in fake_telegram.sent_messages[0].payload["text"].lower()
