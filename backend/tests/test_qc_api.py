"""QC & MES API conformance: `inspectUnit` and `listAssemblies` against a real PostgreSQL.

The assembly, allocation, and inspection tables are M007. The `orders` (M004) and `garment_units`
(M006) prerequisites are not authored yet, so `PREREQUISITES` below stands in for them with the
column lists frozen in `11-database-schema-spec.md` §2. It is test scaffolding, not a migration,
and it disappears when those migrations land; the M007 invariant suite uses the same stand-in.

Run it against a reachable server::

    QC_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/postgres pytest -q backend/tests/test_qc_api.py

Without a reachable server the module skips, so it stays green on a runner with no database.
"""

import json
import os
import uuid
from pathlib import Path
from typing import Any, Iterator, Optional

import pytest

try:
    import psycopg2
except ImportError:  # pragma: no cover - the driver is a test-only prerequisite
    psycopg2 = None

SCHEMA = "qc_api_verify"
MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
ADMIN_DSN = os.getenv("QC_TEST_DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/postgres")
APP_DSN = os.getenv(
    "QC_TEST_APP_DATABASE_URL", "postgresql://lukla_app:lukla_secret@127.0.0.1:5432/postgres"
)


def sqlalchemy_url(dsn: str) -> str:
    return dsn.replace("postgresql://", "postgresql+psycopg2://", 1)


# The app builds its engine while it is imported, and this suite overrides that session anyway.
# Point it at the driver this suite installs (psycopg2) unless the caller already chose one.
os.environ.setdefault("DATABASE_URL", sqlalchemy_url(ADMIN_DSN))
os.environ.setdefault("LUKLA_APP_DATABASE_URL", sqlalchemy_url(APP_DSN))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.auth import create_access_token
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.main import app

pytestmark = pytest.mark.skipif(
    psycopg2 is None, reason="the QC API suite needs psycopg2 to build its throwaway schema"
)

PREREQUISITES = """
CREATE TABLE orders (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    order_number text NOT NULL,
    beneficiary_tenant_id uuid NOT NULL,
    scheme text NOT NULL CHECK (scheme IN ('CMT', 'SEMI_CMT', 'FULL_PACKAGE')),
    status text NOT NULL,
    timezone text NOT NULL DEFAULT 'Asia/Jakarta',
    cutoff_local time NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id),
    CONSTRAINT uq_orders_number UNIQUE (tenant_id, order_number)
);

CREATE TABLE garment_units (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    order_id uuid NOT NULL,
    component_code text NOT NULL,
    source_tally_id uuid NULL,
    operator_id uuid NOT NULL,
    status text NOT NULL DEFAULT 'MENUNGGU_QC'
        CHECK (status IN ('MENUNGGU_QC', 'QC_PASS', 'REWORK', 'REJECT_SCRAP', 'ASSEMBLED')),
    piece_rate_snapshot_id uuid NULL,
    wage_credited_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, id)
);
"""

TENANT_A = "11111111-1111-4111-8111-111111111111"
TENANT_B = "22222222-2222-4222-8222-222222222222"
INSPECTOR = "33333333-3333-4333-8333-333333333333"
ORDER_A = "44444444-4444-4444-8444-444444444444"
ORDER_B = "44444444-4444-4444-8444-444444444445"
ASSEMBLY_A = "55555555-5555-4555-8555-555555555555"
ASSEMBLY_A_ASSEMBLING = "55555555-5555-4555-8555-555555555556"
ASSEMBLY_A_EMPTY = "55555555-5555-4555-8555-555555555557"
ASSEMBLY_A_SECOND = "55555555-5555-4555-8555-555555555558"
ASSEMBLY_B = "66666666-6666-4666-8666-666666666666"
PIECES_A = (
    "77777777-7777-4777-8777-777777777771",
    "77777777-7777-4777-8777-777777777772",
    "77777777-7777-4777-8777-777777777773",
)
PIECE_A_SECOND_ASSEMBLY = "77777777-7777-4777-8777-777777777774"
PIECE_B = "88888888-8888-4888-8888-888888888888"
UNKNOWN_ASSEMBLY = "99999999-9999-4999-8999-999999999999"

KEY = "qc-api-test-key-0001"
OTHER_KEY = "qc-api-test-key-0002"


