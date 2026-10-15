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
from src.main import app

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


def _approve(client: TestClient, registration_id: str) -> None:
    token = _admin_token(client)
    approved = client.post(
        f"{PREFIX}/admin/registrations/{registration_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "active"


def _register_and_approve(client: TestClient, identity: dict[str, str]) -> None:
    created = client.post(f"{PREFIX}/register", json=identity)
    assert created.status_code == 201, created.text
    _approve(client, created.json()["registration_id"])


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
    assert ok.json()["actor"]["role"] == "employee"


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
