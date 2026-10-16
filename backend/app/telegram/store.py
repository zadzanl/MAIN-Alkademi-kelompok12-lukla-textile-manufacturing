"""
Persistence boundary for Telegram Copilot Bot bindings, single-use enrollment codes,
processed `update_id` idempotency records, and bounded per-chat conversation history.

Ceiling: Uses a deterministic SQLite / in-memory store by default for zero-dependency test
and local execution, while pairing with `backend/migrations/013_telegram_copilot_bindings.sql`
for PostgreSQL deployments. Set `TELEGRAM_STORE_SQLITE_PATH` to a file path to persist across
process restarts in local/staging environments without PostgreSQL.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from ..copilot.schemas import ChatMessage
from .schemas import TelegramBinding
from .security import generate_enrollment_code, hash_enrollment_code


MAX_ENROLLMENT_ATTEMPTS = 5
MAX_CHAT_HISTORY_MESSAGES = 6


@dataclass
class EnrollmentCodeRecord:
    code_hash: str
    role: str
    actor_id: uuid.UUID
    tenant_id: uuid.UUID
    legal_owner_id: Optional[uuid.UUID]
    expires_at: datetime
    consumed_at: Optional[datetime] = None
    consumed_by_chat_id: Optional[str] = None
    attempts: int = 0


class TelegramStore:
    """
    Thread-safe SQLite-backed store (supports `:memory:` or file path) enforcing:
    - Single-use, short-lived, hashed enrollment codes (`code_hash` primary key)
    - Persistent `chat_id` -> `(actor_id, tenant_id, roles, active)` bindings
    - Atomic `update_id` claiming to prevent duplicate inference on webhook retries
    """

    def __init__(self, sqlite_path: Optional[str] = None) -> None:
        self._sqlite_path = sqlite_path or os.getenv("TELEGRAM_STORE_SQLITE_PATH", ":memory:")
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self._sqlite_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS telegram_enrollment_codes (
                    code_hash TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    legal_owner_id TEXT NULL,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT NULL,
                    consumed_by_chat_id TEXT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS telegram_bindings (
                    telegram_chat_id TEXT PRIMARY KEY,
                    actor_id TEXT NOT NULL,
                    tenant_id TEXT NOT NULL,
                    roles_json TEXT NOT NULL,
                    legal_owner_id TEXT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT NULL
                );

                CREATE TABLE IF NOT EXISTS telegram_processed_updates (
                    update_id INTEGER PRIMARY KEY,
                    telegram_chat_id TEXT NULL,
                    status TEXT NOT NULL,
                    processed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS telegram_chat_failed_attempts (
                    telegram_chat_id TEXT PRIMARY KEY,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS telegram_chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def reset(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(
                """
                DELETE FROM telegram_enrollment_codes;
                DELETE FROM telegram_bindings;
                DELETE FROM telegram_processed_updates;
                DELETE FROM telegram_chat_failed_attempts;
                DELETE FROM telegram_chat_history;
                """
            )

    def claim_update_id(self, update_id: int, chat_id: Optional[str] = None) -> bool:
        """
        Atomically claim `update_id`. Returns True if this is the first time seeing `update_id`,
        or False if it was already processed/claimed.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        """
                        INSERT INTO telegram_processed_updates (update_id, telegram_chat_id, status, processed_at)
                        VALUES (?, ?, 'CLAIMED', ?)
                        """,
                        (int(update_id), str(chat_id) if chat_id is not None else None, now_iso),
                    )
                return True
            except sqlite3.IntegrityError:
                return False

    def create_enrollment_code(
        self,
        role: str,
        actor_id: uuid.UUID,
        tenant_id: uuid.UUID,
        legal_owner_id: Optional[uuid.UUID] = None,
        expires_in_seconds: int = 900,
    ) -> tuple[str, datetime]:
        raw_code = generate_enrollment_code()
        code_hash = hash_enrollment_code(raw_code)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=expires_in_seconds)

        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO telegram_enrollment_codes (
                    code_hash, role, actor_id, tenant_id, legal_owner_id, expires_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code_hash,
                    role,
                    str(actor_id),
                    str(tenant_id),
                    str(legal_owner_id) if legal_owner_id else None,
                    expires_at.isoformat(),
                    now.isoformat(),
                ),
            )
        return raw_code, expires_at

    def consume_enrollment_code(self, raw_code: str, chat_id: str | int) -> Optional[TelegramBinding]:
        """
        Validate and consume a one-time enrollment code for `chat_id`.
        Returns the created `TelegramBinding` on success, or `None` if the code is invalid,
        expired, already consumed, chat is rate-limited on failed attempts, or chat already has
        an active binding (re-enrollment requires explicit admin revocation first).
        """
        chat_id_str = str(chat_id)
        if not raw_code or len(raw_code.strip()) < 6 or len(raw_code.strip()) > 128:
            self._record_failed_attempt(chat_id_str)
            return None

        with self._lock:
            if self._get_failed_attempts(chat_id_str) >= MAX_ENROLLMENT_ATTEMPTS:
                return None

            # Do not silently overwrite an already-active binding without explicit admin revocation
            existing = self.resolve_active_binding(chat_id_str)
            if existing is not None:
                return None

            code_hash = hash_enrollment_code(raw_code.strip())
            row = self._conn.execute(
                "SELECT * FROM telegram_enrollment_codes WHERE code_hash = ?",
                (code_hash,),
            ).fetchone()

            if row is None:
                self._record_failed_attempt(chat_id_str)
                return None

            if row["consumed_at"] is not None:
                self._record_failed_attempt(chat_id_str)
                return None

            now = datetime.now(timezone.utc)
            expires_at = datetime.fromisoformat(row["expires_at"])
            if now >= expires_at:
                self._record_failed_attempt(chat_id_str)
                return None

            now_iso = now.isoformat()
            roles = [row["role"]]
            with self._conn:
                self._conn.execute(
                    """
                    UPDATE telegram_enrollment_codes
                    SET consumed_at = ?, consumed_by_chat_id = ?
                    WHERE code_hash = ? AND consumed_at IS NULL
                    """,
                    (now_iso, chat_id_str, code_hash),
                )
                self._conn.execute(
                    """
                    INSERT INTO telegram_bindings (
                        telegram_chat_id, actor_id, tenant_id, roles_json, legal_owner_id, active, created_at, revoked_at
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, NULL)
                    ON CONFLICT(telegram_chat_id) DO UPDATE SET
                        actor_id = excluded.actor_id,
                        tenant_id = excluded.tenant_id,
                        roles_json = excluded.roles_json,
                        legal_owner_id = excluded.legal_owner_id,
                        active = 1,
                        created_at = excluded.created_at,
                        revoked_at = NULL
                    """,
                    (
                        chat_id_str,
                        row["actor_id"],
                        row["tenant_id"],
                        json.dumps(roles),
                        row["legal_owner_id"],
                        now_iso,
                    ),
                )
                self._conn.execute(
                    "DELETE FROM telegram_chat_failed_attempts WHERE telegram_chat_id = ?",
                    (chat_id_str,),
                )

            return TelegramBinding(
                telegram_chat_id=chat_id_str,
                actor_id=uuid.UUID(row["actor_id"]),
                tenant_id=uuid.UUID(row["tenant_id"]),
                roles=roles,
                legal_owner_id=uuid.UUID(row["legal_owner_id"]) if row["legal_owner_id"] else None,
                active=True,
                created_at=now,
                revoked_at=None,
            )

    def resolve_active_binding(self, chat_id: str | int) -> Optional[TelegramBinding]:
        chat_id_str = str(chat_id)
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM telegram_bindings WHERE telegram_chat_id = ? AND active = 1",
                (chat_id_str,),
            ).fetchone()
            if row is None:
                return None
            return TelegramBinding(
                telegram_chat_id=row["telegram_chat_id"],
                actor_id=uuid.UUID(row["actor_id"]),
                tenant_id=uuid.UUID(row["tenant_id"]),
                roles=json.loads(row["roles_json"]),
                legal_owner_id=uuid.UUID(row["legal_owner_id"]) if row["legal_owner_id"] else None,
                active=bool(row["active"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                revoked_at=datetime.fromisoformat(row["revoked_at"]) if row["revoked_at"] else None,
            )

    def revoke_binding(self, chat_id: str | int) -> datetime:
        chat_id_str = str(chat_id)
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE telegram_bindings
                SET active = 0, revoked_at = ?
                WHERE telegram_chat_id = ?
                """,
                (now_iso, chat_id_str),
            )
            self._conn.execute(
                "DELETE FROM telegram_chat_history WHERE telegram_chat_id = ?",
                (chat_id_str,),
            )
        return now

    def get_recent_history(self, chat_id: str | int) -> List[ChatMessage]:
        chat_id_str = str(chat_id)
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT role, content FROM telegram_chat_history
                WHERE telegram_chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id_str, MAX_CHAT_HISTORY_MESSAGES),
            ).fetchall()
        return [ChatMessage(role=r["role"], content=r["content"]) for r in reversed(rows)]

    def append_history_turn(self, chat_id: str | int, user_message: str, assistant_reply: str) -> None:
        chat_id_str = str(chat_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO telegram_chat_history (telegram_chat_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
                (chat_id_str, user_message, now_iso),
            )
            self._conn.execute(
                "INSERT INTO telegram_chat_history (telegram_chat_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
                (chat_id_str, assistant_reply, now_iso),
            )

    def _get_failed_attempts(self, chat_id_str: str) -> int:
        row = self._conn.execute(
            "SELECT failed_count FROM telegram_chat_failed_attempts WHERE telegram_chat_id = ?",
            (chat_id_str,),
        ).fetchone()
        return int(row["failed_count"]) if row else 0

    def _record_failed_attempt(self, chat_id_str: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO telegram_chat_failed_attempts (telegram_chat_id, failed_count, updated_at)
                VALUES (?, 1, ?)
                ON CONFLICT(telegram_chat_id) DO UPDATE SET
                    failed_count = telegram_chat_failed_attempts.failed_count + 1,
                    updated_at = excluded.updated_at
                """,
                (chat_id_str, now_iso),
            )


telegram_store = TelegramStore()


def resolve_active_telegram_binding(chat_id: str | int) -> Optional[TelegramBinding]:
    return telegram_store.resolve_active_binding(chat_id)


def consume_enrollment_code(code: str, chat_id: str | int) -> Optional[TelegramBinding]:
    return telegram_store.consume_enrollment_code(code, chat_id)


def reset_telegram_store_for_tests() -> None:
    telegram_store.reset()