class AdminDatabase:
    """Statement-per-connection helper for schema setup and assertions as the owner role."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def execute(self, sql: str, params: Optional[tuple[Any, ...]] = None) -> list[tuple[Any, ...]]:
        connection = psycopg2.connect(self.dsn)
        connection.autocommit = True
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path = {SCHEMA}")
                cursor.execute(sql, params)
                return cursor.fetchall() if cursor.description else []
        finally:
            connection.close()


def _seed(database: AdminDatabase) -> None:
    database.execute(
        """
        INSERT INTO tenants (id, tenant_code, name, kind) VALUES
            (%s, 'QC_API_A', 'Tenant A Fabrics', 'CLIENT'),
            (%s, 'QC_API_B', 'Tenant B Garments', 'CLIENT');
        """,
        (TENANT_A, TENANT_B),
    )
    database.execute(
        "INSERT INTO actors (id, email, display_name) VALUES (%s, 'qc-api@lukla.test', 'QC Inspector')",
        (INSPECTOR,),
    )
    database.execute(
        """
        INSERT INTO orders (id, tenant_id, order_number, beneficiary_tenant_id, scheme, status)
        VALUES (%s, %s, 'ORD-A-1', %s, 'CMT', 'CONFIRMED'),
               (%s, %s, 'ORD-B-1', %s, 'CMT', 'CONFIRMED')
        """,
        (ORDER_A, TENANT_A, TENANT_A, ORDER_B, TENANT_B, TENANT_B),
    )
    database.execute(
        """
        INSERT INTO garment_units (id, tenant_id, order_id, component_code, operator_id)
        SELECT piece, %s, %s, 'SLEEVE', %s FROM unnest(%s::uuid[]) AS piece
        """,
        (TENANT_A, ORDER_A, INSPECTOR, list(PIECES_A) + [PIECE_A_SECOND_ASSEMBLY]),
    )
    database.execute(
        """
        INSERT INTO garment_units (id, tenant_id, order_id, component_code, operator_id)
        VALUES (%s, %s, %s, 'SLEEVE', %s)
        """,
        (PIECE_B, TENANT_B, ORDER_B, INSPECTOR),
    )
    database.execute(
        """
        INSERT INTO garment_assemblies (id, tenant_id, order_id, serial_code, status) VALUES
            (%s, %s, %s, 'A-1', 'MENUNGGU_QC'),
            (%s, %s, %s, 'A-2', 'ASSEMBLING'),
            (%s, %s, %s, 'A-3', 'MENUNGGU_QC'),
            (%s, %s, %s, 'A-4', 'MENUNGGU_QC'),
            (%s, %s, %s, 'B-1', 'MENUNGGU_QC')
        """,
        (
            ASSEMBLY_A, TENANT_A, ORDER_A,
            ASSEMBLY_A_ASSEMBLING, TENANT_A, ORDER_A,
            ASSEMBLY_A_EMPTY, TENANT_A, ORDER_A,
            ASSEMBLY_A_SECOND, TENANT_A, ORDER_A,
            ASSEMBLY_B, TENANT_B, ORDER_B,
        ),
    )
    database.execute(
        """
        INSERT INTO assembly_components (tenant_id, assembly_id, garment_unit_id, component_code)
        SELECT %s, %s, piece, 'SLEEVE' FROM unnest(%s::uuid[]) AS piece
        """,
        (TENANT_A, ASSEMBLY_A, list(PIECES_A)),
    )
    for tenant_id, assembly_id, piece in (
        (TENANT_A, ASSEMBLY_A_SECOND, PIECE_A_SECOND_ASSEMBLY),
        (TENANT_B, ASSEMBLY_B, PIECE_B),
    ):
        database.execute(
            """
            INSERT INTO assembly_components
                (tenant_id, assembly_id, garment_unit_id, component_code)
            VALUES (%s, %s, %s, 'SLEEVE')
            """,
            (tenant_id, assembly_id, piece),
        )


@pytest.fixture(scope="module")
def admin() -> Iterator[AdminDatabase]:
    """A throwaway schema holding M001, the M004/M006 stand-ins, and M007."""
    database = AdminDatabase(ADMIN_DSN)
    try:
        psycopg2.connect(ADMIN_DSN).close()
    except psycopg2.Error as exc:  # pragma: no cover - depends on the local machine
        pytest.skip(f"PostgreSQL is not reachable at {ADMIN_DSN}: {exc}")

    database.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
    database.execute(f"CREATE SCHEMA {SCHEMA}")
    database.execute((MIGRATIONS / "001_identities.sql").read_text(encoding="utf-8"))
    database.execute(f"GRANT USAGE ON SCHEMA {SCHEMA} TO lukla_app")
    database.execute(PREREQUISITES)
    database.execute((MIGRATIONS / "007_assemblies_and_qc.sql").read_text(encoding="utf-8"))
    _seed(database)
    try:
        yield database
    finally:
        database.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")


@pytest.fixture
def reset_state(admin: AdminDatabase) -> AdminDatabase:
    """Every test starts from the seeded queue, an empty log, and no reserved keys."""
    admin.execute("TRUNCATE qc_defects, qc_inspections, idempotency_records")
    admin.execute("UPDATE garment_units SET status = 'MENUNGGU_QC'")
    admin.execute("UPDATE garment_assemblies SET status = 'MENUNGGU_QC'")
    admin.execute(
        "UPDATE garment_assemblies SET status = 'ASSEMBLING' WHERE id = %s",
        (ASSEMBLY_A_ASSEMBLING,),
    )
    return admin


@pytest.fixture(autouse=True)
def taxonomy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Deployment-managed taxonomy: a default list, and tenant B replacing it."""
    path = tmp_path / "defect_taxonomy.json"
    path.write_text(
        json.dumps({"default": ["broken stitch", "puckering"], "tenants": {TENANT_B: ["hole"]}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "QC_DEFECT_TAXONOMY_PATH", str(path))


@pytest.fixture
def client(reset_state: AdminDatabase) -> Iterator[TestClient]:
    """The real app, wired to the runtime role `lukla_app` against the throwaway schema."""
    engine = create_engine(
        sqlalchemy_url(APP_DSN),
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={SCHEMA},public"},
    )
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db() -> Iterator[Any]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def token(tenant_id: str, *roles: str) -> str:
    return create_access_token({"sub": INSPECTOR, "roles": list(roles), "tenant_id": tenant_id})


def inspector_token(tenant_id: str = TENANT_A) -> str:
    return token(tenant_id, "QCInspector")


def headers(token_value: str, key: str = KEY) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_value}", "Idempotency-Key": key}


def inspection_body(
    disposition: str = "PASS",
    defects: Optional[list[dict[str, Any]]] = None,
    assembly_id: str = ASSEMBLY_A,
) -> dict[str, Any]:
    return {
        "assemblyId": assembly_id,
        "disposition": disposition,
        "defects": defects if defects is not None else [],
    }


def defect(piece: str, code: str = "puckering") -> dict[str, Any]:
    return {"componentUnitId": piece, "code": code, "notes": None}


def inspections(admin: AdminDatabase) -> list[tuple[str, str, int, str]]:
    return [
        (str(assembly_id), disposition, sequence_no, key)
        for assembly_id, disposition, sequence_no, key in admin.execute(
            "SELECT assembly_id, disposition, sequence_no, idempotency_key"
            " FROM qc_inspections ORDER BY sequence_no"
        )
    ]


def defects(admin: AdminDatabase) -> list[tuple[str, str]]:
    return [
        (code, str(unit_id))
        for code, unit_id in admin.execute(
            "SELECT defect_code, garment_unit_id FROM qc_defects ORDER BY defect_code"
        )
    ]


# ---------------------------------------------------------------------------
# inspectUnit
# ---------------------------------------------------------------------------


def test_repair_records_the_defect_and_moves_the_assembly_and_its_pieces(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    response = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REPAIR", [defect(PIECES_A[0]), defect(PIECES_A[1], "broken stitch")]),
        headers=headers(inspector_token()),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["assemblyId"] == ASSEMBLY_A
    assert body["disposition"] == "REPAIR"
    assert [item["componentUnitId"] for item in body["defects"]] == [PIECES_A[0], PIECES_A[1]]
    assert uuid.UUID(body["id"])

    assert defects(reset_state) == [("broken stitch", PIECES_A[1]), ("puckering", PIECES_A[0])]
    assert inspections(reset_state) == [(ASSEMBLY_A, "REPAIR", 1, KEY)]
    assert reset_state.execute(
        "SELECT status FROM garment_assemblies WHERE id = %s", (ASSEMBLY_A,)
    ) == [("REWORK",)]
    assert reset_state.execute(
        "SELECT DISTINCT status FROM garment_units WHERE id = ANY(%s::uuid[])", (list(PIECES_A),)
    ) == [("REWORK",)]


def test_rework_is_re_inspectable_and_sequences_increment(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    first = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REPAIR", [defect(PIECES_A[0])]),
        headers=headers(inspector_token(), "qc-api-test-key-0010"),
    )
    second = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("PASS"),
        headers=headers(inspector_token(), "qc-api-test-key-0011"),
    )

    assert (first.status_code, second.status_code) == (201, 201)
    assert [row[2] for row in inspections(reset_state)] == [1, 2]
    assert reset_state.execute(
        "SELECT status FROM garment_assemblies WHERE id = %s", (ASSEMBLY_A,)
    ) == [("QC_PASS",)]
    assert reset_state.execute(
        "SELECT DISTINCT status FROM garment_units WHERE id = ANY(%s::uuid[])", (list(PIECES_A),)
    ) == [("QC_PASS",)]


def test_a_final_pass_cannot_be_overridden(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    passed = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("PASS"),
        headers=headers(inspector_token(), "qc-api-test-key-0020"),
    )
    override = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REJECT", [defect(PIECES_A[0])]),
        headers=headers(inspector_token(), "qc-api-test-key-0021"),
    )

    assert passed.status_code == 201
    assert override.status_code == 409
    assert override.json()["code"] == "INVALID_STATE"
    assert len(inspections(reset_state)) == 1


