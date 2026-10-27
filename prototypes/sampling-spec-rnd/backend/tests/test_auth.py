"""Contract tests for the portal authentication API (src/api/auth_routes.py).

Covers the full internal-user lifecycle: registration -> Admin IT approval ->
login -> change password -> forgot/reset password, plus the error paths the
frontend depends on.

Run:  pytest -q   (from the backend/ directory)
"""

from __future__ import annotations

import os
import re
import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api import auth_routes
from src.api.auth_deps import session_context
from src.main import app
from src.services.auth_store import AuthError, get_store

PREFIX = "/api/auth"


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def captured_email(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Intercept outbound email so the OTP can be read back in tests."""
    box: dict[str, str] = {}

    def fake_send(to: str, subject: str, body: str) -> str:
        box["to"] = to
        box["subject"] = subject
        box["body"] = body
        return "dev-log"

    monkeypatch.setattr(auth_routes, "send_email", fake_send)
    return box


def _unique_identity() -> dict[str, str]:
    token = uuid.uuid4().hex[:8]
    numeric = str(uuid.uuid4().int)
    ktp = numeric[:16].ljust(16, "0")
    phone = "08" + numeric[16:28].ljust(10, "0")
    return {
        "full_name": "Budi Santoso",
        "email": f"budi.{token}@luka.local",
        "employee_id": f"EMP-{token.upper()}",
        "ktp_id": ktp,
        "phone": phone,
        "department": "Produksi",
        "password": "Rahasia123",
        "consent": True,
    }


def _admin_token(client: TestClient) -> str:
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@luka.local")
    password = os.getenv("SEED_ADMIN_PASSWORD", "Admin#12345")
    response = client.post(f"{PREFIX}/login", json={"identifier": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["accessToken"]


def _approve(client: TestClient, registration_id: str, role: str = "Sample") -> None:
    token = _admin_token(client)
    approved = client.post(
        f"{PREFIX}/admin/registrations/{registration_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": role},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "active"


def _register_and_approve(
    client: TestClient, identity: dict[str, str], role: str = "Sample"
) -> None:
    created = client.post(f"{PREFIX}/register", json=identity)
    assert created.status_code == 201, created.text
    _approve(client, created.json()["registration_id"], role=role)


# ─── Registration ─────────────────────────────────────────────────────────────


def test_register_creates_pending_account(client: TestClient) -> None:
    identity = _unique_identity()
    response = client.post(f"{PREFIX}/register", json=identity)
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "pending"


def test_register_rejects_duplicate_identity(client: TestClient) -> None:
    identity = _unique_identity()
    assert client.post(f"{PREFIX}/register", json=identity).status_code == 201
    duplicate = client.post(f"{PREFIX}/register", json=identity)
    assert duplicate.status_code == 409


def test_register_rejects_invalid_ktp(client: TestClient) -> None:
    identity = _unique_identity()
    identity["ktp_id"] = "123"
    assert client.post(f"{PREFIX}/register", json=identity).status_code == 400


def test_register_requires_consent(client: TestClient) -> None:
    identity = _unique_identity()
    identity["consent"] = False
    assert client.post(f"{PREFIX}/register", json=identity).status_code == 400


# ─── Login gating ─────────────────────────────────────────────────────────────


def test_login_blocked_until_approved(client: TestClient) -> None:
    identity = _unique_identity()
    created = client.post(f"{PREFIX}/register", json=identity)
    assert created.status_code == 201, created.text

    pending = client.post(
        f"{PREFIX}/login",
        json={"identifier": identity["email"], "password": identity["password"]},
    )
    assert pending.status_code == 403

    _approve(client, created.json()["registration_id"])
    ok = client.post(
        f"{PREFIX}/login",
        json={"identifier": identity["employee_id"], "password": identity["password"]},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["actor"]["role"] == "Sample"


def test_login_rejects_wrong_password(client: TestClient) -> None:
    identity = _unique_identity()
    _register_and_approve(client, identity)
    bad = client.post(
        f"{PREFIX}/login",
        json={"identifier": identity["email"], "password": "WrongPass123"},
    )
    assert bad.status_code == 401


def test_me_requires_valid_token(client: TestClient) -> None:
    assert client.get(f"{PREFIX}/me").status_code == 401
    assert client.get(f"{PREFIX}/me", headers={"Authorization": "Bearer nope"}).status_code == 401


# ─── Change password ──────────────────────────────────────────────────────────


def test_change_password_revokes_session_and_updates_login(client: TestClient) -> None:
    identity = _unique_identity()
    _register_and_approve(client, identity)
    token = client.post(
        f"{PREFIX}/login",
        json={"identifier": identity["email"], "password": identity["password"]},
    ).json()["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    wrong = client.post(
        f"{PREFIX}/change-password",
        json={"current_password": "Nope12345", "new_password": "Baru12345"},
        headers=headers,
    )
    assert wrong.status_code == 401

    changed = client.post(
        f"{PREFIX}/change-password",
        json={"current_password": identity["password"], "new_password": "Baru12345"},
        headers=headers,
    )
    assert changed.status_code == 200, changed.text

    # Session revoked after password change.
    assert client.get(f"{PREFIX}/me", headers=headers).status_code == 401

    # New password works, old one does not.
    assert client.post(
        f"{PREFIX}/login", json={"identifier": identity["email"], "password": "Baru12345"}
    ).status_code == 200
    assert client.post(
        f"{PREFIX}/login", json={"identifier": identity["email"], "password": identity["password"]}
    ).status_code == 401


# ─── Forgot / reset password ──────────────────────────────────────────────────


def test_forgot_password_is_generic_for_unknown_identifier(client: TestClient) -> None:
    response = client.post(f"{PREFIX}/forgot-password", json={"identifier": "ghost@luka.local"})
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_forgot_and_reset_password_flow(client: TestClient, captured_email: dict[str, str]) -> None:
    identity = _unique_identity()
    _register_and_approve(client, identity)

    requested = client.post(f"{PREFIX}/forgot-password", json={"identifier": identity["email"]})
    assert requested.status_code == 200

    match = re.search(r"\b(\d{6})\b", captured_email.get("body", ""))
    assert match, "OTP not found in outbound email"
    otp = match.group(1)

    assert client.post(
        f"{PREFIX}/reset-password",
        json={"identifier": identity["email"], "otp": "000000", "new_password": "Reset12345"},
    ).status_code == 400

    reset = client.post(
        f"{PREFIX}/reset-password",
        json={"identifier": identity["email"], "otp": otp, "new_password": "Reset12345"},
    )
    assert reset.status_code == 200, reset.text

    assert client.post(
        f"{PREFIX}/login", json={"identifier": identity["email"], "password": "Reset12345"}
    ).status_code == 200


# ─── Admin approval authorization ─────────────────────────────────────────────


def test_admin_endpoints_forbidden_for_employee(client: TestClient) -> None:
    identity = _unique_identity()
    _register_and_approve(client, identity)
    token = client.post(
        f"{PREFIX}/login",
        json={"identifier": identity["email"], "password": identity["password"]},
    ).json()["accessToken"]

    forbidden = client.get(
        f"{PREFIX}/admin/registrations", headers={"Authorization": f"Bearer {token}"}
    )
    assert forbidden.status_code == 403


def test_admin_lists_and_rejects_registration(client: TestClient) -> None:
    identity = _unique_identity()
    created = client.post(f"{PREFIX}/register", json=identity)
    registration_id = created.json()["registration_id"]

    admin = _admin_token(client)
    headers = {"Authorization": f"Bearer {admin}"}

    listing = client.get(f"{PREFIX}/admin/registrations", headers=headers)
    assert listing.status_code == 200
    assert any(r["registration_id"] == registration_id for r in listing.json()["data"])

    rejected = client.post(
        f"{PREFIX}/admin/registrations/{registration_id}/reject", headers=headers
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    # Rejected account cannot log in.
    blocked = client.post(
        f"{PREFIX}/login",
        json={"identifier": identity["email"], "password": identity["password"]},
    )
    assert blocked.status_code == 403


def test_all_slide_04_demo_logins(client: TestClient) -> None:
    cases = [
        ("qc1", "qc12345", "QCInspector", "Budi Santoso (QC Inspector)"),
        ("finance1", "finance12345", "FinancePayroll", "Siti Rahma (Finance & Payroll)"),
        ("owner1", "owner12345", "Owner", "Bambang Wijaya (Owner/Eksekutif)"),
        ("sample1", "sample12345", "Sample", "Adis Pratama (Tim Sample)"),
        ("gudang1", "gudang12345", "Warehouse", "Joko Susilo (Gudang/Warehouse)"),
        ("mandor1", "mandor12345", "Mandor", "Asep Suryana (Kepala Produksi/Mandor)"),
        ("penjahit1", "penjahit12345", "Tailor", "Dewi Lestari (Penjahit/Tailor)"),
        ("klien1", "klien12345", "client", "Klien 1 (Nusantara Apparel)"),
        ("klien5", "klien54321", "client", "Klien 5 (Bumi Tekstil)"),
    ]
    for username, pwd, expected_role, expected_name in cases:
        res = client.post(
            f"{PREFIX}/login",
            json={"identifier": username, "password": pwd},
        )
        assert res.status_code == 200, f"Failed login for {username}"
        body = res.json()
        assert body["actor"]["role"] == expected_role, f"Role mismatch for {username}"
        assert body["actor"]["displayName"] == expected_name, f"Name mismatch for {username}"


# ─── RBAC: approval requires an assignable role ──────────────────────────────


def _pending_registration(client: TestClient) -> str:
    identity = _unique_identity()
    created = client.post(f"{PREFIX}/register", json=identity)
    assert created.status_code == 201, created.text
    return created.json()["registration_id"]


def _approve_raw(client: TestClient, registration_id: str, body: dict[str, object]):
    token = _admin_token(client)
    return client.post(
        f"{PREFIX}/admin/registrations/{registration_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )


def test_approve_without_role_is_rejected(client: TestClient) -> None:
    registration_id = _pending_registration(client)
    response = _approve_raw(client, registration_id, {})
    assert response.status_code == 422, response.text
    assert get_store().get_user(registration_id).status == "pending"


def test_approve_with_client_role_is_rejected(client: TestClient) -> None:
    registration_id = _pending_registration(client)
    response = _approve_raw(client, registration_id, {"role": "client"})
    assert response.status_code == 422, response.text


def test_approve_with_arbitrary_role_is_rejected(client: TestClient) -> None:
    registration_id = _pending_registration(client)
    response = _approve_raw(client, registration_id, {"role": "SuperUser"})
    assert response.status_code == 422, response.text


def test_approved_account_logs_in_with_assigned_role(client: TestClient) -> None:
    identity = _unique_identity()
    _register_and_approve(client, identity, role="Warehouse")
    login = client.post(
        f"{PREFIX}/login",
        json={"identifier": identity["email"], "password": identity["password"]},
    )
    assert login.status_code == 200, login.text
    assert login.json()["actor"]["role"] == "Warehouse"


def test_store_rejects_client_role_on_activation() -> None:
    user = get_store().seed_user(
        email=f"store.{uuid.uuid4().hex[:8]}@luka.local",
        password="Rahasia123",
        employee_id=f"STORE-{uuid.uuid4().hex[:8].upper()}",
        full_name="Store Level",
    )
    with pytest.raises(AuthError) as excinfo:
        get_store().set_status(user.user_id, "active", "client")
    assert excinfo.value.code == "INVALID_ROLE"


# ─── RBAC: roleless sessions are denied on every protected endpoint ──────────

SAMPLING_PREFIX = "/api/sampling-spec-rnd"


def _roleless_token() -> str:
    store = get_store()
    user = store.seed_user(
        email=f"roleless.{uuid.uuid4().hex[:8]}@luka.local",
        password="Rahasia123",
        employee_id=f"ROLELESS-{uuid.uuid4().hex[:8].upper()}",
        full_name="Roleless Session",
        role="employee",
    )
    token, _ = store.create_session(user.user_id, 3600)
    return token


def _iter_sampling_routes(routes, prefix: str = "") -> list[tuple[str, object]]:
    """Flatten FastAPI 0.141's nested ``_IncludedRouter`` tree into full paths.

    Included routers are no longer flattened into ``app.routes``; each nested
    router carries its parent prefix in ``include_context.prefix`` while leaf
    paths stay relative. Direct routes on a prefixed router already carry the
    full path, so only prepend when the leaf path is relative.
    """
    collected: list[tuple[str, object]] = []
    for route in routes:
        nested = getattr(route, "original_router", None)
        if nested is not None:
            context = route.include_context
            collected.extend(
                _iter_sampling_routes(nested.routes, prefix + (context.prefix or ""))
            )
        elif hasattr(route, "dependant"):
            full_path = (
                route.path
                if not prefix or route.path.startswith(prefix)
                else prefix + route.path
            )
            collected.append((full_path, route))
    return collected


def _sampling_routes() -> list[tuple[str, object]]:
    return [
        (path, route)
        for path, route in _iter_sampling_routes(app.routes)
        if path.startswith(SAMPLING_PREFIX) and path != f"{SAMPLING_PREFIX}/health"
    ]


def test_protected_routes_include_session_context() -> None:
    routes = _sampling_routes()
    assert routes, "no protected sampling routes discovered"
    for path, route in routes:
        calls = [dependency.call for dependency in route.dependant.dependencies]
        assert session_context in calls, f"{path} is missing session_context"


def test_roleless_token_forbidden_on_every_protected_route(client: TestClient) -> None:
    token = _roleless_token()
    headers = {"Authorization": f"Bearer {token}"}
    routes = _sampling_routes()
    assert routes, "no protected sampling routes discovered"
    for path, route in routes:
        method = next(iter(route.methods - {"HEAD", "OPTIONS"}))
        url = re.sub(r"\{[^}]+\}", str(uuid.uuid4()), path)
        response = client.request(method, url, headers=headers, json={})
        assert response.status_code == 403, (
            f"{method} {url} returned {response.status_code}: {response.text}"
        )


def test_health_route_is_public(client: TestClient) -> None:
    response = client.get(f"{SAMPLING_PREFIX}/health")
    assert response.status_code == 200, response.text


