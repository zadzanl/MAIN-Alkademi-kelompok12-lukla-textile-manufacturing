import uuid
import pytest
import jwt
import concurrent.futures
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.auth import create_access_token
from backend.app.models.identities import Tenant, Actor
from backend.app.models.idempotency import IdempotencyRecord
from backend.app.models.ledger import LedgerAccount, LedgerTransaction, LedgerEntry
from backend.app.models.audit import AuditEvent
from backend.app.schemas.ledger import LedgerRequest, LedgerEntry as LedgerEntrySchema, ReversalRequest

# Database Engines
admin_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
app_engine = create_engine(settings.LUKLA_APP_DATABASE_URL, pool_pre_ping=True)

AdminSession = sessionmaker(bind=admin_engine, autocommit=False, autoflush=False)
AppSession = sessionmaker(bind=app_engine, autocommit=False, autoflush=False)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure schema and base tables exist."""
    with admin_engine.connect() as conn:
        conn.execute(text("SELECT 1;"))
        conn.commit()

@pytest.fixture
def db_admin():
    """Superuser session for test fixture setup."""
    session = AdminSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def db_app():
    """Unprivileged runtime lukla_app session."""
    session = AppSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def client():
    """TestClient wired to unprivileged application role lukla_app."""
    def override_get_db():
        session = AppSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def tenant_fixture(db_admin):
    """Seed test tenants, actors, and operational accounts."""
    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    # Create tenants
    tenant_a = Tenant(
        id=tenant_a_id,
        tenant_code=f"TENANT_A_{uuid.uuid4().hex[:6]}",
        name="Tenant A Fabrics",
        kind="CLIENT",
        active=True
    )
    tenant_b = Tenant(
        id=tenant_b_id,
        tenant_code=f"TENANT_B_{uuid.uuid4().hex[:6]}",
        name="Tenant B Garments",
        kind="CLIENT",
        active=True
    )
    actor = Actor(
        id=actor_id,
        email=f"finance_{uuid.uuid4().hex[:6]}@lukla.io",
        display_name="Lukla Finance Lead",
        active=True
    )
    db_admin.add_all([tenant_a, tenant_b, actor])
    db_admin.commit()

    # Seed canonical operational accounts for Tenant A and Tenant B
    db_admin.execute(text("SELECT seed_operational_accounts(:tenant_id, 'IDR')"), {"tenant_id": str(tenant_a_id)})
    db_admin.execute(text("SELECT seed_operational_accounts(:tenant_id, 'IDR')"), {"tenant_id": str(tenant_b_id)})
    db_admin.commit()

    # Create tokens for various roles
    owner_token_a = create_access_token({
        "sub": str(actor_id),
        "roles": ["Owner"],
        "tenant_id": str(tenant_a_id)
    })
    finance_token_a = create_access_token({
        "sub": str(actor_id),
        "roles": ["FinancePayroll"],
        "tenant_id": str(tenant_a_id)
    })
    tailor_token_a = create_access_token({
        "sub": str(actor_id),
        "roles": ["Tailor"],
        "tenant_id": str(tenant_a_id)
    })
    finance_token_b = create_access_token({
        "sub": str(actor_id),
        "roles": ["FinancePayroll"],
        "tenant_id": str(tenant_b_id)
    })

    return {
        "tenant_a_id": tenant_a_id,
        "tenant_b_id": tenant_b_id,
        "actor_id": actor_id,
        "owner_token_a": owner_token_a,
        "finance_token_a": finance_token_a,
        "tailor_token_a": tailor_token_a,
        "finance_token_b": finance_token_b,
    }


# ==============================================================================
# 1. Mathematical Balance & Database Invariants
# ==============================================================================

def test_unbalanced_transaction_api_rollback(client, tenant_fixture, db_admin):
    """Unbalanced transaction fails validation and rolls back completely."""
    payload = {
        "transactionType": "FABRIC_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 1000000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 999000}
        ]
    }
    key = f"idemp-unbalanced-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )

    assert resp.status_code == 400
    assert resp.headers.get("content-type") == "application/problem+json"
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "unbalanced" in body["detail"].lower()

    # Confirm nothing was written to ledger_transactions
    count = db_admin.execute(
        select(LedgerTransaction).filter_by(tenant_id=tenant_fixture["tenant_a_id"])
    ).scalars().all()
    assert len(count) == 0


def test_direct_sql_deferred_balance_and_empty_header_trigger(tenant_fixture):
    """Deferred constraint trigger rejects empty headers and unbalanced commits in SQL."""
    tenant_id = tenant_fixture["tenant_a_id"]

    # 1. Empty transaction header without lines must fail at commit
    with pytest.raises(Exception) as exc_empty:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)}
            )
            empty_tx_id = uuid.uuid4()
            conn.execute(
                text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'TEST_EMPTY')"),
                {"id": str(empty_tx_id), "t_id": str(tenant_id)}
            )
            tx.commit()

    assert "EMPTY_OR_ONE_SIDED_TRANSACTION" in str(exc_empty.value)

    # 2. Unbalanced lines must fail at commit
    with pytest.raises(Exception) as exc_unbalanced:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant_id)}
            )
            tx_id = uuid.uuid4()
            conn.execute(
                text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'TEST_UNBALANCED')"),
                {"id": str(tx_id), "t_id": str(tenant_id)}
            )
            # Find accounts
            accts = conn.execute(
                text("SELECT id, code FROM ledger_accounts WHERE tenant_id = :t_id"),
                {"t_id": str(tenant_id)}
            ).fetchall()
            acct_map = {row[1]: row[0] for row in accts}

            # Insert Debit 1000, Credit 999
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', 1000, 'IDR')"),
                {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct_map["CUSTODIAL_MATERIAL"])}
            )
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'CREDIT', 999, 'IDR')"),
                {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct_map["CUSTODIAL_OBLIGATION"])}
            )
            tx.commit()

    assert "TRANSACTION_UNBALANCED" in str(exc_unbalanced.value)


def test_entry_check_constraints(tenant_fixture):
    """Negative amount or invalid direction fail table check constraints."""
    tenant_id = tenant_fixture["tenant_a_id"]

    with pytest.raises(Exception) as exc_amount:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
            tx_id = uuid.uuid4()
            conn.execute(
                text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'TEST_CHK')"),
                {"id": str(tx_id), "t_id": str(tenant_id)}
            )
            acct = conn.execute(text("SELECT id FROM ledger_accounts WHERE tenant_id = :t_id LIMIT 1"), {"t_id": str(tenant_id)}).scalar_one()
            # Non-positive amount
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', 0, 'IDR')"),
                {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct)}
            )
            tx.commit()

    assert "amount_minor" in str(exc_amount.value) or "chk_entry_amount_positive" in str(exc_amount.value)


def test_strict_immutability(client, tenant_fixture):
    """Direct SQL UPDATE or DELETE on ledger tables raises LEDGER_IMMUTABLE."""
    tenant_id = tenant_fixture["tenant_a_id"]

    # Post a valid transaction first via API
    payload = {
        "transactionType": "CUSTODIAL_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 500000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 500000}
        ]
    }
    key = f"idemp-immut-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp.status_code == 201
    posted_id = resp.json()["id"]

    # Attempt direct SQL UPDATE as lukla_app
    with pytest.raises(Exception) as exc_update:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
            conn.execute(
                text("UPDATE ledger_transactions SET transaction_type = 'HACKED' WHERE id = :id"),
                {"id": str(posted_id)}
            )
            tx.commit()

    assert "LEDGER_IMMUTABLE" in str(exc_update.value) or "permission denied" in str(exc_update.value)

    # Attempt direct SQL DELETE as lukla_app
    with pytest.raises(Exception) as exc_delete:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
            conn.execute(
                text("DELETE FROM ledger_entries WHERE transaction_id = :id"),
                {"id": str(posted_id)}
            )
            tx.commit()

    assert "LEDGER_IMMUTABLE" in str(exc_delete.value) or "permission denied" in str(exc_delete.value)


def test_late_line_insertion_block(client, tenant_fixture):
    """Appending lines to a previously committed transaction fails created_xid check."""
    tenant_id = tenant_fixture["tenant_a_id"]

    # Post a valid transaction
    payload = {
        "transactionType": "CUSTODIAL_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 200000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 200000}
        ]
    }
    key = f"idemp-lateline-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp.status_code == 201
    posted_id = resp.json()["id"]

    # Attempt late-line insert in a new transaction
    with pytest.raises(Exception) as exc_late:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
            acct = conn.execute(text("SELECT id FROM ledger_accounts WHERE tenant_id = :t_id LIMIT 1"), {"t_id": str(tenant_id)}).scalar_one()
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', 100, 'IDR')"),
                {"t_id": str(tenant_id), "tx_id": str(posted_id), "acct": str(acct)}
            )
            tx.commit()

    assert "LATE_LINE_INSERTION_BLOCKED" in str(exc_late.value)


def test_composite_foreign_key_cross_tenant_isolation(tenant_fixture, db_admin):
    """Composite FK prevents referencing Tenant B account from Tenant A transaction."""
    tenant_a = tenant_fixture["tenant_a_id"]
    tenant_b = tenant_fixture["tenant_b_id"]

    # Query Tenant B account via db_admin (bypasses RLS to obtain valid Tenant B account ID)
    acct_b = db_admin.execute(
        text("SELECT id FROM ledger_accounts WHERE tenant_id = :t_b LIMIT 1"),
        {"t_b": str(tenant_b)}
    ).scalar_one()

    with pytest.raises(Exception) as exc_fk:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_a)})

            # Create transaction in Tenant A
            tx_id = uuid.uuid4()
            conn.execute(
                text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'CROSS_TENANT')"),
                {"id": str(tx_id), "t_id": str(tenant_a)}
            )

            # Attempt to insert Tenant A entry pointing to Tenant B account
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_a, :tx_id, :acct_b, 'DEBIT', 100, 'IDR')"),
                {"t_a": str(tenant_a), "tx_id": str(tx_id), "acct_b": str(acct_b)}
            )
            tx.commit()

    assert "fk_ledger_entries_account" in str(exc_fk.value)


# ==============================================================================
# 2. Account Code Validation (Negative Controls)
# ==============================================================================

def test_unknown_account_code_rejected(client, tenant_fixture):
    """Unknown accountCode returns 400 VALIDATION_ERROR and rolls back."""
    payload = {
        "transactionType": "CUSTODIAL_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "NON_EXISTENT_CODE", "direction": "DEBIT", "amountMinor": 100000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 100000}
        ]
    }
    key = f"idemp-unk-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp.status_code == 400
    assert resp.headers.get("content-type") == "application/problem+json"
    data = resp.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert "Unknown accountCode" in data["detail"]


def test_inactive_account_rejected(client, tenant_fixture, db_admin):
    """Inactive account (active = false) returns 400 VALIDATION_ERROR."""
    tenant_id = tenant_fixture["tenant_a_id"]
    # Deactivate RAW_MATERIAL_ASSET
    db_admin.execute(
        text("UPDATE ledger_accounts SET active = false WHERE tenant_id = :t_id AND code = 'RAW_MATERIAL_ASSET'"),
        {"t_id": str(tenant_id)}
    )
    db_admin.commit()

    payload = {
        "transactionType": "PURCHASE",
        "currency": "IDR",
        "entries": [
            {"accountCode": "RAW_MATERIAL_ASSET", "direction": "DEBIT", "amountMinor": 100000},
            {"accountCode": "ACCOUNTS_PAYABLE", "direction": "CREDIT", "amountMinor": 100000}
        ]
    }
    key = f"idemp-inact-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"
    assert "inactive" in resp.json()["detail"].lower()


def test_currency_mismatch_rejected(client, tenant_fixture, db_admin):
    """Currency mismatch between entry and account returns 400 VALIDATION_ERROR."""
    tenant_id = tenant_fixture["tenant_a_id"]
    # Create USD account
    db_admin.execute(
        text("INSERT INTO ledger_accounts (tenant_id, code, name, account_class, currency, active) VALUES (:t_id, 'USD_BANK', 'USD Bank', 'ASSET', 'USD', true)"),
        {"t_id": str(tenant_id)}
    )
    db_admin.commit()

    payload = {
        "transactionType": "TRANSFER",
        "currency": "IDR",
        "entries": [
            {"accountCode": "USD_BANK", "direction": "DEBIT", "amountMinor": 100000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 100000}
        ]
    }
    key = f"idemp-curr-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "VALIDATION_ERROR"
    assert "currency" in resp.json()["detail"].lower()


# ==============================================================================
# 3. Multi-Tenant Boundary & Connection Pool Safety
# ==============================================================================

def test_row_level_security_tenant_isolation(client, tenant_fixture):
    """RLS ensures queries for Tenant B return 0 rows belonging to Tenant A."""
    # Tenant A posts a transaction
    payload = {
        "transactionType": "CUSTODIAL_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 750000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 750000}
        ]
    }
    key = f"idemp-rls-{uuid.uuid4().hex}"
    resp_a = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp_a.status_code == 201

    # Tenant B queries ledger entries
    resp_b = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_b']}"}
    )
    assert resp_b.status_code == 200
    items_b = resp_b.json()["items"]
    # Ensure none of Tenant A's items are visible
    for item in items_b:
        assert item["tenantId"] != str(tenant_fixture["tenant_a_id"])


def test_connection_pool_guc_reset_leakage_protection(tenant_fixture):
    """Reusing pooled connections confirms app.tenant_id resets and does not leak."""
    tenant_a = tenant_fixture["tenant_a_id"]

    # Checkout connection 1 and set tenant_a session-level GUC
    conn1 = app_engine.connect()
    conn1.execute(text("SELECT set_config('app.tenant_id', :t_id, false)"), {"t_id": str(tenant_a)})
    guc1 = conn1.execute(text("SELECT current_setting('app.tenant_id', true)")).scalar()
    assert guc1 == str(tenant_a)

    # Checkin connection 1 (our hook runs RESET ALL)
    conn1.close()

    # Re-checkout connection from the pool
    conn2 = app_engine.connect()
    guc2 = conn2.execute(text("SELECT current_setting('app.tenant_id', true)")).scalar()
    # GUC must be reset to empty / None
    assert guc2 is None or guc2 == ""

    # Unauthenticated / un-scoped query returns 0 rows
    rows = conn2.execute(text("SELECT count(*) FROM ledger_accounts")).scalar()
    assert rows == 0
    conn2.close()


# ==============================================================================
# 4. Authentication & RBAC
# ==============================================================================

def test_unauthenticated_request_rejected(client):
    """Requests lacking Bearer auth return 401 AUTH_REQUIRED."""
    resp = client.get("/api/v1/ledger/entries")
    assert resp.status_code == 401
    assert resp.headers.get("content-type") == "application/problem+json"
    assert resp.json()["code"] == "AUTH_REQUIRED"


def test_unauthorized_role_rejected(client, tenant_fixture):
    """Non-owner / non-finance roles return 403 FORBIDDEN."""
    resp = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": f"Bearer {tenant_fixture['tailor_token_a']}"}
    )
    assert resp.status_code == 403
    assert resp.headers.get("content-type") == "application/problem+json"
    assert resp.json()["code"] == "FORBIDDEN"


def test_authorized_owner_and_finance_accepted(client, tenant_fixture):
    """Both Owner and FinancePayroll roles are authorized."""
    resp_owner = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": f"Bearer {tenant_fixture['owner_token_a']}"}
    )
    assert resp_owner.status_code == 200

    resp_finance = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}
    )
    assert resp_finance.status_code == 200


# ==============================================================================
# 5. Core Posting & Audit Persistence
# ==============================================================================

def test_append_ledger_transaction_happy_path(client, tenant_fixture, db_admin):
    """Posting creates transaction, entries, and audit record within single ACID tx."""
    payload = {
        "transactionType": "CUSTODIAL_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 1250000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 1250000}
        ]
    }
    key = f"idemp-post-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["tenantId"] == str(tenant_fixture["tenant_a_id"])
    assert len(data["entries"]) == 2
    tx_id = data["id"]

    # Verify audit_events row persisted
    audit = db_admin.execute(
        select(AuditEvent).filter_by(
            tenant_id=tenant_fixture["tenant_a_id"],
            entity_type="ledger_transactions",
            entity_id=uuid.UUID(tx_id)
        )
    ).scalar_one_or_none()
    assert audit is not None
    assert audit.action == "LEDGER_TRANSACTION_APPENDED"


# ==============================================================================
# 6. Idempotency Replay & Conflict
# ==============================================================================

def test_posting_idempotency_replay_and_conflict(client, tenant_fixture, db_admin):
    """Identical replay returns cached response; payload modification returns 409 Conflict."""
    payload1 = {
        "transactionType": "WIP_ACCRUAL",
        "currency": "IDR",
        "entries": [
            {"accountCode": "WIP_DIRECT_LABOR", "direction": "DEBIT", "amountMinor": 300000},
            {"accountCode": "WAGES_PAYABLE", "direction": "CREDIT", "amountMinor": 300000}
        ]
    }
    key = f"idemp-key-{uuid.uuid4().hex}"

    # First request
    resp1 = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload1
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    # Replay with identical payload
    resp2 = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload1
    )
    assert resp2.status_code == 201
    assert resp2.json()["id"] == id1

    # Replay with mismatched payload
    payload_altered = dict(payload1)
    payload_altered["entries"] = [
        {"accountCode": "WIP_DIRECT_LABOR", "direction": "DEBIT", "amountMinor": 350000},
        {"accountCode": "WAGES_PAYABLE", "direction": "CREDIT", "amountMinor": 350000}
    ]
    resp3 = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload_altered
    )
    assert resp3.status_code == 409
    assert resp3.headers.get("content-type") == "application/problem+json"
    assert resp3.json()["code"] == "IDEMPOTENCY_CONFLICT"


def test_reversal_idempotency_replay_and_conflict(client, tenant_fixture):
    """Reversal replay returns cached 201; altered reason returns 409 Conflict."""
    # Post initial transaction
    post_payload = {
        "transactionType": "CUSTODIAL_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 400000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 400000}
        ]
    }
    p_key = f"idemp-rev-src-{uuid.uuid4().hex}"
    p_resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": p_key},
        json=post_payload
    )
    tx_id = p_resp.json()["id"]

    # First reversal
    rev_key = f"idemp-rev-{uuid.uuid4().hex}"
    rev_payload = {"reason": "Defective batch received"}
    rev_resp1 = client.post(
        f"/api/v1/ledger/transactions/{tx_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": rev_key},
        json=rev_payload
    )
    assert rev_resp1.status_code == 201
    rev_id1 = rev_resp1.json()["id"]

    # Replay identical reversal
    rev_resp2 = client.post(
        f"/api/v1/ledger/transactions/{tx_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": rev_key},
        json=rev_payload
    )
    assert rev_resp2.status_code == 201
    assert rev_resp2.json()["id"] == rev_id1

    # Replay with altered payload
    rev_resp3 = client.post(
        f"/api/v1/ledger/transactions/{tx_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": rev_key},
        json={"reason": "Different reason entirely"}
    )
    assert rev_resp3.status_code == 409
    assert rev_resp3.json()["code"] == "IDEMPOTENCY_CONFLICT"


# ==============================================================================
# 7. Compensating Reversals Invariant
# ==============================================================================

def test_compensating_reversal_inversion_and_invariants(client, tenant_fixture, db_admin):
    """Reversal mirrors entries with inverted directions; duplicate and reverse-of-reversal fail."""
    # Post initial transaction
    post_payload = {
        "transactionType": "WIP_ACCRUAL",
        "currency": "IDR",
        "entries": [
            {"accountCode": "WIP_DIRECT_LABOR", "direction": "DEBIT", "amountMinor": 600000},
            {"accountCode": "WAGES_PAYABLE", "direction": "CREDIT", "amountMinor": 600000}
        ]
    }
    p_key = f"idemp-rev-inv-{uuid.uuid4().hex}"
    p_resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": p_key},
        json=post_payload
    )
    orig_tx_id = p_resp.json()["id"]

    # 1. Reverse transaction
    rev_key = f"idemp-rev-exec-{uuid.uuid4().hex}"
    rev_resp = client.post(
        f"/api/v1/ledger/transactions/{orig_tx_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": rev_key},
        json={"reason": "Incorrect operator tally"}
    )
    assert rev_resp.status_code == 201
    rev_data = rev_resp.json()
    assert rev_data["reversalOf"] == orig_tx_id
    reversal_tx_id = rev_data["id"]

    # Verify entry inversion
    entries = rev_data["entries"]
    assert len(entries) == 2
    for e in entries:
        if e["accountCode"] == "WIP_DIRECT_LABOR":
            assert e["direction"] == "CREDIT"
            assert e["amountMinor"] == 600000
        elif e["accountCode"] == "WAGES_PAYABLE":
            assert e["direction"] == "DEBIT"
            assert e["amountMinor"] == 600000

    # 2. Duplicate reversal with a NEW idempotency key fails with 409 Conflict
    new_key = f"idemp-rev-dup-{uuid.uuid4().hex}"
    dup_resp = client.post(
        f"/api/v1/ledger/transactions/{orig_tx_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": new_key},
        json={"reason": "Trying to reverse again"}
    )
    assert dup_resp.status_code == 409
    assert dup_resp.json()["code"] == "INVALID_STATE"

    # 3. Reversing a reversal transaction is rejected with 409 Conflict
    rev_of_rev_key = f"idemp-rev-rev-{uuid.uuid4().hex}"
    rev_of_rev_resp = client.post(
        f"/api/v1/ledger/transactions/{reversal_tx_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": rev_of_rev_key},
        json={"reason": "Trying to reverse the reversal"}
    )
    assert rev_of_rev_resp.status_code == 409
    assert rev_of_rev_resp.json()["code"] == "INVALID_STATE"


# ==============================================================================
# 8. Pagination & Contract Conformity
# ==============================================================================

def test_ledger_entries_cursor_pagination(client, tenant_fixture):
    """GET /api/v1/ledger/entries adheres to LedgerPage cursor pagination."""
    # Post 5 transactions
    for i in range(5):
        payload = {
            "transactionType": "BATCH_RUN",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 10000 * (i + 1)},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 10000 * (i + 1)}
            ]
        }
        client.post(
            "/api/v1/ledger/transactions",
            headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": f"idemp-page-{i}-{uuid.uuid4().hex}"},
            json=payload
        )

    # Page 1 (pageSize = 2)
    p1 = client.get(
        "/api/v1/ledger/entries?pageSize=2",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}
    )
    assert p1.status_code == 200
    p1_data = p1.json()
    assert len(p1_data["items"]) == 2
    assert p1_data["nextCursor"] is not None

    # Page 2 using cursor
    cursor1 = p1_data["nextCursor"]
    p2 = client.get(
        f"/api/v1/ledger/entries?pageSize=2&cursor={cursor1}",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}
    )
    assert p2.status_code == 200
    p2_data = p2.json()
    assert len(p2_data["items"]) == 2
    assert p2_data["nextCursor"] is not None
    # Ensure items are distinct
    p1_ids = {item["id"] for item in p1_data["items"]}
    for item in p2_data["items"]:
        assert item["id"] not in p1_ids


def test_cursor_pagination_end_of_results_and_invalid_cursor(client, tenant_fixture):
    """Test that final page returns nextCursor=None and invalid cursor returns 400 VALIDATION_ERROR."""
    # 1. Invalid cursor string returns 400 VALIDATION_ERROR
    bad_resp = client.get(
        "/api/v1/ledger/entries?cursor=NOT_VALID_BASE64!@#$",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}
    )
    assert bad_resp.status_code == 400
    assert bad_resp.headers.get("content-type") == "application/problem+json"
    assert bad_resp.json()["code"] == "VALIDATION_ERROR"

    # 2. Query with high page size to reach the end of results
    last_page = client.get(
        "/api/v1/ledger/entries?pageSize=100",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}
    )
    assert last_page.status_code == 200
    assert last_page.json()["nextCursor"] is None


def test_reversal_target_not_found_and_cross_tenant_rejected(client, tenant_fixture):
    """Reversing non-existent transaction or transaction from another tenant returns 404 Problem."""
    fake_tx_id = uuid.uuid4()
    resp_missing = client.post(
        f"/api/v1/ledger/transactions/{fake_tx_id}/reversals",
        headers={
            "Authorization": f"Bearer {tenant_fixture['finance_token_a']}",
            "Idempotency-Key": f"idemp-notfound-{uuid.uuid4().hex}"
        },
        json={"reason": "Should fail because target does not exist"}
    )
    assert resp_missing.status_code == 404
    assert resp_missing.headers.get("content-type") == "application/problem+json"
    assert resp_missing.json()["code"] == "VALIDATION_ERROR"
    assert "not found" in resp_missing.json()["detail"].lower()

    # Tenant B posts a transaction
    post_payload = {
        "transactionType": "CUSTODIAL_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 350000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 350000}
        ]
    }
    resp_b = client.post(
        "/api/v1/ledger/transactions",
        headers={
            "Authorization": f"Bearer {tenant_fixture['finance_token_b']}",
            "Idempotency-Key": f"idemp-post-b-{uuid.uuid4().hex}"
        },
        json=post_payload
    )
    assert resp_b.status_code == 201
    tx_b_id = resp_b.json()["id"]

    # Tenant A attempts to reverse Tenant B's transaction -> returns 404 without data leak
    resp_cross = client.post(
        f"/api/v1/ledger/transactions/{tx_b_id}/reversals",
        headers={
            "Authorization": f"Bearer {tenant_fixture['finance_token_a']}",
            "Idempotency-Key": f"idemp-rev-cross-{uuid.uuid4().hex}"
        },
        json={"reason": "Attacking cross-tenant reversal"}
    )
    assert resp_cross.status_code == 404
    assert resp_cross.json()["code"] == "VALIDATION_ERROR"
    assert "not found" in resp_cross.json()["detail"].lower()


def test_concurrent_posting_idempotency_race(client, tenant_fixture, db_admin):
    """
    Multiple concurrent worker threads contending for the same Idempotency-Key
    under sub-millisecond arrival windows.
    Verifies that exactly ONE transaction is committed, all callers receive 201 Created
    with the exact same transaction ID, and no duplicate entries are created.
    """
    shared_key = f"idemp-race-post-{uuid.uuid4().hex}"
    payload = {
        "transactionType": "PAYROLL_RUN",
        "currency": "IDR",
        "entries": [
            {"accountCode": "WIP_DIRECT_LABOR", "direction": "DEBIT", "amountMinor": 888000},
            {"accountCode": "WAGES_PAYABLE", "direction": "CREDIT", "amountMinor": 888000}
        ]
    }

    def worker_post():
        return client.post(
            "/api/v1/ledger/transactions",
            headers={
                "Authorization": f"Bearer {tenant_fixture['finance_token_a']}",
                "Idempotency-Key": shared_key
            },
            json=payload
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker_post) for _ in range(5)]
        responses = [f.result() for f in futures]

    # Every concurrent request must receive 201 Created
    for resp in responses:
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

    # All responses must return the identical transaction ID
    tx_ids = [resp.json()["id"] for resp in responses]
    assert len(set(tx_ids)) == 1, f"Expected exactly one transaction ID, got: {set(tx_ids)}"
    canonical_tx_id = tx_ids[0]

    # In database, exactly ONE transaction row exists with this ID
    tx_rows = db_admin.execute(
        select(LedgerTransaction).filter_by(
            id=uuid.UUID(canonical_tx_id),
            tenant_id=tenant_fixture["tenant_a_id"]
        )
    ).scalars().all()
    assert len(tx_rows) == 1

    # Exactly 2 entry rows exist for this transaction
    entry_rows = db_admin.execute(
        select(LedgerEntry).filter_by(
            transaction_id=uuid.UUID(canonical_tx_id),
            tenant_id=tenant_fixture["tenant_a_id"]
        )
    ).scalars().all()
    assert len(entry_rows) == 2


def test_concurrent_reversal_idempotency_race(client, tenant_fixture, db_admin):
    """
    Multiple concurrent worker threads contending to reverse the same transaction
    using the same Idempotency-Key.
    Verifies that all threads receive 201 Created with the identical reversal ID,
    and only one reversal transaction exists.
    """
    # 1. Post original transaction
    post_resp = client.post(
        "/api/v1/ledger/transactions",
        headers={
            "Authorization": f"Bearer {tenant_fixture['finance_token_a']}",
            "Idempotency-Key": f"idemp-orig-rev-{uuid.uuid4().hex}"
        },
        json={
            "transactionType": "MATERIAL_ADJUSTMENT",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 250000},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 250000}
            ]
        }
    )
    assert post_resp.status_code == 201
    orig_tx_id = post_resp.json()["id"]

    # 2. Race reversals
    shared_rev_key = f"idemp-race-rev-{uuid.uuid4().hex}"
    rev_payload = {"reason": "Concurrent reversal test"}

    def worker_reverse():
        return client.post(
            f"/api/v1/ledger/transactions/{orig_tx_id}/reversals",
            headers={
                "Authorization": f"Bearer {tenant_fixture['finance_token_a']}",
                "Idempotency-Key": shared_rev_key
            },
            json=rev_payload
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker_reverse) for _ in range(5)]
        responses = [f.result() for f in futures]

    for resp in responses:
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"

    rev_ids = [resp.json()["id"] for resp in responses]
    assert len(set(rev_ids)) == 1
    canonical_rev_id = rev_ids[0]

    # In database, exactly ONE reversal row exists
    rev_rows = db_admin.execute(
        select(LedgerTransaction).filter_by(
            tenant_id=tenant_fixture["tenant_a_id"],
            reversal_of=uuid.UUID(orig_tx_id)
        )
    ).scalars().all()
    assert len(rev_rows) == 1
    assert str(rev_rows[0].id) == canonical_rev_id


def test_large_batch_100_plus_entries_posting_and_reversal(client, tenant_fixture, db_admin):
    """
    Stress test: Posting and reversing a transaction containing 100+ lines (50 debits + 50 credits)
    within a single transaction header. Verifies balancing, trigger throughput, and reversal mirroring.
    """
    entries = []
    line_count = 100
    # 50 debits of 1,000 and 50 credits of 1,000 -> Total Debit = 50,000, Total Credit = 50,000
    for i in range(line_count // 2):
        entries.append({
            "accountCode": "CUSTODIAL_MATERIAL",
            "direction": "DEBIT",
            "amountMinor": 1000
        })
    for i in range(line_count // 2):
        entries.append({
            "accountCode": "CUSTODIAL_OBLIGATION",
            "direction": "CREDIT",
            "amountMinor": 1000
        })

    post_payload = {
        "transactionType": "BULK_PIECE_RATE_SETTLEMENT",
        "currency": "IDR",
        "entries": entries
    }

    key = f"idemp-batch-100-{uuid.uuid4().hex}"
    post_resp = client.post(
        "/api/v1/ledger/transactions",
        headers={
            "Authorization": f"Bearer {tenant_fixture['finance_token_a']}",
            "Idempotency-Key": key
        },
        json=post_payload
    )
    assert post_resp.status_code == 201
    posted_data = post_resp.json()
    assert len(posted_data["entries"]) == 100
    tx_id = posted_data["id"]

    # Reversal of 100+ line transaction
    rev_key = f"idemp-rev-100-{uuid.uuid4().hex}"
    rev_resp = client.post(
        f"/api/v1/ledger/transactions/{tx_id}/reversals",
        headers={
            "Authorization": f"Bearer {tenant_fixture['finance_token_a']}",
            "Idempotency-Key": rev_key
        },
        json={"reason": "Reversing 100-line batch settlement"}
    )
    assert rev_resp.status_code == 201
    rev_data = rev_resp.json()
    assert rev_data["reversalOf"] == tx_id
    assert len(rev_data["entries"]) == 100

    # Verify that in the reversal, directions are exactly inverted:
    # 50 credits on CUSTODIAL_MATERIAL and 50 debits on CUSTODIAL_OBLIGATION
    rev_debits = sum(1 for e in rev_data["entries"] if e["direction"] == "DEBIT")
    rev_credits = sum(1 for e in rev_data["entries"] if e["direction"] == "CREDIT")
    assert rev_debits == 50
    assert rev_credits == 50


# ==============================================================================
# 9. Track 2 Adversarial Edge Cases: Auth, RFC 7807, Boundaries & Contract
# ==============================================================================

def test_bearer_authorization_header_case_insensitivity_and_malformed_formats(client, tenant_fixture):
    """Verify case-insensitive Bearer scheme and proper rejection of malformed headers."""
    token = tenant_fixture["finance_token_a"]

    # 1. Lowercase "bearer" is accepted
    resp_lower = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": f"bearer {token}"}
    )
    assert resp_lower.status_code == 200

    # 2. Uppercase "BEARER" is accepted
    resp_upper = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": f"BEARER {token}"}
    )
    assert resp_upper.status_code == 200

    # 3. "Bearer" with no token returns 401 AUTH_REQUIRED
    resp_empty_token = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": "Bearer"}
    )
    assert resp_empty_token.status_code == 401
    assert resp_empty_token.json()["code"] == "AUTH_REQUIRED"

    # 4. "Bearer   " (whitespace only) returns 401 AUTH_REQUIRED
    resp_ws = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": "Bearer    "}
    )
    assert resp_ws.status_code == 401
    assert resp_ws.json()["code"] == "AUTH_REQUIRED"

    # 5. Non-bearer scheme (e.g. Basic) returns 401 AUTH_REQUIRED
    resp_basic = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )
    assert resp_basic.status_code == 401
    assert resp_basic.json()["code"] == "AUTH_REQUIRED"


def test_jwt_claims_validation_attacks(client, tenant_fixture, db_admin):
    """Adversarial testing of JWT signature, expiration, required claims, and catalog existence."""
    tenant_id = tenant_fixture["tenant_a_id"]
    actor_id = tenant_fixture["actor_id"]

    # 1. Expired token returns 401 AUTH_REQUIRED
    expired_token = create_access_token(
        {"sub": str(actor_id), "roles": ["FinancePayroll"], "tenant_id": str(tenant_id)},
        expires_delta=timedelta(seconds=-60)
    )
    resp_exp = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp_exp.status_code == 401
    assert resp_exp.json()["code"] == "AUTH_REQUIRED"
    assert "expired" in resp_exp.json()["detail"].lower()

    # 2. Token without 'exp' claim is rejected (prevents perpetual un-expiring tokens)
    token_no_exp = jwt.encode(
        {"sub": str(actor_id), "roles": ["FinancePayroll"], "tenant_id": str(tenant_id)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    resp_no_exp = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {token_no_exp}"})
    assert resp_no_exp.status_code == 401
    assert resp_no_exp.json()["code"] == "AUTH_REQUIRED"

    # 3. Bad signature token returns 401 AUTH_REQUIRED
    bad_sig_token = jwt.encode(
        {"sub": str(actor_id), "roles": ["FinancePayroll"], "tenant_id": str(tenant_id), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "wrong-secret-key-12345678901234567890",
        algorithm="HS256"
    )
    resp_bad_sig = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {bad_sig_token}"})
    assert resp_bad_sig.status_code == 401
    assert resp_bad_sig.json()["code"] == "AUTH_REQUIRED"

    # 4. Token signed with algorithm 'none' is rejected
    none_alg_token = jwt.encode(
        {"sub": str(actor_id), "roles": ["FinancePayroll"], "tenant_id": str(tenant_id), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        key="",
        algorithm="none"
    )
    resp_none = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {none_alg_token}"})
    assert resp_none.status_code == 401
    assert resp_none.json()["code"] == "AUTH_REQUIRED"

    # 5. Token with non-UUID actor ID string returns 401 AUTH_REQUIRED (prevents 500 DB crash)
    bad_actor_token = jwt.encode(
        {"sub": "attacker_invalid_uuid", "roles": ["Owner"], "tenant_id": str(tenant_id), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    resp_bad_actor = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {bad_actor_token}"})
    assert resp_bad_actor.status_code == 401
    assert resp_bad_actor.json()["code"] == "AUTH_REQUIRED"

    # 6. Token with non-existent actor UUID returns 401 AUTH_REQUIRED
    non_existent_actor = uuid.uuid4()
    ghost_actor_token = jwt.encode(
        {"sub": str(non_existent_actor), "roles": ["Owner"], "tenant_id": str(tenant_id), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    resp_ghost_actor = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {ghost_actor_token}"})
    assert resp_ghost_actor.status_code == 401
    assert resp_ghost_actor.json()["code"] == "AUTH_REQUIRED"
    assert "not found" in resp_ghost_actor.json()["detail"].lower()

    # 7. Token with non-existent tenant UUID returns 403 FORBIDDEN
    non_existent_tenant = uuid.uuid4()
    ghost_tenant_token = jwt.encode(
        {"sub": str(actor_id), "roles": ["Owner"], "tenant_id": str(non_existent_tenant), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    resp_ghost_tenant = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {ghost_tenant_token}"})
    assert resp_ghost_tenant.status_code == 403
    assert resp_ghost_tenant.json()["code"] == "FORBIDDEN"
    assert "tenant" in resp_ghost_tenant.json()["detail"].lower()

    # 8. Token missing tenant claim returns 403 TENANT_CONTEXT_MISSING
    no_tenant_token = jwt.encode(
        {"sub": str(actor_id), "roles": ["Owner"], "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    resp_no_tenant = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {no_tenant_token}"})
    assert resp_no_tenant.status_code == 403
    assert resp_no_tenant.json()["code"] == "TENANT_CONTEXT_MISSING"

    # 9. Unauthorized roles return 403 FORBIDDEN
    for unauth_role in [["Tailor"], ["Warehouse"], ["QCInspector"], ["MaklonClient"], []]:
        bad_role_token = jwt.encode(
            {"sub": str(actor_id), "roles": unauth_role, "tenant_id": str(tenant_id), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            settings.SECRET_KEY,
            algorithm="HS256"
        )
        resp_role = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {bad_role_token}"})
        assert resp_role.status_code == 403
        assert resp_role.json()["code"] == "FORBIDDEN"


def test_recheck_caller_authorization_on_idempotent_replay(client, tenant_fixture):
    """
    R2 Invariant: Recheck caller authorization even on idempotent replays.
    A cached 201 response must NEVER be returned to an unauthenticated or unauthorized caller.
    """
    key = f"idemp-auth-replay-{uuid.uuid4().hex}"
    payload = {
        "transactionType": "WIP_ACCRUAL",
        "currency": "IDR",
        "entries": [
            {"accountCode": "WIP_DIRECT_LABOR", "direction": "DEBIT", "amountMinor": 150000},
            {"accountCode": "WAGES_PAYABLE", "direction": "CREDIT", "amountMinor": 150000}
        ]
    }

    # 1. Legitimate Finance user posts transaction -> 201 Created
    resp_legit = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp_legit.status_code == 201
    tx_id = resp_legit.json()["id"]

    # 2. Unauthenticated replay with identical key -> 401 AUTH_REQUIRED
    resp_no_auth = client.post(
        "/api/v1/ledger/transactions",
        headers={"Idempotency-Key": key},
        json=payload
    )
    assert resp_no_auth.status_code == 401
    assert resp_no_auth.json()["code"] == "AUTH_REQUIRED"

    # 3. Unauthorized role (Tailor) replay with identical key -> 403 FORBIDDEN
    resp_tailor = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['tailor_token_a']}", "Idempotency-Key": key},
        json=payload
    )
    assert resp_tailor.status_code == 403
    assert resp_tailor.json()["code"] == "FORBIDDEN"

    # 4. Cross-tenant replay: Tenant B using same key does NOT see Tenant A's cached response
    resp_tenant_b = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_b']}", "Idempotency-Key": key},
        json=payload
    )
    # Tenant B has isolated key namespace; creates a new transaction under Tenant B
    assert resp_tenant_b.status_code == 201
    assert resp_tenant_b.json()["tenantId"] == str(tenant_fixture["tenant_b_id"])
    assert resp_tenant_b.json()["id"] != tx_id


def test_rfc7807_problem_schema_strict_conformity_and_no_null_violations(client, tenant_fixture):
    """
    Ensure RFC 7807 Problem error responses strictly conform to openapi.yaml:
    - Never emit 'violations: null' on 401, 403, 404, 409 errors (violates non-nullable array schema).
    - Emit 'violations: [{field, message}]' on 400 validation errors.
    - Code strictly belongs to the 14 allowed enum values in openapi.yaml.
    """
    allowed_codes = {
        "AUTH_REQUIRED", "FORBIDDEN", "TENANT_CONTEXT_MISSING", "LEGAL_OWNER_MISMATCH",
        "ORDER_BENEFICIARY_MISMATCH", "IDEMPOTENCY_CONFLICT", "INVALID_STATE",
        "LEDGER_IMMUTABLE", "DUPLICATE_REPAIR_CREDIT", "FINANCIAL_RULE_PENDING",
        "VALIDATION_ERROR", "INSUFFICIENT_STOCK", "OVER_CONSUMPTION", "SERVICE_SCOPE_REQUIRED"
    }

    # 401 Check
    resp_401 = client.get("/api/v1/ledger/entries")
    assert resp_401.status_code == 401
    body_401 = resp_401.json()
    assert body_401["code"] in allowed_codes
    assert "violations" not in body_401 or body_401["violations"] is not None

    # 403 Check
    resp_403 = client.get("/api/v1/ledger/entries", headers={"Authorization": f"Bearer {tenant_fixture['tailor_token_a']}"})
    assert resp_403.status_code == 403
    body_403 = resp_403.json()
    assert body_403["code"] in allowed_codes
    assert "violations" not in body_403 or body_403["violations"] is not None

    # 404 Check
    resp_404 = client.post(
        f"/api/v1/ledger/transactions/{uuid.uuid4()}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": f"idemp-notfound-{uuid.uuid4().hex}"},
        json={"reason": "Testing 404 schema"}
    )
    assert resp_404.status_code == 404
    body_404 = resp_404.json()
    assert body_404["code"] in allowed_codes
    assert "violations" not in body_404 or body_404["violations"] is not None

    # 400 Validation Error Check (violations MUST be a non-null list of dicts with field and message)
    resp_400 = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": "short"},
        json={"transactionType": "A", "currency": "IDR", "entries": []}
    )
    assert resp_400.status_code == 400
    body_400 = resp_400.json()
    assert body_400["code"] in allowed_codes
    assert "violations" in body_400
    assert isinstance(body_400["violations"], list)
    assert len(body_400["violations"]) > 0
    for v in body_400["violations"]:
        assert "field" in v and "message" in v


def test_no_database_traces_exposed_in_error_responses(client, tenant_fixture):
    """
    R2 Invariant: Standardize error responses without exposing database traces (SQL, table names, psycopg error classes).
    """
    # 1. Unbalanced transaction
    resp_unbal = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": f"idemp-unbal-{uuid.uuid4().hex}"},
        json={
            "transactionType": "TEST",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 100},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 200}
            ]
        }
    )
    assert resp_unbal.status_code == 400
    detail_unbal = resp_unbal.json()["detail"]
    assert "psycopg" not in detail_unbal
    assert "SQL:" not in detail_unbal
    assert "SELECT " not in detail_unbal

    # 2. Duplicate reversal
    src_resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": f"idemp-src-db-{uuid.uuid4().hex}"},
        json={
            "transactionType": "CUSTODIAL_RECEIPT",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 50000},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 50000}
            ]
        }
    )
    src_id = src_resp.json()["id"]

    # Reversal 1
    rev1 = client.post(
        f"/api/v1/ledger/transactions/{src_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": f"idemp-rev1-{uuid.uuid4().hex}"},
        json={"reason": "First reversal"}
    )
    assert rev1.status_code == 201

    # Reversal 2 (duplicate)
    rev2 = client.post(
        f"/api/v1/ledger/transactions/{src_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": f"idemp-rev2-{uuid.uuid4().hex}"},
        json={"reason": "Second reversal"}
    )
    assert rev2.status_code == 409
    detail_dup = rev2.json()["detail"]
    assert "psycopg" not in detail_dup
    assert "SQL:" not in detail_dup
    assert "uq_ledger_tx_reversal" not in detail_dup


def test_idempotency_key_header_boundary_validation(client, tenant_fixture):
    """Verify OpenAPI header parameter Idempotency-Key boundary validation (16 <= length <= 200)."""
    valid_payload = {
        "transactionType": "CUSTODIAL_RECEIPT",
        "currency": "IDR",
        "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 5000},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 5000}
        ]
    }

    # 1. Missing header -> 400 Bad Request
    resp_missing = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"},
        json=valid_payload
    )
    assert resp_missing.status_code == 400
    assert resp_missing.json()["code"] == "VALIDATION_ERROR"
    assert any("Idempotency-Key" in v["field"] for v in resp_missing.json()["violations"])

    # 2. Length 15 (< 16) -> 400 Bad Request
    resp_too_short = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": "123456789012345"},
        json=valid_payload
    )
    assert resp_too_short.status_code == 400
    assert resp_too_short.json()["code"] == "VALIDATION_ERROR"

    # 3. Length 201 (> 200) -> 400 Bad Request
    resp_too_long = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": "k" * 201},
        json=valid_payload
    )
    assert resp_too_long.status_code == 400
    assert resp_too_long.json()["code"] == "VALIDATION_ERROR"

    # 4. Length 16 (minimum boundary) -> 201 Created
    resp_min = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": "k" * 16},
        json=valid_payload
    )
    assert resp_min.status_code == 201

    # 5. Length 200 (maximum boundary) -> 201 Created
    resp_max = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": "k" * 200},
        json=valid_payload
    )
    assert resp_max.status_code == 201


def test_reversal_path_uuid_validation(client, tenant_fixture):
    """Verify non-UUID path parameter on reversal endpoint returns 400 VALIDATION_ERROR with violation."""
    resp = client.post(
        "/api/v1/ledger/transactions/not-a-valid-uuid/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": f"idemp-baduuid-{uuid.uuid4().hex}"},
        json={"reason": "Testing bad UUID"}
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "violations" in body
    assert any("transactionId" in v["field"] for v in body["violations"])


def test_cursor_pagination_parameter_boundaries_and_resilience(client, tenant_fixture):
    """Verify pageSize boundary enforcement and cursor parsing resilience."""
    # 1. pageSize = 0 -> 400 VALIDATION_ERROR
    r0 = client.get("/api/v1/ledger/entries?pageSize=0", headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"})
    assert r0.status_code == 400
    assert r0.json()["code"] == "VALIDATION_ERROR"

    # 2. pageSize = 101 -> 400 VALIDATION_ERROR
    r101 = client.get("/api/v1/ledger/entries?pageSize=101", headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"})
    assert r101.status_code == 400
    assert r101.json()["code"] == "VALIDATION_ERROR"

    # 3. Empty cursor string -> handled as page 1 without failure
    r_empty = client.get("/api/v1/ledger/entries?cursor=", headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"})
    assert r_empty.status_code == 200

    # 4. Corrupt cursor (base64 of invalid format) -> 400 VALIDATION_ERROR
    import base64
    corrupt_cursor = base64.urlsafe_b64encode(b"2026-01-01|not-a-uuid").decode()
    r_corrupt = client.get(f"/api/v1/ledger/entries?cursor={corrupt_cursor}", headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"})
    assert r_corrupt.status_code == 400
    assert r_corrupt.json()["code"] == "VALIDATION_ERROR"


def test_openapi_schema_contract_conformity():
    """Verify app.openapi() generates schema matching openapi.yaml contracts."""
    schema = app.openapi()

    # 1. Bearer security scheme declared
    assert "bearerAuth" in schema["components"]["securitySchemes"]
    assert schema["components"]["securitySchemes"]["bearerAuth"]["type"] == "http"
    assert schema["components"]["securitySchemes"]["bearerAuth"]["scheme"] == "bearer"
    assert schema["components"]["securitySchemes"]["bearerAuth"]["bearerFormat"] == "JWT"

    # 2. Problem and Violation schemas present
    assert "Problem" in schema["components"]["schemas"]
    assert "Violation" in schema["components"]["schemas"]

    # 3. Default 422 HTTPValidationError removed
    assert "HTTPValidationError" not in schema["components"]["schemas"]

    # 4. Check ledger endpoints
    ledger_post = schema["paths"]["/api/v1/ledger/transactions"]["post"]
    assert "401" in ledger_post["responses"]
    assert "403" in ledger_post["responses"]
    assert "400" in ledger_post["responses"]
    assert "409" in ledger_post["responses"]
    assert "422" not in ledger_post["responses"]

    reversal_post = schema["paths"]["/api/v1/ledger/transactions/{transactionId}/reversals"]["post"]
    assert "401" in reversal_post["responses"]
    assert "403" in reversal_post["responses"]
    assert "404" in reversal_post["responses"]
    assert "409" in reversal_post["responses"]
    assert "422" not in reversal_post["responses"]

    entries_get = schema["paths"]["/api/v1/ledger/entries"]["get"]
    assert "401" in entries_get["responses"]
    assert "403" in entries_get["responses"]
    assert "422" not in entries_get["responses"]


# ==============================================================================
# 10. Track 3 Comprehensive Negative Boundary & Unprivileged Role Hardening
# ==============================================================================

def test_unprivileged_role_table_privilege_revocations(db_app, tenant_fixture):
    """
    R1 Invariant Hardening: Direct UPDATE and DELETE table privileges are REVOKED
    from the runtime unprivileged application role (lukla_app) across all core tables.
    Attempts to mutate ledger_transactions, ledger_entries, audit_events, or idempotency_records
    raise PostgreSQL permission denied errors.
    """
    tenant_id = tenant_fixture["tenant_a_id"]
    db_app.execute(text("SELECT set_request_context(:t_id)"), {"t_id": str(tenant_id)})

    # 1. UPDATE on ledger_transactions -> permission denied
    with pytest.raises(Exception) as exc_update_tx:
        db_app.execute(
            text("UPDATE ledger_transactions SET transaction_type = 'HACK' WHERE tenant_id = :t_id"),
            {"t_id": str(tenant_id)}
        )
    assert "permission denied" in str(exc_update_tx.value).lower()
    db_app.rollback()

    # 2. DELETE on ledger_transactions -> permission denied
    with pytest.raises(Exception) as exc_delete_tx:
        db_app.execute(
            text("DELETE FROM ledger_transactions WHERE tenant_id = :t_id"),
            {"t_id": str(tenant_id)}
        )
    assert "permission denied" in str(exc_delete_tx.value).lower()
    db_app.rollback()

    # 3. UPDATE on ledger_entries -> permission denied
    with pytest.raises(Exception) as exc_update_entry:
        db_app.execute(
            text("UPDATE ledger_entries SET amount_minor = 1 WHERE tenant_id = :t_id"),
            {"t_id": str(tenant_id)}
        )
    assert "permission denied" in str(exc_update_entry.value).lower()
    db_app.rollback()

    # 4. DELETE on ledger_entries -> permission denied
    with pytest.raises(Exception) as exc_delete_entry:
        db_app.execute(
            text("DELETE FROM ledger_entries WHERE tenant_id = :t_id"),
            {"t_id": str(tenant_id)}
        )
    assert "permission denied" in str(exc_delete_entry.value).lower()
    db_app.rollback()

    # 5. UPDATE on audit_events -> permission denied
    with pytest.raises(Exception) as exc_update_audit:
        db_app.execute(
            text("UPDATE audit_events SET action = 'HACKED' WHERE tenant_id = :t_id"),
            {"t_id": str(tenant_id)}
        )
    assert "permission denied" in str(exc_update_audit.value).lower()
    db_app.rollback()

    # 6. DELETE on audit_events -> permission denied
    with pytest.raises(Exception) as exc_delete_audit:
        db_app.execute(
            text("DELETE FROM audit_events WHERE tenant_id = :t_id"),
            {"t_id": str(tenant_id)}
        )
    assert "permission denied" in str(exc_delete_audit.value).lower()
    db_app.rollback()

    # 7. DELETE on idempotency_records -> permission denied
    with pytest.raises(Exception) as exc_delete_idemp:
        db_app.execute(
            text("DELETE FROM idempotency_records WHERE tenant_id = :t_id"),
            {"t_id": str(tenant_id)}
        )
    assert "permission denied" in str(exc_delete_idemp.value).lower()
    db_app.rollback()


def test_privileged_role_immutability_triggers(db_admin, tenant_fixture, client):
    """
    R1 Invariant Hardening: Strict immutability is hardened at the database trigger layer.
    Even when connected as a table-privileged superuser (bypassing GRANT/REVOKE),
    the PL/pgSQL BEFORE UPDATE OR DELETE triggers raise LEDGER_IMMUTABLE (SQLSTATE 55000).
    """
    tenant_id = tenant_fixture["tenant_a_id"]

    # Post a transaction via API
    key = f"idemp-trig-immut-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json={
            "transactionType": "CUSTODIAL_RECEIPT",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 350000},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 350000}
            ]
        }
    )
    assert resp.status_code == 201
    tx_id = resp.json()["id"]

    # 1. Superuser UPDATE on ledger_transactions raises LEDGER_IMMUTABLE
    with pytest.raises(Exception) as exc_up_tx:
        db_admin.execute(
            text("UPDATE ledger_transactions SET transaction_type = 'MODIFIED' WHERE id = :id"),
            {"id": str(tx_id)}
        )
        db_admin.commit()
    assert "LEDGER_IMMUTABLE" in str(exc_up_tx.value)
    db_admin.rollback()

    # 2. Superuser DELETE on ledger_transactions raises LEDGER_IMMUTABLE
    with pytest.raises(Exception) as exc_del_tx:
        db_admin.execute(
            text("DELETE FROM ledger_transactions WHERE id = :id"),
            {"id": str(tx_id)}
        )
        db_admin.commit()
    assert "LEDGER_IMMUTABLE" in str(exc_del_tx.value)
    db_admin.rollback()

    # 3. Superuser UPDATE on ledger_entries raises LEDGER_IMMUTABLE
    with pytest.raises(Exception) as exc_up_entry:
        db_admin.execute(
            text("UPDATE ledger_entries SET amount_minor = 999999 WHERE transaction_id = :id"),
            {"id": str(tx_id)}
        )
        db_admin.commit()
    assert "LEDGER_IMMUTABLE" in str(exc_up_entry.value)
    db_admin.rollback()

    # 4. Superuser DELETE on ledger_entries raises LEDGER_IMMUTABLE
    with pytest.raises(Exception) as exc_del_entry:
        db_admin.execute(
            text("DELETE FROM ledger_entries WHERE transaction_id = :id"),
            {"id": str(tx_id)}
        )
        db_admin.commit()
    assert "LEDGER_IMMUTABLE" in str(exc_del_entry.value)
    db_admin.rollback()


def test_entry_check_constraints_negative_and_zero_amounts_and_invalid_direction(tenant_fixture):
    """
    R1 Table Check Constraints:
    - amount_minor > 0 (strictly positive; zero and negative amounts rejected)
    - direction IN ('DEBIT', 'CREDIT') (all other strings rejected)
    """
    tenant_id = tenant_fixture["tenant_a_id"]

    # Obtain valid account
    with app_engine.connect() as conn:
        conn.execute(text("SELECT set_config('app.tenant_id', :t_id, false)"), {"t_id": str(tenant_id)})
        acct = conn.execute(text("SELECT id FROM ledger_accounts WHERE tenant_id = :t_id LIMIT 1"), {"t_id": str(tenant_id)}).scalar_one()

    # 1. Non-positive amounts: 0, -1, -500000
    for bad_amount in [0, -1, -500000]:
        with pytest.raises(Exception) as exc_amt:
            with app_engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
                    tx_id = uuid.uuid4()
                    conn.execute(
                        text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'TEST')"),
                        {"id": str(tx_id), "t_id": str(tenant_id)}
                    )
                    conn.execute(
                        text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', :amt, 'IDR')"),
                        {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct), "amt": bad_amount}
                    )
        assert "chk_entry_amount_positive" in str(exc_amt.value) or "amount_minor" in str(exc_amt.value)

    # 2. Invalid directions: SIDEWAYS, INVALID, debit (lowercase), credit (lowercase), empty string
    for bad_dir in ["SIDEWAYS", "INVALID", "debit", "credit", ""]:
        with pytest.raises(Exception) as exc_dir:
            with app_engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
                    tx_id = uuid.uuid4()
                    conn.execute(
                        text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'TEST')"),
                        {"id": str(tx_id), "t_id": str(tenant_id)}
                    )
                    conn.execute(
                        text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, :dir, 1000, 'IDR')"),
                        {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct), "dir": bad_dir}
                    )
        assert "chk_entry_direction" in str(exc_dir.value) or "direction" in str(exc_dir.value)


def test_one_sided_transaction_direct_sql_deferred_trigger(tenant_fixture):
    """
    R1 Invariant: Deferred zero-sum trigger must reject one-sided transactions:
    - Transactions with ONLY debits (0 credits) raise EMPTY_OR_ONE_SIDED_TRANSACTION.
    - Transactions with ONLY credits (0 debits) raise EMPTY_OR_ONE_SIDED_TRANSACTION.
    """
    tenant_id = tenant_fixture["tenant_a_id"]

    with app_engine.connect() as conn:
        conn.execute(text("SELECT set_config('app.tenant_id', :t_id, false)"), {"t_id": str(tenant_id)})
        accts = conn.execute(text("SELECT id FROM ledger_accounts WHERE tenant_id = :t_id LIMIT 2"), {"t_id": str(tenant_id)}).fetchall()
        acct1, acct2 = accts[0][0], accts[1][0]

    # 1. Debit-only transaction (2 debits, 0 credits)
    with pytest.raises(Exception) as exc_debit_only:
        with app_engine.connect() as conn:
            with conn.begin():
                conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
                tx_id = uuid.uuid4()
                conn.execute(
                    text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'TEST_DEBIT_ONLY')"),
                    {"id": str(tx_id), "t_id": str(tenant_id)}
                )
                conn.execute(
                    text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', 500, 'IDR')"),
                    {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct1)}
                )
                conn.execute(
                    text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', 500, 'IDR')"),
                    {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct2)}
                )
    assert "EMPTY_OR_ONE_SIDED_TRANSACTION" in str(exc_debit_only.value)

    # 2. Credit-only transaction (2 credits, 0 debits)
    with pytest.raises(Exception) as exc_credit_only:
        with app_engine.connect() as conn:
            with conn.begin():
                conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
                tx_id = uuid.uuid4()
                conn.execute(
                    text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'TEST_CREDIT_ONLY')"),
                    {"id": str(tx_id), "t_id": str(tenant_id)}
                )
                conn.execute(
                    text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'CREDIT', 500, 'IDR')"),
                    {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct1)}
                )
                conn.execute(
                    text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'CREDIT', 500, 'IDR')"),
                    {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(acct2)}
                )
    assert "EMPTY_OR_ONE_SIDED_TRANSACTION" in str(exc_credit_only.value)


def test_multi_currency_balancing_in_direct_sql(tenant_fixture, db_admin):
    """
    R1 Invariant: Deferred zero-sum trigger must balance PER CURRENCY:
    - Multi-currency entries where total debit == total credit across currencies
      but individual currency balance != 0 must fail with TRANSACTION_UNBALANCED.
    - Multi-currency entries balanced per currency must commit successfully.
    """
    tenant_id = tenant_fixture["tenant_a_id"]

    # Create USD accounts for tenant A
    db_admin.execute(
        text("INSERT INTO ledger_accounts (tenant_id, code, name, account_class, currency, active) VALUES (:t_id, 'USD_MATERIAL', 'USD Material', 'ASSET', 'USD', true) ON CONFLICT DO NOTHING"),
        {"t_id": str(tenant_id)}
    )
    db_admin.execute(
        text("INSERT INTO ledger_accounts (tenant_id, code, name, account_class, currency, active) VALUES (:t_id, 'USD_OBLIGATION', 'USD Obligation', 'LIABILITY', 'USD', true) ON CONFLICT DO NOTHING"),
        {"t_id": str(tenant_id)}
    )
    db_admin.commit()

    with app_engine.connect() as conn:
        conn.execute(text("SELECT set_config('app.tenant_id', :t_id, false)"), {"t_id": str(tenant_id)})
        idr_acct = conn.execute(text("SELECT id FROM ledger_accounts WHERE tenant_id = :t_id AND currency = 'IDR' LIMIT 1"), {"t_id": str(tenant_id)}).scalar_one()
        usd_acct = conn.execute(text("SELECT id FROM ledger_accounts WHERE tenant_id = :t_id AND currency = 'USD' LIMIT 1"), {"t_id": str(tenant_id)}).scalar_one()

    # 1. Unbalanced multi-currency: Debit 1000 IDR, Credit 1000 USD (equal absolute amounts, unbalanced per currency)
    with pytest.raises(Exception) as exc_unbal:
        with app_engine.connect() as conn:
            with conn.begin():
                conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
                tx_id = uuid.uuid4()
                conn.execute(
                    text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'MULTI_CURR_UNBAL')"),
                    {"id": str(tx_id), "t_id": str(tenant_id)}
                )
                conn.execute(
                    text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', 1000, 'IDR')"),
                    {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(idr_acct)}
                )
                conn.execute(
                    text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'CREDIT', 1000, 'USD')"),
                    {"t_id": str(tenant_id), "tx_id": str(tx_id), "acct": str(usd_acct)}
                )
    assert "TRANSACTION_UNBALANCED" in str(exc_unbal.value)

    # 2. Balanced multi-currency: Debit 1000 IDR, Credit 1000 IDR, Debit 200 USD, Credit 200 USD
    with app_engine.connect() as conn:
        with conn.begin():
            conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
            ok_tx_id = uuid.uuid4()
            conn.execute(
                text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type) VALUES (:id, :t_id, 'MULTI_CURR_BAL')"),
                {"id": str(ok_tx_id), "t_id": str(tenant_id)}
            )
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', 1000, 'IDR')"),
                {"t_id": str(tenant_id), "tx_id": str(ok_tx_id), "acct": str(idr_acct)}
            )
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'CREDIT', 1000, 'IDR')"),
                {"t_id": str(tenant_id), "tx_id": str(ok_tx_id), "acct": str(idr_acct)}
            )
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'DEBIT', 200, 'USD')"),
                {"t_id": str(tenant_id), "tx_id": str(ok_tx_id), "acct": str(usd_acct)}
            )
            conn.execute(
                text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_id, :tx_id, :acct, 'CREDIT', 200, 'USD')"),
                {"t_id": str(tenant_id), "tx_id": str(ok_tx_id), "acct": str(usd_acct)}
            )

        # Confirm 4 entries exist with tenant context set
        conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
        entry_count = conn.execute(
            text("SELECT count(*) FROM ledger_entries WHERE transaction_id = :tx_id"),
            {"tx_id": str(ok_tx_id)}
        ).scalar()
        assert entry_count == 4


def test_composite_foreign_key_transaction_isolation(tenant_fixture, client):
    """
    R1 Invariant: Composite Foreign Key fk_ledger_entries_transaction
    Attempting to attach an entry under Tenant B to Tenant A's transaction
    violates (tenant_id, transaction_id) composite FK at the relational layer
    (or triggers TRANSACTION_NOT_FOUND in the late-line trigger).
    """
    tenant_a = tenant_fixture["tenant_a_id"]
    tenant_b = tenant_fixture["tenant_b_id"]

    # Post a transaction in Tenant A via API
    key = f"idemp-fk-tx-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": key},
        json={
            "transactionType": "CUSTODIAL_RECEIPT",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 200000},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 200000}
            ]
        }
    )
    assert resp.status_code == 201
    tx_a_id = resp.json()["id"]

    # Attempt to insert entry under Tenant B pointing to Tenant A's transaction
    with pytest.raises(Exception) as exc_fk_tx:
        with app_engine.connect() as conn:
            with conn.begin():
                conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_b)})
                acct_b = conn.execute(text("SELECT id FROM ledger_accounts WHERE tenant_id = :t_id LIMIT 1"), {"t_id": str(tenant_b)}).scalar_one()
                conn.execute(
                    text("INSERT INTO ledger_entries (tenant_id, transaction_id, account_id, direction, amount_minor, currency) VALUES (:t_b, :tx_a, :acct, 'DEBIT', 100, 'IDR')"),
                    {"t_b": str(tenant_b), "tx_a": str(tx_a_id), "acct": str(acct_b)}
                )
    assert "TRANSACTION_NOT_FOUND" in str(exc_fk_tx.value) or "fk_ledger_entries_transaction" in str(exc_fk_tx.value)


def test_reversal_database_triggers_and_indexes(tenant_fixture, client):
    """
    R1 Invariant: Database-level enforcement of reversal constraints:
    - Partial unique index uq_ledger_tx_reversal prevents duplicate reversals in direct SQL.
    - Trigger trg_fn_check_reversal_of_reversal forbids reversing a reversal in direct SQL.
    """
    tenant_id = tenant_fixture["tenant_a_id"]

    # 1. Post original transaction
    p_key = f"idemp-sql-rev-src-{uuid.uuid4().hex}"
    p_resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": p_key},
        json={
            "transactionType": "CUSTODIAL_RECEIPT",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 100000},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 100000}
            ]
        }
    )
    assert p_resp.status_code == 201
    orig_tx_id = p_resp.json()["id"]

    # 2. Reverse it
    r_key = f"idemp-sql-rev-rev-{uuid.uuid4().hex}"
    r_resp = client.post(
        f"/api/v1/ledger/transactions/{orig_tx_id}/reversals",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": r_key},
        json={"reason": "Testing SQL constraints"}
    )
    assert r_resp.status_code == 201
    rev_tx_id = r_resp.json()["id"]

    # 3. Direct SQL: Attempt duplicate reversal on orig_tx_id -> fails uq_ledger_tx_reversal
    with pytest.raises(Exception) as exc_dup:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
            conn.execute(
                text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type, reversal_of) VALUES (gen_random_uuid(), :t_id, 'DUP_REV', :orig)"),
                {"t_id": str(tenant_id), "orig": str(orig_tx_id)}
            )
            tx.commit()
    assert "uq_ledger_tx_reversal" in str(exc_dup.value)

    # 4. Direct SQL: Attempt to reverse rev_tx_id -> fails CANNOT_REVERSE_REVERSAL
    with pytest.raises(Exception) as exc_rev_rev:
        with app_engine.connect() as conn:
            tx = conn.begin()
            conn.execute(text("SELECT set_config('app.tenant_id', :t_id, true)"), {"t_id": str(tenant_id)})
            conn.execute(
                text("INSERT INTO ledger_transactions (id, tenant_id, transaction_type, reversal_of) VALUES (gen_random_uuid(), :t_id, 'REV_OF_REV', :rev)"),
                {"t_id": str(tenant_id), "rev": str(rev_tx_id)}
            )
            tx.commit()
    assert "CANNOT_REVERSE_REVERSAL" in str(exc_rev_rev.value)


def test_stored_procedure_security_definer_and_search_path(db_app):
    """
    R1 Security Definer: Harden all stored procedures (set_request_context,
    append_ledger_transaction, seed_operational_accounts) with SECURITY DEFINER
    and SET search_path = pg_catalog, public.
    """
    rows = db_app.execute(
        text("SELECT proname, prosecdef, proconfig FROM pg_proc WHERE proname IN ('set_request_context', 'append_ledger_transaction', 'seed_operational_accounts')")
    ).fetchall()

    proc_map = {row[0]: (row[1], row[2]) for row in rows}
    for name in ["set_request_context", "append_ledger_transaction", "seed_operational_accounts"]:
        assert name in proc_map, f"Missing procedure {name}"
        is_secdef, config = proc_map[name]
        assert is_secdef is True, f"Procedure {name} must be SECURITY DEFINER"
        assert config is not None and any("search_path=pg_catalog, public" in c for c in config), (
            f"Procedure {name} search_path must be 'pg_catalog, public', got {config}"
        )


def test_rls_catalog_and_cross_tenant_isolation_all_five_tables(db_app, tenant_fixture, client):
    """
    R1 Row Level Security:
    - ENABLE ROW LEVEL SECURITY and FORCE ROW LEVEL SECURITY are active on all tenant tables
      (ledger_accounts, ledger_transactions, ledger_entries, idempotency_records, audit_events).
    - Unauthorized tenant queries return 0 rows across all 5 tables.
    """
    tenant_a = tenant_fixture["tenant_a_id"]
    tenant_b = tenant_fixture["tenant_b_id"]

    # 1. Verify pg_class catalog flags for all 5 tables
    tables = ["ledger_accounts", "ledger_transactions", "ledger_entries", "idempotency_records", "audit_events"]
    for table_name in tables:
        row = db_app.execute(
            text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = :tbl"),
            {"tbl": table_name}
        ).fetchone()
        assert row is not None, f"Table {table_name} not found"
        assert row[0] is True, f"Table {table_name} must have ENABLE ROW LEVEL SECURITY"
        assert row[1] is True, f"Table {table_name} must have FORCE ROW LEVEL SECURITY"

    # 2. Populate Tenant A records
    post_key = f"idemp-rls-all5-{uuid.uuid4().hex}"
    resp = client.post(
        "/api/v1/ledger/transactions",
        headers={"Authorization": f"Bearer {tenant_fixture['finance_token_a']}", "Idempotency-Key": post_key},
        json={
            "transactionType": "CUSTODIAL_RECEIPT",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 650000},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 650000}
            ]
        }
    )
    assert resp.status_code == 201

    # 3. Query as Tenant B: all 5 tables must return 0 rows belonging to Tenant A
    db_app.execute(text("SELECT set_request_context(:t_b)"), {"t_b": str(tenant_b)})

    for tbl in tables:
        count = db_app.execute(
            text(f"SELECT count(*) FROM {tbl} WHERE tenant_id = :t_a"),
            {"t_a": str(tenant_a)}
        ).scalar()
        assert count == 0, f"Table {tbl} leaked Tenant A rows to Tenant B session!"

    # 4. Query with reset / un-scoped context: all 5 tables return 0 rows
    db_app.execute(text("SELECT set_request_context('00000000-0000-0000-0000-000000000000'::uuid)"))
    for tbl in tables:
        count = db_app.execute(text(f"SELECT count(*) FROM {tbl}")).scalar()
        assert count == 0, f"Table {tbl} leaked rows to un-scoped session!"


def test_api_entry_negative_boundaries_and_one_sided_validation(client, tenant_fixture):
    """
    R2 API Negative Boundaries:
    - amountMinor <= 0 rejected with 400 VALIDATION_ERROR.
    - direction not in ('DEBIT', 'CREDIT') rejected with 400 VALIDATION_ERROR.
    - entries array < 2 rejected with 400 VALIDATION_ERROR.
    - one-sided entries (all DEBIT or all CREDIT) rejected with 400 VALIDATION_ERROR.
    - non-ISO currency strings rejected with 400 VALIDATION_ERROR.
    """
    auth_header = {"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}

    # 1. amountMinor = 0
    r_zero = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-bound-0-{uuid.uuid4().hex}"},
        json={"transactionType": "TEST", "currency": "IDR", "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 0},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 0}
        ]}
    )
    assert r_zero.status_code == 400
    assert r_zero.json()["code"] == "VALIDATION_ERROR"
    assert any("amountMinor" in v["field"] for v in r_zero.json()["violations"])

    # 2. amountMinor = -500
    r_neg = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-bound-neg-{uuid.uuid4().hex}"},
        json={"transactionType": "TEST", "currency": "IDR", "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": -500},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": -500}
        ]}
    )
    assert r_neg.status_code == 400
    assert r_neg.json()["code"] == "VALIDATION_ERROR"
    assert any("amountMinor" in v["field"] for v in r_neg.json()["violations"])

    # 3. direction = 'SIDEWAYS'
    r_dir = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-bound-dir-{uuid.uuid4().hex}"},
        json={"transactionType": "TEST", "currency": "IDR", "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "SIDEWAYS", "amountMinor": 100},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 100}
        ]}
    )
    assert r_dir.status_code == 400
    assert r_dir.json()["code"] == "VALIDATION_ERROR"
    assert any("direction" in v["field"] for v in r_dir.json()["violations"])

    # 4. entries = [] (empty)
    r_empty = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-bound-empty-{uuid.uuid4().hex}"},
        json={"transactionType": "TEST", "currency": "IDR", "entries": []}
    )
    assert r_empty.status_code == 400
    assert r_empty.json()["code"] == "VALIDATION_ERROR"
    assert any("entries" in v["field"] for v in r_empty.json()["violations"])

    # 5. entries = [1 entry] (single entry)
    r_single = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-bound-single-{uuid.uuid4().hex}"},
        json={"transactionType": "TEST", "currency": "IDR", "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 100}
        ]}
    )
    assert r_single.status_code == 400
    assert r_single.json()["code"] == "VALIDATION_ERROR"
    assert any("entries" in v["field"] for v in r_single.json()["violations"])

    # 6. One-sided entries: 2 DEBITS, 0 CREDITS
    r_debits = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-bound-deb-{uuid.uuid4().hex}"},
        json={"transactionType": "TEST", "currency": "IDR", "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 100},
            {"accountCode": "RAW_MATERIAL_ASSET", "direction": "DEBIT", "amountMinor": 100}
        ]}
    )
    assert r_debits.status_code == 400
    assert r_debits.json()["code"] == "VALIDATION_ERROR"
    assert "at least one debit and at least one credit" in r_debits.json()["detail"].lower()

    # 7. One-sided entries: 2 CREDITS, 0 DEBITS
    r_credits = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-bound-cred-{uuid.uuid4().hex}"},
        json={"transactionType": "TEST", "currency": "IDR", "entries": [
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 100},
            {"accountCode": "ACCOUNTS_PAYABLE", "direction": "CREDIT", "amountMinor": 100}
        ]}
    )
    assert r_credits.status_code == 400
    assert r_credits.json()["code"] == "VALIDATION_ERROR"
    assert "at least one debit and at least one credit" in r_credits.json()["detail"].lower()

    # 8. Lowercase currency "idr"
    r_curr_lower = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-bound-currl-{uuid.uuid4().hex}"},
        json={"transactionType": "TEST", "currency": "idr", "entries": [
            {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 100},
            {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 100}
        ]}
    )
    assert r_curr_lower.status_code == 400
    assert r_curr_lower.json()["code"] == "VALIDATION_ERROR"
    assert any("currency" in v["field"] for v in r_curr_lower.json()["violations"])


def test_api_reversal_request_body_validation(client, tenant_fixture):
    """
    R2 API Negative Boundaries: ReversalRequest body validation:
    - Missing body or empty body returns 400 VALIDATION_ERROR.
    - Non-string reason returns 400 VALIDATION_ERROR.
    """
    auth_header = {"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}
    fake_tx_id = uuid.uuid4()

    # 1. Empty body {}
    r_empty_body = client.post(
        f"/api/v1/ledger/transactions/{fake_tx_id}/reversals",
        headers={**auth_header, "Idempotency-Key": f"idemp-rev-body-emp-{uuid.uuid4().hex}"},
        json={}
    )
    assert r_empty_body.status_code == 400
    assert r_empty_body.json()["code"] == "VALIDATION_ERROR"
    assert any("reason" in v["field"] for v in r_empty_body.json()["violations"])

    # 2. Non-string reason {"reason": 12345}
    r_bad_type = client.post(
        f"/api/v1/ledger/transactions/{fake_tx_id}/reversals",
        headers={**auth_header, "Idempotency-Key": f"idemp-rev-body-typ-{uuid.uuid4().hex}"},
        json={"reason": 12345}
    )
    assert r_bad_type.status_code == 400
    assert r_bad_type.json()["code"] == "VALIDATION_ERROR"
    assert any("reason" in v["field"] for v in r_bad_type.json()["violations"])


def test_account_resolution_negative_controls_database_rollback(client, tenant_fixture, db_app):
    """
    R2 & R3 Invariant: Account resolution failure rolls back completely:
    No rows are committed in ledger_transactions, ledger_entries, or idempotency_records.
    Verified using unprivileged db_app session.
    """
    tenant_id = tenant_fixture["tenant_a_id"]
    auth_header = {"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}
    db_app.execute(text("SELECT set_request_context(:t_id)"), {"t_id": str(tenant_id)})

    # Initial transaction count
    initial_tx_count = len(db_app.execute(select(LedgerTransaction).filter_by(tenant_id=tenant_id)).scalars().all())

    # 1. Unknown accountCode
    unk_key = f"idemp-rollback-unk-{uuid.uuid4().hex}"
    resp_unk = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": unk_key},
        json={
            "transactionType": "TEST",
            "currency": "IDR",
            "entries": [
                {"accountCode": "GHOST_ACCOUNT", "direction": "DEBIT", "amountMinor": 1000},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 1000}
            ]
        }
    )
    assert resp_unk.status_code == 400

    # Verify zero db state change
    db_app.rollback()
    db_app.execute(text("SELECT set_request_context(:t_id)"), {"t_id": str(tenant_id)})
    tx_count_1 = len(db_app.execute(select(LedgerTransaction).filter_by(tenant_id=tenant_id)).scalars().all())
    assert tx_count_1 == initial_tx_count
    idemp_1 = db_app.execute(select(IdempotencyRecord).filter_by(tenant_id=tenant_id, key=unk_key)).scalar_one_or_none()
    assert idemp_1 is None

    # 2. Inactive accountCode
    inact_key = f"idemp-rollback-inact-{uuid.uuid4().hex}"
    # Deactivate account via direct SQL in admin
    with admin_engine.connect() as conn:
        conn.execute(text("UPDATE ledger_accounts SET active = false WHERE tenant_id = :t_id AND code = 'WIP_DIRECT_LABOR'"), {"t_id": str(tenant_id)})
        conn.commit()

    resp_inact = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": inact_key},
        json={
            "transactionType": "TEST",
            "currency": "IDR",
            "entries": [
                {"accountCode": "WIP_DIRECT_LABOR", "direction": "DEBIT", "amountMinor": 1000},
                {"accountCode": "WAGES_PAYABLE", "direction": "CREDIT", "amountMinor": 1000}
            ]
        }
    )
    assert resp_inact.status_code == 400

    # Reactivate
    with admin_engine.connect() as conn:
        conn.execute(text("UPDATE ledger_accounts SET active = true WHERE tenant_id = :t_id AND code = 'WIP_DIRECT_LABOR'"), {"t_id": str(tenant_id)})
        conn.commit()

    db_app.rollback()
    db_app.execute(text("SELECT set_request_context(:t_id)"), {"t_id": str(tenant_id)})
    tx_count_2 = len(db_app.execute(select(LedgerTransaction).filter_by(tenant_id=tenant_id)).scalars().all())
    assert tx_count_2 == initial_tx_count
    idemp_2 = db_app.execute(select(IdempotencyRecord).filter_by(tenant_id=tenant_id, key=inact_key)).scalar_one_or_none()
    assert idemp_2 is None


def test_reversal_persists_audit_event(client, tenant_fixture, db_app):
    """
    R2 Invariant: Reversals persist an associated audit_events row
    with action='LEDGER_TRANSACTION_REVERSED' within the same ACID transaction.
    """
    tenant_id = tenant_fixture["tenant_a_id"]
    auth_header = {"Authorization": f"Bearer {tenant_fixture['finance_token_a']}"}

    # Post initial transaction
    post_resp = client.post(
        "/api/v1/ledger/transactions",
        headers={**auth_header, "Idempotency-Key": f"idemp-audit-rev-src-{uuid.uuid4().hex}"},
        json={
            "transactionType": "CUSTODIAL_RECEIPT",
            "currency": "IDR",
            "entries": [
                {"accountCode": "CUSTODIAL_MATERIAL", "direction": "DEBIT", "amountMinor": 420000},
                {"accountCode": "CUSTODIAL_OBLIGATION", "direction": "CREDIT", "amountMinor": 420000}
            ]
        }
    )
    assert post_resp.status_code == 201
    orig_tx_id = post_resp.json()["id"]

    # Reverse transaction
    reversal_reason = "Customer canceled Maklon batch"
    rev_resp = client.post(
        f"/api/v1/ledger/transactions/{orig_tx_id}/reversals",
        headers={**auth_header, "Idempotency-Key": f"idemp-audit-rev-exec-{uuid.uuid4().hex}"},
        json={"reason": reversal_reason}
    )
    assert rev_resp.status_code == 201
    rev_tx_id = uuid.UUID(rev_resp.json()["id"])

    # Query audit_events using unprivileged db_app
    db_app.execute(text("SELECT set_request_context(:t_id)"), {"t_id": str(tenant_id)})
    audit = db_app.execute(
        select(AuditEvent).filter_by(
            tenant_id=tenant_id,
            entity_type="ledger_transactions",
            entity_id=rev_tx_id
        )
    ).scalar_one_or_none()

    assert audit is not None
    assert audit.action == "LEDGER_TRANSACTION_REVERSED"
    assert audit.payload.get("reversal_of") == orig_tx_id
    assert audit.payload.get("reason") == reversal_reason


def test_empty_ledger_pagination(client, db_admin):
    """
    R2 Invariant: GET /api/v1/ledger/entries on a newly created tenant with 0 transactions
    returns 200 OK with items=[] and nextCursor=None.
    """
    new_tenant_id = uuid.uuid4()
    new_actor_id = uuid.uuid4()

    new_tenant = Tenant(
        id=new_tenant_id,
        tenant_code=f"TENANT_EMPTY_{uuid.uuid4().hex[:6]}",
        name="Empty Tenant Fabrics",
        kind="CLIENT",
        active=True
    )
    new_actor = Actor(
        id=new_actor_id,
        email=f"empty_{uuid.uuid4().hex[:6]}@lukla.io",
        display_name="Empty Tenant Finance",
        active=True
    )
    db_admin.add_all([new_tenant, new_actor])
    db_admin.commit()

    token = create_access_token({
        "sub": str(new_actor_id),
        "roles": ["FinancePayroll"],
        "tenant_id": str(new_tenant_id)
    })

    resp = client.get(
        "/api/v1/ledger/entries",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["nextCursor"] is None



