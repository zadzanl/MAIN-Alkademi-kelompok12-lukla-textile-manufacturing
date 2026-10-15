"""Restricted-role regression checks for the payroll SQL foundation.

Ceiling: this module covers the core database contracts only. It expects the
caller to migrate a disposable database and provide both explicit connection
URLs; broader RLS, lifecycle, concurrency, and application-auth checks remain
separate verification work.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import DBAPIError

DATABASE_URL = os.environ.get("DATABASE_URL")
APP_DATABASE_URL = os.environ.get("LUKLA_APP_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL or not APP_DATABASE_URL,
    reason="DATABASE_URL and LUKLA_APP_DATABASE_URL must target an explicit disposable database",
)


@pytest.fixture(scope="module")
def engines() -> Iterator[tuple[Engine, Engine]]:
    assert DATABASE_URL is not None
    assert APP_DATABASE_URL is not None
    admin_url = make_url(DATABASE_URL)
    app_url = make_url(APP_DATABASE_URL)
    if (
        not admin_url.database
        or not admin_url.database.startswith("payroll_revision_")
        or admin_url.database != app_url.database
        or admin_url.host != app_url.host
        or admin_url.port != app_url.port
    ):
        raise RuntimeError("Payroll invariants require two URLs for the same payroll_revision_* DB")
    admin = create_engine(DATABASE_URL, pool_pre_ping=True)
    app = create_engine(APP_DATABASE_URL, pool_pre_ping=True)
    try:
        yield admin, app
    finally:
        app.dispose()
        admin.dispose()


@pytest.fixture(scope="module")
def identities(engines: tuple[Engine, Engine]) -> tuple[uuid.UUID, uuid.UUID]:
    admin, _ = engines
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    with admin.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO tenants (id, tenant_code, name, kind) "
                "VALUES (:id, :code, 'Payroll Test Tenant', 'CLIENT')"
            ),
            {"id": tenant_id, "code": f"PAYROLL_{tenant_id.hex[:12]}"},
        )
        connection.execute(
            text(
                "INSERT INTO actors (id, email, display_name) "
                "VALUES (:id, :email, 'Payroll Test Actor')"
            ),
            {"id": actor_id, "email": f"payroll-{actor_id.hex}@example.test"},
        )
    return tenant_id, actor_id


def _context(connection: Connection, tenant_id: uuid.UUID, actor_id: uuid.UUID, role: str) -> None:
    connection.execute(
        text("SELECT set_request_context(:tenant_id, :actor_id, :role)"),
        {"tenant_id": tenant_id, "actor_id": actor_id, "role": role},
    )


def _rule_values(tenant_id: uuid.UUID, rule_id: uuid.UUID, name: str) -> dict[str, object]:
    return {
        "id": rule_id,
        "tenant_id": tenant_id,
        "rule_name": name,
        "effective_from": "2026-01-01",
        "parameters": '{"currency":"IDR"}',
    }


def _insert_rule(
    connection: Connection,
    values: dict[str, object],
    status: str = "PENDING",
) -> None:
    connection.execute(
        text(
            "INSERT INTO financial_rule_versions "
            "(id, tenant_id, rule_name, effective_from, parameters, status) "
            "VALUES (:id, :tenant_id, :rule_name, :effective_from, "
            "CAST(:parameters AS jsonb), :status)"
        ),
        {**values, "status": status},
    )


def _insert_period(
    connection: Connection,
    tenant_id: uuid.UUID,
    rule_id: uuid.UUID,
    *,
    start: str,
    end: str,
    timezone: str = "Asia/Jakarta",
    cutoff: str = "12:00:00",
) -> uuid.UUID:
    period_id = uuid.uuid4()
    connection.execute(
        text(
            "INSERT INTO payroll_periods "
            "(id, tenant_id, period_start, period_end, timezone, cutoff_local, rule_version) "
            "VALUES (:id, :tenant_id, :start, :end, :timezone, :cutoff, :rule_id)"
        ),
        {
            "id": period_id,
            "tenant_id": tenant_id,
            "start": start,
            "end": end,
            "timezone": timezone,
            "cutoff": cutoff,
            "rule_id": rule_id,
        },
    )
    return period_id


def _rule_status(connection: Connection, rule_id: uuid.UUID) -> dict[str, object]:
    return connection.execute(
        text("SELECT * FROM payroll_read_rows('financial_rule_versions', :rule_id)"),
        {"rule_id": rule_id},
    ).scalar_one()


def test_r1_rule_proposal_and_owner_approval(engines, identities):
    """FinancePayroll proposes PENDING; only Owner can approve with evidence."""
    _, app = engines
    tenant_id, actor_id = identities
    rule_id = uuid.uuid4()
    rule = _rule_values(tenant_id, rule_id, f"fixture-rule-{rule_id.hex}")

    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "FinancePayroll")
        _insert_rule(connection, rule)
    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "FinancePayroll")
        assert _rule_status(connection, rule_id)["status"] == "PENDING"

    with pytest.raises(DBAPIError, match="RULE_APPROVAL_FORBIDDEN") as denied:
        with app.begin() as connection:
            _context(connection, tenant_id, actor_id, "FinancePayroll")
            connection.execute(
                text(
                    "SELECT payroll_approve_rule(:rule_id, :evidence_id, "
                    ":reference, :note, :request_id)"
                ),
                {
                    "rule_id": rule_id,
                    "evidence_id": uuid.uuid4(),
                    "reference": "fixture",
                    "note": "reviewed",
                    "request_id": uuid.uuid4(),
                },
            )
    assert denied.value.orig.sqlstate == "42501"
    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "FinancePayroll")
        assert _rule_status(connection, rule_id)["status"] == "PENDING"

    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "Owner")
        connection.execute(
            text(
                "SELECT payroll_approve_rule(:rule_id, :evidence_id, "
                ":reference, :note, :request_id)"
            ),
            {
                "rule_id": rule_id,
                "evidence_id": uuid.uuid4(),
                "reference": "fixture",
                "note": "reviewed",
                "request_id": uuid.uuid4(),
            },
        )
    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "Owner")
        approved = _rule_status(connection, rule_id)
        assert approved["status"] == "APPROVED"
        assert approved["approved_by"] == str(actor_id)
        assert approved["evidence_file_id"] is not None

    for role in ("Owner", "FinancePayroll", "", "UnknownRole"):
        with pytest.raises(DBAPIError, match="RULE_APPROVAL_FORBIDDEN") as denied:
            with app.begin() as connection:
                _context(connection, tenant_id, actor_id, role)
                _insert_rule(
                    connection,
                    _rule_values(tenant_id, uuid.uuid4(), f"direct-approved-{uuid.uuid4().hex}"),
                    status="APPROVED",
                )
        assert denied.value.orig.sqlstate == "42501"

    for role in ("", "UnknownRole"):
        with pytest.raises(DBAPIError) as denied:
            with app.begin() as connection:
                _context(connection, tenant_id, actor_id, role)
                _insert_rule(
                    connection,
                    _rule_values(tenant_id, uuid.uuid4(), f"missing-role-{uuid.uuid4().hex}"),
                )
        assert denied.value.orig.sqlstate == "42501"

    with pytest.raises(DBAPIError, match="RULE_APPROVAL_FORBIDDEN") as denied:
        with app.begin() as connection:
            _context(connection, tenant_id, actor_id, "FinancePayroll")
            _insert_rule(
                connection,
                _rule_values(tenant_id, uuid.uuid4(), f"direct-rejected-{uuid.uuid4().hex}"),
                status="REJECTED",
            )
    assert denied.value.orig.sqlstate == "42501"

    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "Owner")
        _insert_rule(
            connection,
            _rule_values(tenant_id, uuid.uuid4(), f"owner-pending-{uuid.uuid4().hex}"),
        )


def test_r2_period_timezone_is_fixed(engines, identities):
    """Only Asia/Jakarta is accepted by the database period contract."""
    _, app = engines
    tenant_id, actor_id = identities
    rule_id = uuid.uuid4()
    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "FinancePayroll")
        _insert_rule(connection, _rule_values(tenant_id, rule_id, f"timezone-{rule_id.hex}"))
    for index, timezone in enumerate(("UTC", "", "Asia/Bangkok")):
        with pytest.raises(DBAPIError, match="payroll_periods_timezone") as denied:
            with app.begin() as connection:
                _context(connection, tenant_id, actor_id, "FinancePayroll")
                _insert_period(
                    connection,
                    tenant_id,
                    rule_id,
                    start=f"2026-{index + 1:02d}-01",
                    end=f"2026-{index + 1:02d}-08",
                    timezone=timezone,
                )
        assert denied.value.orig.sqlstate == "23514"

    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "FinancePayroll")
        _insert_period(connection, tenant_id, rule_id, start="2026-04-01", end="2026-04-08")


def test_r3_period_cutoff_is_whole_minute_and_below_24_hours(engines, identities):
    """Fractional seconds and 24:00 are rejected; valid minute values remain valid."""
    _, app = engines
    tenant_id, actor_id = identities
    rule_id = uuid.uuid4()
    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "FinancePayroll")
        _insert_rule(connection, _rule_values(tenant_id, rule_id, f"cutoff-{rule_id.hex}"))
    invalid_cutoffs = ("12:00:01", "12:00:00.000001", "24:00:00")
    for index, cutoff in enumerate(invalid_cutoffs):
        with pytest.raises(DBAPIError, match="payroll_periods_cutoff_local") as denied:
            with app.begin() as connection:
                _context(connection, tenant_id, actor_id, "FinancePayroll")
                _insert_period(
                    connection,
                    tenant_id,
                    rule_id,
                    start=f"2026-{index + 5:02d}-01",
                    end=f"2026-{index + 5:02d}-08",
                    cutoff=cutoff,
                )
        assert denied.value.orig.sqlstate == "23514"

    for index, cutoff in enumerate(("00:00:00", "12:00:00", "23:59:00")):
        with app.begin() as connection:
            _context(connection, tenant_id, actor_id, "FinancePayroll")
            _insert_period(
                connection,
                tenant_id,
                rule_id,
                start=f"2026-{index + 8:02d}-01",
                end=f"2026-{index + 8:02d}-08",
                cutoff=cutoff,
            )


def test_restricted_reader_requires_context_and_cannot_cross_tenants(engines, identities):
    _, app = engines
    tenant_id, actor_id = identities
    rule_id = uuid.uuid4()
    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "FinancePayroll")
        _insert_rule(connection, _rule_values(tenant_id, rule_id, f"isolation-{rule_id.hex}"))

    with pytest.raises(DBAPIError) as missing:
        with app.begin() as connection:
            _rule_status(connection, rule_id)
    assert missing.value.orig.sqlstate in ("42501", "22023")

    second_tenant = uuid.uuid4()
    admin, _ = engines
    with admin.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO tenants (id, tenant_code, name, kind) "
                "VALUES (:id, :code, 'Other Tenant', 'CLIENT')"
            ),
            {"id": second_tenant, "code": f"PAYROLL_{second_tenant.hex[:12]}"},
        )
    with app.begin() as connection:
        _context(connection, second_tenant, actor_id, "FinancePayroll")
        assert (
            connection.execute(
                text("SELECT payroll_read_rows('financial_rule_versions', :rule_id)"),
                {"rule_id": rule_id},
            )
            .scalars()
            .all()
            == []
        )


def test_pending_rule_blocks_calculation_without_monetary_rows(engines, identities):
    _, app = engines
    tenant_id, actor_id = identities
    rule_id = uuid.uuid4()
    with app.begin() as connection:
        _context(connection, tenant_id, actor_id, "FinancePayroll")
        _insert_rule(connection, _rule_values(tenant_id, rule_id, f"pending-{rule_id.hex}"))
        period_id = _insert_period(
            connection, tenant_id, rule_id, start="2026-02-01", end="2026-02-08"
        )

    with pytest.raises(DBAPIError, match="FINANCIAL_RULE_PENDING") as blocked:
        with app.begin() as connection:
            _context(connection, tenant_id, actor_id, "FinancePayroll")
            connection.execute(
                text("SELECT calculate_weekly_payroll(:period_id, :rule_id)"),
                {"period_id": period_id, "rule_id": rule_id},
            )
    assert blocked.value.orig.sqlstate == "23514"

    admin, _ = engines
    with admin.begin() as connection:
        for table in (
            "wage_credits",
            "payroll_runs",
            "payroll_items",
            "payroll_payments",
        ):
            # Names are a closed literal list, never caller input.
            assert (
                connection.execute(
                    text(f"SELECT count(*) FROM {table} WHERE tenant_id = :tenant_id"),
                    {"tenant_id": tenant_id},
                ).scalar_one()
                == 0
            )
