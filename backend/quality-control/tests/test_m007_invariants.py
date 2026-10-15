"""M007 invariants: the assembly, inspection, and defect rules as PostgreSQL enforces them.

The state machine, the append-only log, and the defect rules are database invariants, not only
service behaviour, so they are verified here against a real PostgreSQL instance in a throwaway
schema. The service tests in the rest of this suite prove the same rules at the domain layer;
this module proves the database refuses to be talked out of them.

The prerequisite tables M004 (``orders``) and M006 (``garment_units``) are not authored yet, so
``PREREQUISITES`` below stands in for them with the column lists frozen in
``11-database-schema-spec.md`` §2. It is test scaffolding, not a migration, and it disappears
when those migrations land.

Run it against a reachable server::

    QC_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/postgres pytest -q

Without a reachable server the module skips, which keeps the blocking CI job green on a runner
that has no database.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 is required by the M007 invariant test")

ADMIN_DSN = os.getenv("QC_TEST_DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/postgres")
APP_DSN = os.getenv(
    "QC_TEST_APP_DATABASE_URL", "postgresql://lukla_app:lukla_secret@127.0.0.1:5432/postgres"
)

SCHEMA = "qc_verify"
MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"

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
ASSEMBLY_B = "66666666-6666-4666-8666-666666666666"
PIECES_A = [
    "77777777-7777-4777-8777-777777777771",
    "77777777-7777-4777-8777-777777777772",
    "77777777-7777-4777-8777-777777777773",
]
PIECE_B = "88888888-8888-4888-8888-888888888888"
UNKNOWN_ID = "99999999-9999-4999-8999-999999999999"


class Database:
    """A tiny psycopg2 helper: one connection per statement, autocommit by default."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def connect(self) -> Any:
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"SET search_path = {SCHEMA}")
        return conn

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> list[tuple[Any, ...]]:
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall() if cur.description else []
        finally:
            conn.close()

    @contextmanager
    def transaction(self, tenant_id: str | None = None) -> Iterator[Any]:
        """One transaction on one connection, so a deferred constraint can fire at COMMIT."""
        conn = self.connect()
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                if tenant_id is not None:
                    cur.execute("SELECT set_request_context(%s)", (tenant_id,))
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def query_for(
        self, tenant_id: str, sql: str, params: tuple[Any, ...] | None = None
    ) -> list[tuple[Any, ...]]:
        """Read as a tenant: the row level security policy needs an installed context."""
        with self.transaction(tenant_id) as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() if cur.description else []

    def error(self, sql: str, params: tuple[Any, ...] | None = None) -> str:
        """Run a statement that must fail, and return its message."""
        return self._expect_error(lambda: self.execute(sql, params))

    def error_for(self, tenant_id: str, sql: str, params: tuple[Any, ...] | None = None) -> str:
        return self._expect_error(lambda: self.query_for(tenant_id, sql, params))

    @staticmethod
    def _expect_error(action: Any) -> str:
        try:
            action()
        except psycopg2.Error as exc:
            return str(exc)
        raise AssertionError("the statement was expected to fail and did not")


