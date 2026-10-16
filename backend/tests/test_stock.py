import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api.v1.stock import (
    DEFAULT_MATERIAL_LOTS,
    issue_material,
    validate_material_dispatch,
)
from app.main import app
from app.core.database import get_db
from app.core.auth import create_access_token
from app.schemas.problem import ProblemException
from app.schemas.stock import MaterialIssueRequest, MaterialLot


LEGAL_OWNER_A = uuid.UUID("c0000000-0000-4000-8000-000000000001")
CLIENT_A = uuid.UUID("d0000000-0000-4000-8000-000000000001")
CLIENT_B = uuid.UUID("d0000000-0000-4000-8000-000000000002")
ORDER_A = uuid.UUID("e0000000-0000-4000-8000-000000000401")
ORDER_B = uuid.UUID("e0000000-0000-4000-8000-000000000402")
TENANT_A = uuid.UUID("b0000000-0000-4000-8000-000000000001")
ACTOR_A = uuid.UUID("f0000000-0000-4000-8000-000000000001")


class _AuthResult:
    def scalar_one_or_none(self):
        return uuid.uuid4()


class _AuthSession:
    def execute(self, _statement, _parameters=None):
        return _AuthResult()

    def close(self):
        pass


@pytest.fixture
def auth_client():
    def override_get_db():
        session = _AuthSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _token(role: str, tenant_id: uuid.UUID = TENANT_A) -> str:
    return create_access_token(
        {"sub": str(ACTOR_A), "roles": [role], "tenant_id": str(tenant_id)}
    )


def test_stock_schema_keeps_scope_dimensions_separate() -> None:
    lot = DEFAULT_MATERIAL_LOTS[0]

    assert lot.tenantId != lot.legalStockOwnerId
    assert lot.legalStockOwnerId == LEGAL_OWNER_A
    assert lot.orderBeneficiaryId == CLIENT_A

    request = MaterialIssueRequest(
        materialLotId=lot.id,
        orderId=ORDER_B,
        quantity={"value": "2", "unit": "METER"},
    )
    assert request.orderId == ORDER_B
    assert request.materialLotId == lot.id


def test_mismatched_dispatch_rejected_before_quantity_mutation() -> None:
    lot = DEFAULT_MATERIAL_LOTS[0]
    starting_quantity = lot.quantity

    with pytest.raises(ProblemException) as error:
        validate_material_dispatch(lot, ORDER_B)

    assert error.value.status == 409
    assert error.value.code == "ORDER_BENEFICIARY_MISMATCH"
    assert lot.quantity == starting_quantity


def test_matched_dispatch_is_blocked_when_no_persistence_exists() -> None:
    lot = DEFAULT_MATERIAL_LOTS[0]

    with pytest.raises(ProblemException) as error:
        asyncio.run(
            issue_material(
                MaterialIssueRequest(
                    materialLotId=lot.id,
                    orderId=ORDER_A,
                    quantity={"value": "2", "unit": "METER"},
                )
            )
        )

    assert error.value.code == "INVALID_STATE"
    assert lot.legalStockOwnerId == LEGAL_OWNER_A
    assert lot.orderBeneficiaryId == CLIENT_A


def test_stock_routes_are_present_in_generated_openapi() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/stock" in paths
    assert "/api/v1/material-issuances" in paths
    assert paths["/api/v1/material-issuances"]["post"]["operationId"] == "issueMaterial"


def test_stock_routes_require_authentication(auth_client: TestClient) -> None:
    assert auth_client.get("/api/v1/stock").status_code == 401
    assert auth_client.post("/api/v1/material-issuances", json={}).status_code == 401


def test_stock_read_is_tenant_scoped_and_ignores_expanding_tenant_filter(
    auth_client: TestClient,
) -> None:
    headers = {"Authorization": f"Bearer {_token('Warehouse')}"}

    own_scope = auth_client.get("/api/v1/stock", headers=headers)
    assert own_scope.status_code == 200
    assert all(item["tenantId"] == str(TENANT_A) for item in own_scope.json()["items"])

    other_tenant = auth_client.get(
        "/api/v1/stock",
        params={"tenantId": "b0000000-0000-4000-8000-000000000002"},
        headers=headers,
    )
    assert other_tenant.status_code == 200
    assert other_tenant.json()["items"] == []


@pytest.mark.parametrize("role", ["MaklonClient", "FinancePayroll", "Tailor"])
def test_stock_rejects_roles_without_route_capability(
    auth_client: TestClient,
    role: str,
) -> None:
    headers = {"Authorization": f"Bearer {_token(role)}"}
    assert auth_client.get("/api/v1/stock", headers=headers).status_code == 403
    assert auth_client.post(
        "/api/v1/material-issuances",
        json={"materialLotId": str(DEFAULT_MATERIAL_LOTS[0].id), "orderId": str(ORDER_A)},
        headers=headers,
    ).status_code == 403


def test_authorized_issuance_keeps_mismatch_rejection_before_invalid_state(
    auth_client: TestClient,
) -> None:
    response = auth_client.post(
        "/api/v1/material-issuances",
        json={
            "materialLotId": str(DEFAULT_MATERIAL_LOTS[0].id),
            "orderId": str(ORDER_B),
            "quantity": {"value": "2", "unit": "METER"},
        },
        headers={"Authorization": f"Bearer {_token('Warehouse')}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "ORDER_BENEFICIARY_MISMATCH"
