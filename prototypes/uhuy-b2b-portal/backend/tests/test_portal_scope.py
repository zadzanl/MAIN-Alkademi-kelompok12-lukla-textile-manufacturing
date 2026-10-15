"""Client-scope isolation tests for the UHUY B2B external portal.

The core invariant of the external portal is that a client session can only ever
observe and mutate its own ``client_id`` data (RBAC "Klien Maklon/Ext"; AT-R08).
These tests pin that boundary using the seeded demo clients A and B.

Run:  pytest -q   (from the backend/ directory)
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.seed import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_PASSWORD,
    DEMO_CLIENT_A_EMAIL,
    DEMO_CLIENT_A_ID,
    DEMO_CLIENT_A_ORDER,
    DEMO_CLIENT_A_PASSWORD,
    DEMO_CLIENT_B_EMAIL,
    DEMO_CLIENT_B_ORDER,
    DEMO_CLIENT_B_PASSWORD,
)

AUTH = "/api/portal/auth"
API = "/api/portal"


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def _login(client: TestClient, identifier: str, password: str) -> dict[str, str]:
    response = client.post(
        f"{AUTH}/login", json={"identifier": identifier, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


def _client_a(client: TestClient) -> dict[str, str]:
    return _login(client, DEMO_CLIENT_A_EMAIL, DEMO_CLIENT_A_PASSWORD)


def _client_b(client: TestClient) -> dict[str, str]:
    return _login(client, DEMO_CLIENT_B_EMAIL, DEMO_CLIENT_B_PASSWORD)


def _admin(client: TestClient) -> dict[str, str]:
    return _login(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD)


# ─── Read isolation ───────────────────────────────────────────────────────────


def test_orders_are_scoped_to_own_client(client: TestClient) -> None:
    a = client.get(f"{API}/orders", headers=_client_a(client))
    assert a.status_code == 200, a.text
    ids = {row["order_id"] for row in a.json()["data"]}
    assert DEMO_CLIENT_A_ORDER in ids
    assert DEMO_CLIENT_B_ORDER not in ids
    assert all(row["client_id"] == DEMO_CLIENT_A_ID for row in a.json()["data"])


def test_client_cannot_fetch_other_clients_order(client: TestClient) -> None:
    # Client A explicitly asks for Client B's order id.
    response = client.get(f"{API}/orders/{DEMO_CLIENT_B_ORDER}", headers=_client_a(client))
    assert response.status_code == 404


def test_stock_is_scoped_to_own_client(client: TestClient) -> None:
    a = client.get(f"{API}/stock", headers=_client_a(client))
    b = client.get(f"{API}/stock", headers=_client_b(client))
    assert a.status_code == 200 and b.status_code == 200
    a_codes = {row["material_code"] for row in a.json()["data"]}
    b_codes = {row["material_code"] for row in b.json()["data"]}
    assert a_codes.isdisjoint(b_codes)
    assert all(row["client_id"] == DEMO_CLIENT_A_ID for row in a.json()["data"])


# ─── Write isolation ──────────────────────────────────────────────────────────


def test_order_request_is_created_for_own_client_only(client: TestClient) -> None:
    a_headers = _client_a(client)
    created = client.post(
        f"{API}/requests/order",
        headers=a_headers,
        json={
            "article_name": "Kaos Raglan Custom",
            "quantity": 300,
            "scheme": "CMT",
            "target_date": "2026-12-10",
            "notes": "Warna navy",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "submitted"

    a_requests = client.get(f"{API}/requests", headers=a_headers).json()["data"]
    assert any(r["article_name"] == "Kaos Raglan Custom" for r in a_requests)
    assert all(r["client_id"] == DEMO_CLIENT_A_ID for r in a_requests)

    b_requests = client.get(f"{API}/requests", headers=_client_b(client)).json()["data"]
    assert all(r["article_name"] != "Kaos Raglan Custom" for r in b_requests)


def test_sample_request_created_and_listed(client: TestClient) -> None:
    a_headers = _client_a(client)
    created = client.post(
        f"{API}/requests/sample",
        headers=a_headers,
        json={"article_name": "Hoodie Sample v1", "notes": "Bahan fleece"},
    )
    assert created.status_code == 201, created.text

    a_requests = client.get(f"{API}/requests", headers=a_headers).json()["data"]
    assert any(
        r["kind"] == "sample" and r["article_name"] == "Hoodie Sample v1" for r in a_requests
    )


# ─── Validation & authorization ───────────────────────────────────────────────


def test_order_request_rejects_invalid_scheme(client: TestClient) -> None:
    response = client.post(
        f"{API}/requests/order",
        headers=_client_a(client),
        json={"article_name": "X", "quantity": 10, "scheme": "BOGUS"},
    )
    assert response.status_code == 400


def test_order_request_rejects_non_positive_quantity(client: TestClient) -> None:
    response = client.post(
        f"{API}/requests/order",
        headers=_client_a(client),
        json={"article_name": "X", "quantity": 0, "scheme": "CMT"},
    )
    assert response.status_code == 422


def test_data_endpoints_require_auth(client: TestClient) -> None:
    assert client.get(f"{API}/orders").status_code == 401
    assert client.get(f"{API}/stock").status_code == 401


def test_admin_cannot_use_client_data_endpoints(client: TestClient) -> None:
    response = client.get(f"{API}/orders", headers=_admin(client))
    assert response.status_code == 403


def test_summary_matches_own_orders(client: TestClient) -> None:
    a = client.get(f"{API}/summary", headers=_client_a(client))
    assert a.status_code == 200
    summary = a.json()["summary"]
    orders = client.get(f"{API}/orders", headers=_client_a(client)).json()["data"]
    assert summary["total_orders"] == len(orders)
