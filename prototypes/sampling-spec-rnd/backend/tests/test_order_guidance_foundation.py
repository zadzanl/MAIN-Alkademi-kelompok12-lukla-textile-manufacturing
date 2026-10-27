"""Focused phase-one checks for persistence and server-derived session scope."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.auth_deps import SessionContext, can_access_record, require_roles, session_context
from src.services.auth_store import AuthStore
from src.services.ops_store import OpsStore, StoreScope, SnapshotError
from src.api.routes import create_api_router


def test_store_schema_pragmas_and_restart_persistence(tmp_path: Path) -> None:
    path = tmp_path / "ops.db"
    store = OpsStore(path)
    with store._migration_connection() as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}
    assert {"sample_versions", "approvals", "orders", "order_confirmations", "audit_events", "idempotency_records"} <= tables

    with store._migration_write_transaction() as connection:
        connection.execute(
            "INSERT INTO sample_versions (version_id, tenant_id, client_id, article_id, status, snapshot_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("v1", "tenant-001", "adis-sports", "article-1", "approved", "{}", "now", "now"),
        )
    reopened = OpsStore(path)
    with reopened._migration_connection() as connection:
        assert connection.execute("SELECT version_id FROM sample_versions").fetchone()[0] == "v1"


def test_seed_import_is_one_time_and_sqlite_authoritative(tmp_path: Path) -> None:
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"sample_versions": [{
        "version_id": "v1", "tenant_id": "tenant-001", "client_id": "adis-sports",
        "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now",
    }]}), encoding="utf-8")
    store = OpsStore(tmp_path / "ops.db")
    assert store.import_seed_once(seed) == 1
    seed.write_text(json.dumps({"sample_versions": [{"version_id": "v2"}]}), encoding="utf-8")
    assert store.import_seed_once(seed) == 0
    with store._migration_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM sample_versions").fetchone()[0] == 1


def test_seed_unknown_root_field_is_atomic_and_retryable(tmp_path: Path) -> None:
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"sample_versions": [], "unexpected": True}), encoding="utf-8")
    store = OpsStore(tmp_path / "ops.db")
    with pytest.raises(SnapshotError, match="unknown field"):
        store.import_seed_once(seed)
    with store._migration_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM sample_versions").fetchone()[0] == 0
    seed.write_text(json.dumps({"sample_versions": [{
        "version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
        "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now",
    }]}), encoding="utf-8")
    assert store.import_seed_once(seed) == 1


def test_live_sample_reads_use_sqlite_after_source_changes(tmp_path: Path) -> None:
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"sample_versions": [{
        "version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
        "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now",
    }]}), encoding="utf-8")
    store = OpsStore(tmp_path / "ops.db")
    assert store.import_seed_once(seed) == 1
    seed.write_text(json.dumps({"sample_versions": [{
        "version_id": "v2", "tenant_id": "tenant-001", "client_id": "wrong",
        "article_id": "changed", "status": "draft", "created_at": "later",
    }]}), encoding="utf-8")
    app = FastAPI()
    app.include_router(create_api_router(store=store))
    app.dependency_overrides[session_context] = lambda: SessionContext(
        "actor-1", "tenant-001", None, "admin"
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/sampling-spec-rnd/sample-versions/all",
            params={"tenant_id": "tenant-001"},
        )
    assert response.status_code == 200
    assert [row["version_id"] for row in response.json()["data"]] == ["v1"]


def test_production_app_factory_restart_derives_revision_lineage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.main import create_app

    db_path = tmp_path / "production.db"
    monkeypatch.setenv("OPS_DB_PATH", str(db_path))
    first = create_app(str(db_path))
    first.dependency_overrides[session_context] = lambda: SessionContext(
        "actor-1", "tenant-001", None, "admin"
    )
    with TestClient(first) as client:
        created = client.post("/api/sampling-spec-rnd/sample-versions/create", params={
            "article_id": "article-1", "article_name": "Article",
        })
        assert created.status_code == 200
        assert created.json()["version_label"] == "v1"

    second = create_app(str(db_path))
    second.dependency_overrides[session_context] = lambda: SessionContext(
        "actor-1", "tenant-001", None, "admin"
    )
    with TestClient(second) as client:
        created = client.post("/api/sampling-spec-rnd/sample-versions/create", params={
            "article_id": "article-1", "article_name": "Article",
        })
        assert created.status_code == 200
        assert created.json()["version_label"] == "v2"
        history = client.get("/api/sampling-spec-rnd/sample-versions/article/article-1/history")
        assert [row["version_label"] for row in history.json()["versions"]] == ["v1", "v2"]
        assert history.json()["versions"][1]["parent_version_id"] == history.json()["versions"][0]["version_id"]


def test_append_only_approvals_immutable_snapshots_and_foreign_keys(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "ops.db")
    with store._migration_write_transaction() as connection:
        connection.execute(
            "INSERT INTO sample_versions (version_id, tenant_id, client_id, article_id, status, snapshot_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("v1", "tenant-001", "client-001", "article-1", "approved", "{}", "now", "now"),
        )
        connection.execute(
            "INSERT INTO approvals VALUES (?, ?, ?, ?, ?, ?)",
            ("a1", "v1", "sample", "actor", "accepted", "now"),
        )
        connection.execute(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("o1", "tenant-001", "client-001", "v1", "ORD-1", 1, "line", None, "", "accepted", "{\"v\":1}", "now",),
        )
    with store._migration_connection() as connection:
        with pytest.raises(Exception, match="append-only"):
            connection.execute("UPDATE approvals SET note = 'changed' WHERE approval_id = 'a1'")
        with pytest.raises(Exception, match="append-only"):
            connection.execute("DELETE FROM approvals WHERE approval_id = 'a1'")
        with pytest.raises(Exception, match="immutable"):
            connection.execute("UPDATE orders SET accepted_snapshot_json = '{}' WHERE order_id = 'o1'")
        with pytest.raises(Exception):
            connection.execute(
                "INSERT INTO approvals VALUES (?, ?, ?, ?, ?, ?)",
                ("missing", "no-version", "sample", "actor", "", "now"),
            )
        assert connection.execute("SELECT COUNT(*) FROM approvals").fetchone()[0] == 1


def test_session_context_requires_missing_and_expired_auth() -> None:
    with pytest.raises(HTTPException) as missing:
        session_context(None)
    assert missing.value.status_code == 401

    auth = AuthStore()
    user = auth.seed_user(email="client@example.test", password="Pass12345", employee_id="c1",
                          full_name="Client", role="client", client_id="adis-sports")
    token, _ = auth.create_session(user.user_id, 0)
    with pytest.raises(HTTPException) as expired:
        session_context(f"Bearer {token}")
    assert expired.value.status_code == 401


def test_session_context_exposes_scope_and_unmapped_client_is_denied() -> None:
    auth = AuthStore()
    mapped = auth.seed_user(email="mapped@example.test", password="Pass12345", employee_id="mapped",
                            full_name="Mapped", role="client", client_id="adis-sports")
    token, _ = auth.create_session(mapped.user_id, 60)
    original = __import__("src.api.auth_deps", fromlist=["get_store"]).get_store
    try:
        import src.api.auth_deps as deps
        deps.get_store = lambda: auth
        with pytest.raises(HTTPException) as denied:
            session_context(f"Bearer {token}")
        assert denied.value.status_code == 403
        unmapped = auth.seed_user(email="unmapped@example.test", password="Pass12345", employee_id="unmapped",
                                  full_name="Unmapped", role="client")
        assert unmapped.client_id is None
    finally:
        deps.get_store = original


def test_direct_gateway_rejects_wrong_client_and_lineages_are_independent(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "scope.db")

    def snapshot(version_id: str, client_id: str | None) -> dict[str, object]:
        return {"version_id": version_id, "tenant_id": "tenant-001", "client_id": client_id,
                "article_id": "article-1", "article_name": "Article", "status": "draft",
                "created_by": "actor", "created_at": version_id, "updated_at": version_id,
                "revision_log": [], "components": [], "materials": []}

    a1 = store.create_sample_version(snapshot("a1", "client-a"), OpsStore._issue_scope("tenant-001", "client-a", "actor", "client"))
    b1 = store.create_sample_version(snapshot("b1", "client-b"), OpsStore._issue_scope("tenant-001", "client-b", "actor", "client"))
    assert (a1["version_label"], b1["version_label"]) == ("v1", "v1")
    assert store.update_sample_version(a1["version_id"], OpsStore._issue_scope("tenant-001", "client-b", "actor", "client"), {**a1, "status": "approved"}, expected_etag=0) is None
    assert store.get_sample_version(a1["version_id"], OpsStore._issue_scope("tenant-001", "client-a", "actor", "client"))["status"] == "draft"

    restarted = OpsStore(tmp_path / "scope.db")
    a2 = restarted.create_sample_revision(a1["version_id"], OpsStore._issue_scope("tenant-001", "client-a", "actor", "client"), snapshot("a2", "client-a"))
    b2 = restarted.create_sample_revision(b1["version_id"], OpsStore._issue_scope("tenant-001", "client-b", "actor", "client"), snapshot("b2", "client-b"))
    assert (a2["version_label"], b2["version_label"]) == ("v2", "v2")
    assert a2["parent_version_id"] == a1["version_id"] and b2["parent_version_id"] == b1["version_id"]


def test_update_compare_and_set_allows_one_concurrent_approval(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "cas.db")
    base = store.create_sample_version({"version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
        "article_id": "article-1", "status": "pending_approval", "created_at": "now", "updated_at": "now"}, OpsStore._issue_scope("tenant-001", None, "actor", "staff"))
    results: list[dict[str, object] | None] = []
    barrier = threading.Barrier(2)

    def approve(actor: str) -> None:
        barrier.wait()
        results.append(store.update_sample_version(base["version_id"], OpsStore._issue_scope("tenant-001", None, actor, "staff"), {**base, "status": "approved", "updated_at": actor}, expected_etag=0, approval=("sample", actor, "ok")))

    threads = [threading.Thread(target=approve, args=(actor,)) for actor in ("a", "b")]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert sum(result is not None for result in results) == 1
    with store._migration_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM approvals").fetchone()[0] == 1


def test_sampling_routes_are_protected_except_health(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(create_api_router(store=OpsStore(tmp_path / "route-auth.db")))
    paths = app.openapi()["paths"]
    sampling_paths = [path for path in paths if path.startswith("/api/sampling-spec-rnd/")]
    assert sampling_paths
    with TestClient(app) as client:
        for path in sampling_paths:
            if path.endswith("/health"):
                assert client.get(path).status_code == 200
            else:
                concrete_path = path.replace("{", "missing-").replace("}", "")
                method = next(iter(paths[path])).upper()
                assert client.request(method, concrete_path).status_code == 401


def test_store_requires_explicit_scope_and_rejects_conflicting_scope(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "scope-required.db")
    with pytest.raises(TypeError, match="server-authorized"):
        store.list_sample_versions(None)
    with pytest.raises(TypeError, match="server-authorized"):
        StoreScope("tenant-001", "client-a", True, "actor", "staff")
    assert not hasattr(StoreScope, "issued")
    assert not hasattr(store, "connect")
    assert not hasattr(store, "connection")
    assert not hasattr(store, "write_transaction")


def test_invalid_seed_batch_is_rejected_without_partial_rows_and_can_retry(tmp_path: Path) -> None:
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"sample_versions": [
        {"version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
         "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now"},
        {"version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
         "article_id": "article-2", "status": "draft", "created_at": "now", "updated_at": "now"},
    ]}), encoding="utf-8")
    store = OpsStore(tmp_path / "ops.db")
    with pytest.raises(SnapshotError, match="unique"):
        store.import_seed_once(seed)
    with store._migration_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM sample_versions").fetchone()[0] == 0
    seed.write_text(json.dumps({"sample_versions": [{
        "version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
        "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now",
    }]}), encoding="utf-8")
    assert store.import_seed_once(seed) == 1


def test_forged_identity_and_malformed_persisted_snapshot_do_not_mutate_valid_row(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "snapshot-integrity.db")
    scope = OpsStore._issue_scope("tenant-001", None, "actor", "staff")
    base = store.create_sample_version({
        "version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
        "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now",
    }, scope)
    with pytest.raises(SnapshotError, match="Immutable"):
        store.update_sample_version(base["version_id"], scope, {**base, "tenant_id": "other"}, expected_etag=0)
    assert store.get_sample_version(base["version_id"], scope)["status"] == "draft"
    with store._migration_write_transaction() as connection:
        connection.execute("UPDATE sample_versions SET snapshot_json = ? WHERE version_id = ?", ("[broken]", base["version_id"]))
    with pytest.raises(SnapshotError, match="malformed"):
        store.get_sample_version(base["version_id"], scope)


def test_concurrent_draft_edits_use_persisted_etag(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "draft-cas.db")
    scope = OpsStore._issue_scope("tenant-001", None, "actor", "staff")
    base = store.create_sample_version({
        "version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
        "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now",
        "components": [], "materials": [],
    }, scope)
    results: list[dict[str, object] | None] = []
    barrier = threading.Barrier(2)

    def edit(name: str) -> None:
        barrier.wait()
        results.append(store.update_sample_version(base["version_id"], scope, {**base, "components": [{"name": name}]}, expected_etag=0))

    threads = [threading.Thread(target=edit, args=(name,)) for name in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sum(result is not None for result in results) == 1
    assert store.get_sample_version(base["version_id"], scope)["etag"] == 1


def test_snapshot_validation_rejects_missing_unknown_nested_and_numeric_values(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "validation.db")
    scope = OpsStore._issue_scope("tenant-001", None, "actor", "staff")
    with pytest.raises(SnapshotError, match="missing required"):
        store.create_sample_version({"article_id": "article-1", "status": "draft", "created_at": "now"}, scope)
    valid = {"article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now"}
    with pytest.raises(SnapshotError, match="unknown"):
        store.create_sample_version({**valid, "unexpected": True}, scope)
    with pytest.raises(SnapshotError, match="entries"):
        store.create_sample_version({**valid, "components": [None]}, scope)
    with pytest.raises(SnapshotError, match="finite"):
        store.create_sample_version({**valid, "materials": [{"unit_cost": True}]}, scope)


def test_material_validation_returns_422_without_mutating_snapshot(tmp_path: Path) -> None:
    app = FastAPI()
    store = OpsStore(tmp_path / "materials.db")
    app.include_router(create_api_router(store=store))
    app.dependency_overrides[session_context] = lambda: SessionContext("actor", "tenant-001", None, "admin")
    with TestClient(app) as client:
        created = client.post("/api/sampling-spec-rnd/sample-versions/create", params={"article_id": "article-1", "article_name": "Article"})
        version_id = created.json()["version_id"]
        response = client.put(f"/api/sampling-spec-rnd/sample-versions/{version_id}/materials", json={"materials": [{"total_cost": "not-a-number"}]})
        assert response.status_code == 422
        snapshot = client.get(f"/api/sampling-spec-rnd/sample-versions/{version_id}").json()["data"]
        assert snapshot["materials"] == []


def test_revision_unknown_body_field_is_422_without_mutation_and_retryable(tmp_path: Path) -> None:
    app = FastAPI()
    store = OpsStore(tmp_path / "revision-body.db")
    app.include_router(create_api_router(store=store))
    app.dependency_overrides[session_context] = lambda: SessionContext("actor", "tenant-001", None, "admin")
    with TestClient(app) as client:
        created = client.post("/api/sampling-spec-rnd/sample-versions/create", params={"article_id": "article-1", "article_name": "Article"})
        version_id = created.json()["version_id"]
        before = client.get(f"/api/sampling-spec-rnd/sample-versions/{version_id}").json()["data"]
        rejected = client.post(f"/api/sampling-spec-rnd/sample-versions/{version_id}/new-revision", params={"revision_note": "retry"}, json={"unexpected": True})
        assert rejected.status_code == 422
        assert client.get(f"/api/sampling-spec-rnd/sample-versions/{version_id}").json()["data"] == before
        retry = client.post(f"/api/sampling-spec-rnd/sample-versions/{version_id}/new-revision", params={"revision_note": "retry"}, json={"components": [], "materials": []})
        assert retry.status_code == 200


def test_material_overflow_is_422_without_mutation_and_retryable(tmp_path: Path) -> None:
    app = FastAPI()
    store = OpsStore(tmp_path / "material-overflow.db")
    app.include_router(create_api_router(store=store))
    app.dependency_overrides[session_context] = lambda: SessionContext("actor", "tenant-001", None, "admin")
    with TestClient(app) as client:
        created = client.post("/api/sampling-spec-rnd/sample-versions/create", params={"article_id": "article-1", "article_name": "Article"})
        version_id = created.json()["version_id"]
        before = client.get(f"/api/sampling-spec-rnd/sample-versions/{version_id}").json()["data"]
        rejected = client.put(f"/api/sampling-spec-rnd/sample-versions/{version_id}/materials", json={"materials": [{"estimated_usage": 1e308, "unit_cost": 1e308}]})
        assert rejected.status_code == 422
        after = client.get(f"/api/sampling-spec-rnd/sample-versions/{version_id}").json()["data"]
        assert after == before
        retry = client.put(f"/api/sampling-spec-rnd/sample-versions/{version_id}/materials", json={"materials": [{"estimated_usage": 2, "unit_cost": 3}]})
        assert retry.status_code == 200
        assert retry.json()["estimated_total_cost"] == 6


def test_material_huge_integer_is_422_without_mutation_and_retryable(tmp_path: Path) -> None:
    from src.main import create_app

    app = create_app(str(tmp_path / "material-huge-integer.db"))
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"identifier": "ADMIN-IT", "password": "Admin#12345"})
        assert login.status_code == 200, login.text
        client.headers.update({"Authorization": f"Bearer {login.json()['accessToken']}"})
        created = client.post("/api/sampling-spec-rnd/sample-versions/create", params={"article_id": "article-1", "article_name": "Article"})
        assert created.status_code == 200, created.text
        version_id = created.json()["version_id"]
        before = client.get(f"/api/sampling-spec-rnd/sample-versions/{version_id}").json()["data"]
        rejected = client.put(
            f"/api/sampling-spec-rnd/sample-versions/{version_id}/materials",
            json={"materials": [{"estimated_usage": 10**4000, "unit_cost": 2, "total_cost": 10**4000}]},
        )
        assert rejected.status_code == 422
        after = client.get(f"/api/sampling-spec-rnd/sample-versions/{version_id}").json()["data"]
        assert after == before
        assert after["etag"] == before["etag"]
        assert after["revision_log"] == before["revision_log"]
        retry = client.put(
            f"/api/sampling-spec-rnd/sample-versions/{version_id}/materials",
            json={"materials": [{"estimated_usage": 2, "unit_cost": 3}]},
        )
        assert retry.status_code == 200
        assert retry.json()["estimated_total_cost"] == 6


def test_seed_huge_integer_is_atomic_and_retryable(tmp_path: Path) -> None:
    seed = tmp_path / "huge-seed.json"
    base = {"tenant_id": "tenant-001", "client_id": None, "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now"}
    seed.write_text(json.dumps({"sample_versions": [{**base, "version_id": "v1", "materials": [{"estimated_usage": 10**4000}]}]}), encoding="utf-8")
    store = OpsStore(tmp_path / "huge-seed.db")
    with pytest.raises(SnapshotError, match="integer is too large"):
        store.import_seed_once(seed)
    with store._migration_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM sample_versions").fetchone()[0] == 0
    seed.write_text(json.dumps({"sample_versions": [{**base, "version_id": "v1", "materials": [{"estimated_usage": 2, "unit_cost": 3, "total_cost": 6}]}]}), encoding="utf-8")
    assert store.import_seed_once(seed) == 1


def test_seed_type_and_batch_limits_are_atomic_and_retryable(tmp_path: Path) -> None:
    seed = tmp_path / "seed.json"
    base = {"tenant_id": "tenant-001", "client_id": None, "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now"}
    seed.write_text(json.dumps({"sample_versions": [{**base, "version_id": 1}]}), encoding="utf-8")
    store = OpsStore(tmp_path / "seed-limits.db")
    with pytest.raises(SnapshotError, match="version_id"):
        store.import_seed_once(seed)
    seed.write_text(json.dumps({"sample_versions": [{**base, "version_id": f"v{i}", "article_id": f"a{i}"} for i in range(201)]}), encoding="utf-8")
    with pytest.raises(SnapshotError, match="200-row"):
        store.import_seed_once(seed)
    with store._migration_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM sample_versions").fetchone()[0] == 0
    seed.write_text(json.dumps({"sample_versions": [{**base, "version_id": "v1"}]}), encoding="utf-8")
    assert store.import_seed_once(seed) == 1


def test_seed_document_limit_and_encoding_errors_are_stable_and_retryable(tmp_path: Path) -> None:
    seed = tmp_path / "bounded-seed.json"
    store = OpsStore(tmp_path / "bounded-seed.db")
    seed.write_bytes(b"{" + b" " * (5 * 1024 * 1024) + b"}")
    with pytest.raises(SnapshotError, match="5 MB"):
        store.import_seed_once(seed)
    seed.write_bytes(b"\xff\xfe")
    with pytest.raises(SnapshotError, match="malformed"):
        store.import_seed_once(seed)
    seed.write_text(json.dumps({"sample_versions": [{
        "version_id": "v1", "tenant_id": "tenant-001", "client_id": None,
        "article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now",
    }]}), encoding="utf-8")
    assert store.import_seed_once(seed) == 1


def test_nested_schema_rejects_null_wrong_type_boolean_and_nonfinite_values(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "nested.db")
    scope = OpsStore._issue_scope("tenant-001", None, "actor", "staff")
    base = {"article_id": "article-1", "status": "draft", "created_at": "now", "updated_at": "now"}
    invalid = [
        {"components": [{"part_name": None}]},
        {"components": [{"estimated_usage_m": True}]},
        {"components": [{"estimated_usage_m": "2"}]},
        {"materials": [{"unit_cost": float("inf")}]},
        {"revision_log": [{"action": 1}]},
        {"revision_log": [{"action": "created", "unexpected": "x"}]},
    ]
    for extra in invalid:
        with pytest.raises(SnapshotError):
            store.create_sample_version({**base, **extra}, scope)
    with store._migration_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM sample_versions").fetchone()[0] == 0


def test_create_body_rejects_unknown_fields_without_mutation(tmp_path: Path) -> None:
    app = FastAPI()
    store = OpsStore(tmp_path / "create-body.db")
    app.include_router(create_api_router(store=store))
    app.dependency_overrides[session_context] = lambda: SessionContext("actor", "tenant-001", None, "admin")
    with TestClient(app) as client:
        response = client.post(
            "/api/sampling-spec-rnd/sample-versions/create",
            params={"article_id": "article-1", "article_name": "Article"},
            json={"components": [], "untrusted": {"ignored": True}},
        )
        assert response.status_code == 422
        with store._migration_connection() as connection:
            assert connection.execute("SELECT COUNT(*) FROM sample_versions").fetchone()[0] == 0


def test_revision_preserves_requested_older_parent_after_newer_version_exists(tmp_path: Path) -> None:
    store = OpsStore(tmp_path / "lineage.db")
    scope = OpsStore._issue_scope("tenant-001", None, "actor", "staff")

    def version(article: str) -> dict[str, object]:
        return {"article_id": article, "status": "draft", "created_at": "now", "updated_at": "now", "components": [], "materials": [], "revision_log": []}

    first = store.create_sample_version(version("article-1"), scope)
    second = store.create_sample_revision(first["version_id"], scope, version("article-1"))
    branched = store.create_sample_revision(first["version_id"], scope, version("article-1"))
    assert second["parent_version_id"] == first["version_id"]
    assert branched["parent_version_id"] == first["version_id"]
    assert store.get_sample_version(branched["version_id"], scope)["parent_version_id"] == first["version_id"]