def _seed(database: Database) -> None:
    database.execute(
        """
        INSERT INTO tenants (id, tenant_code, name, kind) VALUES
            (%s, 'TENANT_A', 'Tenant A Fabrics', 'CLIENT'),
            (%s, 'TENANT_B', 'Tenant B Garments', 'CLIENT');
        """,
        (TENANT_A, TENANT_B),
    )
    database.execute(
        "INSERT INTO actors (id, email, display_name) VALUES (%s, 'qc@lukla.test', 'QC Inspector')",
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
        (TENANT_A, ORDER_A, INSPECTOR, PIECES_A),
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
            (%s, %s, %s, 'B-1', 'MENUNGGU_QC')
        """,
        (
            ASSEMBLY_A,
            TENANT_A,
            ORDER_A,
            ASSEMBLY_A_ASSEMBLING,
            TENANT_A,
            ORDER_A,
            ASSEMBLY_B,
            TENANT_B,
            ORDER_B,
        ),
    )
    database.execute(
        """
        INSERT INTO assembly_components (tenant_id, assembly_id, garment_unit_id, component_code)
        SELECT %s, %s, piece, 'SLEEVE' FROM unnest(%s::uuid[]) AS piece
        """,
        (TENANT_A, ASSEMBLY_A, PIECES_A),
    )
    database.execute(
        """
        INSERT INTO assembly_components (tenant_id, assembly_id, garment_unit_id, component_code)
        VALUES (%s, %s, %s, 'SLEEVE')
        """,
        (TENANT_B, ASSEMBLY_B, PIECE_B),
    )


@pytest.fixture
def admin() -> Iterator[Database]:
    """A throwaway schema holding M001, the M004/M006 stand-ins, and M007."""
    database = Database(ADMIN_DSN)
    try:
        database.connect().close()
    except psycopg2.Error as exc:  # pragma: no cover - depends on the local machine
        pytest.skip(f"PostgreSQL is not reachable at {ADMIN_DSN}: {exc}")

    database.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
    database.execute(f"CREATE SCHEMA {SCHEMA}")
    # 001 creates the lukla_app role and the identity tables the rest depends on.
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
def app(admin: Database) -> Iterator[Database]:
    """The runtime role the API actually connects as."""
    database = Database(APP_DSN)
    try:
        database.connect().close()
    except psycopg2.Error as exc:  # pragma: no cover - depends on the local machine
        pytest.skip(f"lukla_app cannot connect to {APP_DSN}: {exc}")
    yield database


def inspect(assembly_id: str, disposition: str, key: str = "key-1") -> tuple[str, tuple[Any, ...]]:
    return (
        """
        INSERT INTO qc_inspections
            (tenant_id, assembly_id, inspector_id, disposition, idempotency_key)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, sequence_no
        """,
        (TENANT_A, assembly_id, INSPECTOR, disposition, key),
    )


DEFECT_SQL = """
INSERT INTO qc_defects (tenant_id, inspection_id, garment_unit_id, defect_code)
SELECT %s, id, %s, %s FROM qc_inspections
WHERE tenant_id = %s AND assembly_id = %s
"""


def test_the_first_inspection_takes_sequence_one_and_moves_the_assembly_and_its_pieces(
    admin: Database,
) -> None:
    with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "PASS"))
        _, sequence_no = cur.fetchone()

    assert sequence_no == 1
    assert admin.execute(
        "SELECT status FROM garment_assemblies WHERE tenant_id = %s AND id = %s",
        (TENANT_A, ASSEMBLY_A),
    ) == [("QC_PASS",)]
    assert admin.execute(
        "SELECT DISTINCT status FROM garment_units WHERE tenant_id = %s AND id = ANY(%s::uuid[])",
        (TENANT_A, PIECES_A),
    ) == [("QC_PASS",)]


def test_a_final_disposition_cannot_be_overridden(admin: Database) -> None:
    with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "PASS"))

    assert "QC_DISPOSITION_TERMINAL" in admin.error(*inspect(ASSEMBLY_A, "REJECT", key="key-2"))


def test_an_assembly_still_assembling_cannot_be_inspected(admin: Database) -> None:
    assert "QC_ASSEMBLY_NOT_READY" in admin.error(*inspect(ASSEMBLY_A_ASSEMBLING, "PASS"))


def test_an_unknown_assembly_is_refused(admin: Database) -> None:
    assert "QC_ASSEMBLY_NOT_FOUND" in admin.error(*inspect(UNKNOWN_ID, "PASS"))


def test_a_repair_must_name_a_defect(admin: Database) -> None:
    with pytest.raises(psycopg2.Error) as exc:
        with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
            cur.execute(*inspect(ASSEMBLY_A, "REPAIR"))

    assert "QC_DEFECT_REQUIRED" in str(exc.value)


def test_a_pass_must_not_name_a_defect(admin: Database) -> None:
    with pytest.raises(psycopg2.Error) as exc:
        with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
            cur.execute(*inspect(ASSEMBLY_A, "PASS"))
            cur.execute(DEFECT_SQL, (TENANT_A, PIECES_A[0], "puckering", TENANT_A, ASSEMBLY_A))

    assert "QC_DEFECT_NOT_ALLOWED" in str(exc.value)


def test_a_defect_on_a_piece_of_another_assembly_is_refused(admin: Database) -> None:
    with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "REPAIR"))
        cur.execute(DEFECT_SQL, (TENANT_A, PIECES_A[0], "puckering", TENANT_A, ASSEMBLY_A))

    message = admin.error(DEFECT_SQL, (TENANT_A, PIECE_B, "puckering", TENANT_A, ASSEMBLY_A))

    assert "QC_DEFECT_FOREIGN_COMPONENT" in message


def test_a_defect_cannot_reference_another_tenants_inspection(admin: Database) -> None:
    with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "REPAIR"))
        cur.execute(DEFECT_SQL, (TENANT_A, PIECES_A[0], "puckering", TENANT_A, ASSEMBLY_A))

    message = admin.error(DEFECT_SQL, (TENANT_B, PIECE_B, "puckering", TENANT_A, ASSEMBLY_A))

    assert "QC_INSPECTION_NOT_FOUND" in message


def test_a_component_allocation_cannot_cross_tenants(admin: Database) -> None:
    message = admin.error(
        """
        INSERT INTO assembly_components (tenant_id, assembly_id, garment_unit_id, component_code)
        VALUES (%s, %s, %s, 'SLEEVE')
        """,
        (TENANT_B, ASSEMBLY_B, PIECES_A[0]),
    )

    assert "fk_assembly_components_unit" in message or "violates foreign key" in message


def test_a_piece_belongs_to_exactly_one_assembly(admin: Database) -> None:
    message = admin.error(
        """
        INSERT INTO assembly_components (tenant_id, assembly_id, garment_unit_id, component_code)
        VALUES (%s, %s, %s, 'SLEEVE')
        """,
        (TENANT_A, ASSEMBLY_A_ASSEMBLING, PIECES_A[0]),
    )

    assert "uq_assembly_components_unit" in message or "duplicate key" in message


def test_the_rework_inspection_takes_the_next_sequence(admin: Database) -> None:
    with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "REPAIR", key="repair-1"))
        cur.execute(DEFECT_SQL, (TENANT_A, PIECES_A[2], "puckering", TENANT_A, ASSEMBLY_A))

    with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "PASS", key="pass-1"))
        _, sequence_no = cur.fetchone()

    assert sequence_no == 2
    assert admin.execute(
        "SELECT sequence_no, disposition FROM qc_inspections WHERE tenant_id = %s ORDER BY 1",
        (TENANT_A,),
    ) == [(1, "REPAIR"), (2, "PASS")]
    assert admin.execute(
        "SELECT status FROM garment_assemblies WHERE tenant_id = %s AND id = %s",
        (TENANT_A, ASSEMBLY_A),
    ) == [("QC_PASS",)]


def test_the_inspection_log_is_append_only(admin: Database) -> None:
    with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "PASS"))

    assert "QC_INSPECTION_IMMUTABLE" in admin.error(
        "UPDATE qc_inspections SET disposition = 'REJECT' WHERE tenant_id = %s", (TENANT_A,)
    )
    assert "QC_INSPECTION_IMMUTABLE" in admin.error(
        "DELETE FROM qc_inspections WHERE tenant_id = %s", (TENANT_A,)
    )


def test_the_runtime_role_cannot_rewrite_a_recorded_decision(
    admin: Database, app: Database
) -> None:
    with admin.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "PASS"))

    assert "permission denied" in app.error_for(
        TENANT_A,
        "UPDATE qc_inspections SET disposition = 'REJECT' WHERE tenant_id = %s",
        (TENANT_A,),
    )
    assert "permission denied" in app.error_for(
        TENANT_A, "DELETE FROM qc_inspections WHERE tenant_id = %s", (TENANT_A,)
    )


def test_the_runtime_role_records_an_inspection_end_to_end(admin: Database, app: Database) -> None:
    with app.transaction(TENANT_A) as conn, conn.cursor() as cur:
        cur.execute(*inspect(ASSEMBLY_A, "REPAIR", key="app-repair-1"))
        _, sequence_no = cur.fetchone()
        cur.execute(DEFECT_SQL, (TENANT_A, PIECES_A[1], "broken stitch", TENANT_A, ASSEMBLY_A))

    assert sequence_no == 1
    assert admin.execute(
        "SELECT status FROM garment_assemblies WHERE tenant_id = %s AND id = %s",
        (TENANT_A, ASSEMBLY_A),
    ) == [("REWORK",)]
    assert admin.execute(
        "SELECT DISTINCT status FROM garment_units WHERE tenant_id = %s AND id = ANY(%s::uuid[])",
        (TENANT_A, PIECES_A),
    ) == [("REWORK",)]


def test_a_tenant_without_context_sees_no_rows(app: Database) -> None:
    assert app.execute("SELECT count(*) FROM qc_inspections") == [(0,)]
    assert app.execute("SELECT count(*) FROM garment_assemblies") == [(0,)]
    assert app.execute("SELECT count(*) FROM assembly_components") == [(0,)]


def test_a_tenant_sees_only_its_own_rows(app: Database) -> None:
    assert app.query_for(TENANT_A, "SELECT id FROM garment_assemblies ORDER BY id") == [
        (ASSEMBLY_A,),
        (ASSEMBLY_A_ASSEMBLING,),
    ]
    assert app.query_for(TENANT_B, "SELECT id FROM garment_assemblies ORDER BY id") == [
        (ASSEMBLY_B,)
    ]


def test_a_tenant_cannot_write_another_tenants_row(app: Database) -> None:
    message = app.error_for(
        TENANT_A,
        """
        INSERT INTO garment_assemblies (tenant_id, order_id, serial_code, status)
        VALUES (%s, %s, 'B-SNEAK', 'MENUNGGU_QC')
        """,
        (TENANT_B, ORDER_B),
    )

    assert "row-level security" in message or "row level security" in message
