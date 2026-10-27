"""Durable single-server SQLite gateway for sampling records."""
from __future__ import annotations
import json
import math
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS sample_versions (
 version_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, client_id TEXT, article_id TEXT,
 status TEXT NOT NULL, snapshot_json TEXT NOT NULL, created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL, etag INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS approvals (approval_id TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES sample_versions(version_id), approval_type TEXT NOT NULL, actor_id TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, client_id TEXT NOT NULL, version_id TEXT NOT NULL REFERENCES sample_versions(version_id), order_number TEXT NOT NULL, quantity INTEGER NOT NULL, production_line TEXT NOT NULL, target_delivery_date TEXT, notes TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, accepted_snapshot_json TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(tenant_id, order_number));
CREATE TABLE IF NOT EXISTS order_confirmations (confirmation_id TEXT PRIMARY KEY, order_id TEXT NOT NULL UNIQUE REFERENCES orders(order_id), actor_id TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_events (event_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, actor_id TEXT NOT NULL, event_type TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS idempotency_records (idempotency_key TEXT PRIMARY KEY, actor_id TEXT NOT NULL, operation TEXT NOT NULL, payload_hash TEXT NOT NULL, response_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_sample_versions_scope ON sample_versions(tenant_id, client_id);
CREATE INDEX IF NOT EXISTS idx_approvals_version ON approvals(version_id);
CREATE TRIGGER IF NOT EXISTS approvals_append_only_update BEFORE UPDATE ON approvals BEGIN SELECT RAISE(ABORT, 'approvals are append-only'); END;
CREATE TRIGGER IF NOT EXISTS approvals_append_only_delete BEFORE DELETE ON approvals BEGIN SELECT RAISE(ABORT, 'approvals are append-only'); END;
CREATE TRIGGER IF NOT EXISTS orders_snapshot_immutable BEFORE UPDATE OF accepted_snapshot_json ON orders WHEN NEW.accepted_snapshot_json IS NOT OLD.accepted_snapshot_json BEGIN SELECT RAISE(ABORT, 'accepted snapshots are immutable'); END;
"""

@dataclass(frozen=True)
class StoreScope:
    tenant_id: str
    client_id: str | None
    tenant_wide: bool
    actor_id: str
    role: str
    _issued: object = None

    def __post_init__(self) -> None:
        if self._issued is not _SCOPE_CAPABILITY:
            raise TypeError("server-authorized scope is required")
        if self.tenant_wide != (self.client_id is None):
            raise ValueError("scope has conflicting tenant-wide and client values")

class SnapshotError(ValueError):
    pass


SEED_DOCUMENT_MAX_BYTES = 5 * 1024 * 1024
MAX_INTEGER_MAGNITUDE = 10**308


_SCOPE_CAPABILITY = object()

class OpsStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._migration_connection() as c:
            c.executescript(SCHEMA)
            columns = {r[1] for r in c.execute("PRAGMA table_info(sample_versions)")}
            if "etag" not in columns:
                c.execute("ALTER TABLE sample_versions ADD COLUMN etag INTEGER NOT NULL DEFAULT 0")

    @classmethod
    def _issue_scope(cls, tenant_id: str, client_id: str | None, actor_id: str, role: str) -> StoreScope:
        return StoreScope(tenant_id, client_id, client_id is None, actor_id, role, _SCOPE_CAPABILITY)

    def _connect(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, timeout=5.0, isolation_level=None, check_same_thread=False)
        c.row_factory = sqlite3.Row; c.execute("PRAGMA foreign_keys = ON"); c.execute("PRAGMA busy_timeout = 5000")
        if str(c.execute("PRAGMA journal_mode = WAL").fetchone()[0]).lower() != "wal":
            c.close(); raise RuntimeError(f"SQLite WAL unavailable for {self.path}")
        return c

    @contextmanager
    def _migration_connection(self) -> Iterator[sqlite3.Connection]:
        c = self._connect()
        try: yield c
        finally: c.close()

    @contextmanager
    def _migration_write_transaction(self) -> Iterator[sqlite3.Connection]:
        with self._migration_connection() as c:
            c.execute("BEGIN IMMEDIATE")
            try: yield c
            except Exception: c.rollback(); raise
            else: c.commit()

    @staticmethod
    def _scope(scope: StoreScope) -> tuple[str, tuple[object, ...]]:
        if not isinstance(scope, StoreScope) or scope._issued is not _SCOPE_CAPABILITY:
            raise TypeError("server-authorized scope is required")
        if scope.tenant_wide: return "client_id IS NULL", ()
        if not scope.client_id: raise ValueError("client scope requires client_id")
        return "client_id = ?", (scope.client_id,)

    @staticmethod
    def _decode(raw: str) -> dict[str, object]:
        try: value = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc: raise SnapshotError("Stored sample snapshot is malformed") from exc
        if not isinstance(value, dict): raise SnapshotError("Stored sample snapshot must be an object")
        OpsStore._validate_payload(value, persisted=True)
        required = ("version_id", "tenant_id", "client_id", "article_id", "status", "created_at", "updated_at")
        if any(key not in value for key in required): raise SnapshotError("Stored sample snapshot is incomplete")
        return value

    @staticmethod
    def _validate_payload(payload: dict[str, object], *, persisted: bool = False, require_snapshot: bool = False) -> None:
        allowed = {"version_id", "tenant_id", "client_id", "article_id", "article_name", "status", "version_number", "version_label", "parent_version_id", "created_by", "created_at", "updated_at", "approved_by", "approved_at", "converted_to_order_id", "notes", "components", "materials", "revision_log", "etag"}
        component_allowed = {"name", "component_id", "part_name", "description", "material_type", "estimated_usage_m", "unit", "sewing_time_std_ms", "rate_card_idr", "notes"}
        material_allowed = {"material_code", "material_name", "estimated_usage", "unit", "unit_cost", "total_cost", "supplier_id", "notes"}
        revision_allowed = {"action", "by", "at", "note"}
        required = {"version_id", "tenant_id", "client_id", "article_id", "status", "created_at", "updated_at"}
        if not isinstance(payload, dict): raise SnapshotError("Request body must be a bounded object")
        if require_snapshot and not persisted:
            missing = {"article_id", "status", "created_at", "updated_at"} - payload.keys()
            if missing: raise SnapshotError(f"Snapshot is missing required field: {sorted(missing)[0]}")
        if persisted:
            missing = required - payload.keys()
            if missing: raise SnapshotError(f"Snapshot is missing required field: {sorted(missing)[0]}")
        if not isinstance(payload, dict) or any(key not in allowed for key in payload):
            raise SnapshotError("Snapshot contains an unknown field")
        def walk(value: object, depth: int = 0) -> None:
            if depth > 6: raise SnapshotError("Snapshot nesting is too deep")
            if isinstance(value, bool) or value is None or isinstance(value, str):
                if isinstance(value, str) and len(value) > 4096: raise SnapshotError("Snapshot string is too large")
                return
            if isinstance(value, (int, float)):
                if isinstance(value, bool) or (isinstance(value, float) and not math.isfinite(value)): raise SnapshotError("Snapshot numbers must be finite and non-boolean")
                if isinstance(value, int) and abs(value) > MAX_INTEGER_MAGNITUDE: raise SnapshotError("Snapshot integer is too large")
                return
            if isinstance(value, list):
                if len(value) > 200: raise SnapshotError("Snapshot list is too large")
                for item in value: walk(item, depth + 1)
                return
            if isinstance(value, dict):
                if len(value) > 32: raise SnapshotError("Snapshot object is too large")
                for key, item in value.items():
                    if not isinstance(key, str) or len(key) > 128: raise SnapshotError("Snapshot field name is invalid")
                    walk(item, depth + 1)
                return
            raise SnapshotError("Snapshot contains a non-JSON value")
        if not isinstance(payload, dict) or len(payload) > 32: raise SnapshotError("Request body must be a bounded object")
        walk(payload)
        for key in ("components", "materials", "revision_log"):
            if key in payload and not isinstance(payload[key], list): raise SnapshotError(f"{key} must be a bounded list")
        if "version_number" in payload and (isinstance(payload["version_number"], bool) or not isinstance(payload["version_number"], int)): raise SnapshotError("version_number must be an integer")
        for field in ("version_id", "tenant_id", "article_id", "status", "created_at", "updated_at"):
            if field in payload and (isinstance(payload[field], bool) or not isinstance(payload[field], str)):
                raise SnapshotError(f"{field} must be a string")
        if "client_id" in payload and payload["client_id"] is not None and (isinstance(payload["client_id"], bool) or not isinstance(payload["client_id"], str)):
            raise SnapshotError("client_id must be a string or null")
        for key, entry_allowed in (("components", component_allowed), ("materials", material_allowed), ("revision_log", revision_allowed)):
            for entry in payload.get(key, []):
                if not isinstance(entry, dict): raise SnapshotError(f"{key} entries must be objects")
                if any(field not in entry_allowed for field in entry): raise SnapshotError(f"{key} entry contains an unknown field")
        component_strings = {"name", "component_id", "part_name", "description", "material_type", "unit", "rate_card_id", "notes"}
        component_numbers = {"estimated_usage_m", "sewing_time_std_ms", "rate_card_idr"}
        material_strings = {"material_code", "material_name", "unit", "supplier_id", "notes"}
        material_numbers = {"estimated_usage", "unit_cost", "total_cost"}
        revision_strings = {"action", "by", "at", "note"}
        for key, string_fields, numeric_fields in (("components", component_strings, component_numbers), ("materials", material_strings, material_numbers), ("revision_log", revision_strings, set())):
            for entry in payload.get(key, []):
                for field in string_fields:
                    if field in entry and (entry[field] is None or isinstance(entry[field], bool) or not isinstance(entry[field], str)):
                        raise SnapshotError(f"{key}.{field} must be a string")
                for field in numeric_fields:
                    value = entry.get(field)
                    if field in entry and (value is None or isinstance(value, bool) or not isinstance(value, (int, float)) or (isinstance(value, float) and not math.isfinite(value))):
                        raise SnapshotError(f"{key}.{field} must be a finite number")
        for field in ("article_name", "version_label", "created_by", "notes"):
            if field in payload and (payload[field] is None or isinstance(payload[field], bool) or not isinstance(payload[field], str)):
                raise SnapshotError(f"{field} must be a string")
        for entry in payload.get("materials", []):
            for field in ("estimated_usage", "unit_cost", "total_cost"):
                if field in entry and (isinstance(entry[field], bool) or not isinstance(entry[field], (int, float)) or (isinstance(entry[field], float) and not math.isfinite(entry[field]))):
                    raise SnapshotError(f"materials.{field} must be a finite number")
            if "total_cost" in entry and "estimated_usage" in entry and "unit_cost" in entry:
                try:
                    expected = float(entry["estimated_usage"]) * float(entry["unit_cost"])
                    supplied = float(entry["total_cost"])
                except (TypeError, ValueError, OverflowError) as exc:
                    raise SnapshotError("materials.total_cost must be finite") from exc
                if not math.isfinite(expected) or not math.isfinite(supplied): raise SnapshotError("materials.total_cost must be finite")
                if entry["total_cost"] != 0 and not math.isclose(supplied, expected, rel_tol=1e-9, abs_tol=1e-9): raise SnapshotError("materials.total_cost does not match usage and unit cost")

    def import_seed_once(self, json_path: str | Path) -> int:
        with self._migration_write_transaction() as c:
            if c.execute("SELECT 1 FROM sample_versions LIMIT 1").fetchone(): return 0
            source = Path(json_path)
            if not source.exists(): return 0
            try:
                with source.open("rb") as handle:
                    raw = handle.read(SEED_DOCUMENT_MAX_BYTES + 1)
                if len(raw) > SEED_DOCUMENT_MAX_BYTES:
                    raise SnapshotError("Seed document exceeds the 5 MB limit")
                data = json.loads(raw.decode("utf-8"))
            except SnapshotError:
                raise
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
                raise SnapshotError("Seed document is malformed") from exc
            if not isinstance(data, dict):
                raise SnapshotError("Seed sample_versions must be a list")
            if set(data) != {"sample_versions"}:
                raise SnapshotError("Seed document contains an unknown field")
            if not isinstance(data.get("sample_versions"), list): raise SnapshotError("Seed sample_versions must be a list")
            if len(data["sample_versions"]) > 200: raise SnapshotError("Seed sample_versions exceeds the 200-row limit")
            rows = []
            seen: set[str] = set()
            for row in data["sample_versions"]:
                if not isinstance(row, dict): raise SnapshotError("Seed sample row is invalid")
                imported = dict(row)
                self._validate_payload(imported, persisted=True)
                self._decode(json.dumps(imported, sort_keys=True))
                version_id = imported["version_id"]
                if version_id in seen: raise SnapshotError("Seed sample IDs must be unique")
                seen.add(version_id); rows.append(imported)
            for imported in rows:
                c.execute("INSERT INTO sample_versions (version_id,tenant_id,client_id,article_id,status,snapshot_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)", (imported["version_id"], imported.get("tenant_id", ""), imported.get("client_id"), imported.get("article_id"), imported.get("status", "draft"), json.dumps(imported, sort_keys=True), imported.get("created_at", ""), imported["updated_at"]))
            return len(rows)

    def list_sample_versions(self, scope: StoreScope) -> list[dict[str, object]]:
        predicate, extra = self._scope(scope)
        with self._migration_connection() as c: rows = c.execute(f"SELECT snapshot_json, etag FROM sample_versions WHERE tenant_id = ? AND {predicate} ORDER BY created_at DESC", (scope.tenant_id, *extra)).fetchall()
        result = []
        for row in rows:
            value = self._decode(row[0]); value["etag"] = row[1]; result.append(value)
        return result

    def get_sample_version(self, version_id: str, scope: StoreScope) -> dict[str, object] | None:
        predicate, extra = self._scope(scope)
        with self._migration_connection() as c: row = c.execute(f"SELECT snapshot_json, etag FROM sample_versions WHERE version_id = ? AND tenant_id = ? AND {predicate}", (version_id, scope.tenant_id, *extra)).fetchone()
        if not row: return None
        value = self._decode(row[0]); value["etag"] = row[1]; return value

    def update_sample_version(self, version_id: str, scope: StoreScope, snapshot: dict[str, object], *, expected_etag: int, approval: tuple[str, str, str] | None = None) -> dict[str, object] | None:
        self._validate_payload(snapshot)
        predicate, extra = self._scope(scope)
        with self._migration_write_transaction() as c:
            row = c.execute(f"SELECT * FROM sample_versions WHERE version_id = ? AND tenant_id = ? AND {predicate}", (version_id, scope.tenant_id, *extra)).fetchone()
            if row is None: return None
            current = self._decode(row["snapshot_json"])
            immutable = ("version_id", "tenant_id", "client_id", "article_id", "version_number", "version_label", "parent_version_id")
            for key in immutable:
                if key in snapshot and snapshot.get(key) != current.get(key): raise SnapshotError(f"Immutable snapshot field mismatch: {key}")
            if row["etag"] != expected_etag: return None
            updated = dict(current); updated.update({k: v for k, v in snapshot.items() if k not in immutable and k != "etag"})
            new_etag = row["etag"] + 1; updated["etag"] = new_etag
            changed = c.execute(f"UPDATE sample_versions SET status=?, snapshot_json=?, updated_at=?, etag=? WHERE version_id=? AND tenant_id=? AND {predicate} AND etag=?", (updated["status"], json.dumps(updated, sort_keys=True), updated["updated_at"], new_etag, version_id, scope.tenant_id, *extra, expected_etag))
            if changed.rowcount != 1: return None
            if approval is not None: c.execute("INSERT INTO approvals VALUES (?, ?, ?, ?, ?, datetime('now'))", (str(uuid.uuid4()), version_id, approval[0], scope.actor_id, approval[2]))
        return updated

    def list_sample_history(self, scope: StoreScope, article_id: str) -> list[dict[str, object]]:
        predicate, extra = self._scope(scope)
        with self._migration_connection() as c: rows = c.execute(f"SELECT snapshot_json, etag FROM sample_versions WHERE tenant_id=? AND article_id=? AND {predicate} ORDER BY CAST(json_extract(snapshot_json, '$.version_number') AS INTEGER)", (scope.tenant_id, article_id, *extra)).fetchall()
        result=[]
        for row in rows:
            value=self._decode(row[0]); value["etag"]=row[1]; result.append(value)
        return result

    def create_sample_version(self, snapshot: dict[str, object], scope: StoreScope) -> dict[str, object]:
        self._scope(scope); self._validate_payload(snapshot, require_snapshot=True)
        if not isinstance(snapshot.get("article_id"), str) or not snapshot["article_id"]: raise SnapshotError("article_id is required")
        if "tenant_id" in snapshot and snapshot["tenant_id"] != scope.tenant_id: raise SnapshotError("Snapshot scope mismatch")
        if "client_id" in snapshot and snapshot["client_id"] != scope.client_id: raise SnapshotError("Snapshot scope mismatch")
        article_id = snapshot["article_id"]
        predicate, extra = self._scope(scope)
        with self._migration_write_transaction() as c:
            latest = c.execute(f"SELECT version_id, json_extract(snapshot_json, '$.version_number') AS n FROM sample_versions WHERE tenant_id=? AND article_id=? AND {predicate} ORDER BY n DESC LIMIT 1", (scope.tenant_id, article_id, *extra)).fetchone()
            number = int(latest["n"] or 0)+1 if latest else 1
            result={k: v for k, v in snapshot.items() if k not in {"version_id", "tenant_id", "client_id", "version_number", "version_label", "parent_version_id", "etag"}}
            result.update({"version_id": str(uuid.uuid4()), "tenant_id": scope.tenant_id, "client_id": scope.client_id, "article_id": article_id, "version_number":number,"version_label":f"v{number}","parent_version_id":latest["version_id"] if latest else None})
            c.execute("INSERT INTO sample_versions (version_id,tenant_id,client_id,article_id,status,snapshot_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)", (result["version_id"],scope.tenant_id,scope.client_id,article_id,result["status"],json.dumps(result,sort_keys=True),result["created_at"],result["updated_at"]))
        result["etag"]=0; return result

    def create_sample_revision(self, parent_id: str, scope: StoreScope, snapshot: dict[str, object]) -> dict[str, object] | None:
        self._scope(scope); self._validate_payload(snapshot)
        predicate, extra = self._scope(scope)
        with self._migration_write_transaction() as c:
            parent_row = c.execute(f"SELECT snapshot_json FROM sample_versions WHERE version_id=? AND tenant_id=? AND {predicate}", (parent_id, scope.tenant_id, *extra)).fetchone()
            if parent_row is None: return None
            parent = self._decode(parent_row[0])
            if any(k in snapshot and snapshot[k] != parent.get(k) for k in ("tenant_id", "client_id", "article_id")):
                raise SnapshotError("Revision identity mismatch")
            latest = c.execute(f"SELECT version_id, json_extract(snapshot_json, '$.version_number') AS n FROM sample_versions WHERE tenant_id=? AND article_id=? AND {predicate} ORDER BY n DESC LIMIT 1", (scope.tenant_id, parent["article_id"], *extra)).fetchone()
            number = int(latest["n"] or 0) + 1 if latest else 1
            result = {k: v for k, v in snapshot.items() if k not in {"version_id", "tenant_id", "client_id", "version_number", "version_label", "parent_version_id", "etag"}}
            result.update({"version_id": str(uuid.uuid4()), "tenant_id": scope.tenant_id, "client_id": scope.client_id, "article_id": parent["article_id"], "version_number": number, "version_label": f"v{number}", "parent_version_id": parent_id})
            c.execute("INSERT INTO sample_versions (version_id,tenant_id,client_id,article_id,status,snapshot_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)", (result["version_id"], scope.tenant_id, scope.client_id, result["article_id"], result["status"], json.dumps(result, sort_keys=True), result["created_at"], result["updated_at"]))
        result["etag"] = 0
        return result