def test_an_assembly_still_assembling_is_refused(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    response = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("PASS", assembly_id=ASSEMBLY_A_ASSEMBLING),
        headers=headers(inspector_token()),
    )

    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATE"
    assert inspections(reset_state) == []


def test_an_assembly_without_allocated_pieces_is_refused(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    response = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("PASS", assembly_id=ASSEMBLY_A_EMPTY),
        headers=headers(inspector_token()),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert inspections(reset_state) == []


def test_an_unknown_assembly_is_refused(client: TestClient, reset_state: AdminDatabase) -> None:
    response = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("PASS", assembly_id=UNKNOWN_ASSEMBLY),
        headers=headers(inspector_token()),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert inspections(reset_state) == []


def test_a_repair_without_a_defect_is_refused(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    response = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REPAIR"),
        headers=headers(inspector_token()),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert inspections(reset_state) == []


def test_a_pass_with_a_defect_is_refused(client: TestClient, reset_state: AdminDatabase) -> None:
    response = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("PASS", [defect(PIECES_A[0])]),
        headers=headers(inspector_token()),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert inspections(reset_state) == []


def test_a_defect_on_a_piece_of_another_assembly_is_refused(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    response = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REPAIR", [defect(PIECE_A_SECOND_ASSEMBLY)]),
        headers=headers(inspector_token()),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert inspections(reset_state) == []


def test_an_unknown_defect_code_is_refused_naming_the_code(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    response = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REJECT", [defect(PIECES_A[0], "invented defect")]),
        headers=headers(inspector_token()),
    )

    assert response.status_code == 400
    assert "invented defect" in response.json()["detail"]
    assert inspections(reset_state) == []


def test_a_tenant_taxonomy_replaces_the_default(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    """Tenant B configures `hole`; the default list must not leak into its inspections."""
    default_code = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REJECT", [defect(PIECE_B, "puckering")], assembly_id=ASSEMBLY_B),
        headers=headers(inspector_token(TENANT_B)),
    )
    overridden = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REJECT", [defect(PIECE_B, "hole")], assembly_id=ASSEMBLY_B),
        headers=headers(inspector_token(TENANT_B), "qc-api-test-key-0030"),
    )

    assert default_code.status_code == 400
    assert "puckering" in default_code.json()["detail"]
    assert overridden.status_code == 201
    assert len(inspections(reset_state)) == 1


def test_a_replayed_delivery_returns_the_stored_decision_once(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    body = inspection_body("REPAIR", [defect(PIECES_A[0])])
    first = client.post("/api/v1/qc-inspections", json=body, headers=headers(inspector_token()))
    replay = client.post("/api/v1/qc-inspections", json=body, headers=headers(inspector_token()))

    assert (first.status_code, replay.status_code) == (201, 201)
    assert first.json() == replay.json()
    assert len(inspections(reset_state)) == 1


def test_a_changed_payload_on_a_reused_key_conflicts(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    first = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REPAIR", [defect(PIECES_A[0])]),
        headers=headers(inspector_token()),
    )
    conflict = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REPAIR", [defect(PIECES_A[1])]),
        headers=headers(inspector_token()),
    )

    assert first.status_code == 201
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"
    assert len(inspections(reset_state)) == 1


def test_a_retry_of_the_delivery_that_passed_is_not_an_override(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    body = inspection_body("PASS")
    passed = client.post("/api/v1/qc-inspections", json=body, headers=headers(inspector_token()))
    retry = client.post("/api/v1/qc-inspections", json=body, headers=headers(inspector_token()))

    assert (passed.status_code, retry.status_code) == (201, 201)
    assert retry.json() == passed.json()
    assert len(inspections(reset_state)) == 1


def test_inspection_requires_the_qc_inspector_role(
    client: TestClient, reset_state: AdminDatabase
) -> None:
    forbidden = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("PASS"),
        headers=headers(token(TENANT_A, "Tailor")),
    )
    unauthenticated = client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("PASS"),
        headers={"Idempotency-Key": KEY},
    )

    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "FORBIDDEN"
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["code"] == "AUTH_REQUIRED"
    assert inspections(reset_state) == []


# ---------------------------------------------------------------------------
# listAssemblies
# ---------------------------------------------------------------------------


def test_the_queue_returns_the_tenant_assemblies_with_their_pieces(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/assemblies", headers=headers(inspector_token(), OTHER_KEY))

    assert response.status_code == 200
    items = {item["id"]: item for item in response.json()["items"]}
    assert set(items) == {
        ASSEMBLY_A,
        ASSEMBLY_A_ASSEMBLING,
        ASSEMBLY_A_EMPTY,
        ASSEMBLY_A_SECOND,
    }
    assert items[ASSEMBLY_A]["componentUnitIds"] == list(PIECES_A)
    assert items[ASSEMBLY_A]["status"] == "MENUNGGU_QC"
    assert items[ASSEMBLY_A]["serialCode"] == "A-1"
    assert items[ASSEMBLY_A]["orderId"] == ORDER_A


def test_the_queue_filters_by_status(client: TestClient) -> None:
    waiting = client.get(
        "/api/v1/assemblies",
        params={"status": "MENUNGGU_QC"},
        headers=headers(inspector_token(), OTHER_KEY),
    )
    empty = client.get(
        "/api/v1/assemblies",
        params={"status": "REWORK"},
        headers=headers(inspector_token(), OTHER_KEY),
    )

    assert waiting.status_code == 200
    assert len(waiting.json()["items"]) == 3
    assert ASSEMBLY_A_ASSEMBLING not in {item["id"] for item in waiting.json()["items"]}
    assert empty.status_code == 200
    assert empty.json()["items"] == []


def test_the_queue_follows_the_disposition(client: TestClient) -> None:
    client.post(
        "/api/v1/qc-inspections",
        json=inspection_body("REPAIR", [defect(PIECES_A[0])]),
        headers=headers(inspector_token()),
    )
    response = client.get(
        "/api/v1/assemblies",
        params={"status": "REWORK"},
        headers=headers(inspector_token(), OTHER_KEY),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [ASSEMBLY_A]


def test_the_queue_rejects_a_status_outside_the_contract(client: TestClient) -> None:
    response = client.get(
        "/api/v1/assemblies",
        params={"status": "NOT_A_STATUS"},
        headers=headers(inspector_token(), OTHER_KEY),
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_the_queue_requires_a_production_or_qc_role(client: TestClient) -> None:
    response = client.get(
        "/api/v1/assemblies", headers=headers(token(TENANT_A, "Tailor"), OTHER_KEY)
    )

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
