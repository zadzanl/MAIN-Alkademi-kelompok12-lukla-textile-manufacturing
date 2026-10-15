"""In-memory idempotency cache.

Mencerminkan semantik yang dispesifikasikan:
- `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml`
  (`Problem.code = IDEMPOTENCY_CONFLICT`, header `Idempotency-Key` wajib).
- `openspec/changes/lukla-ops-engine-planning/11-database-schema-spec.md` §5
  (`same-hash replay, different-hash conflict`).

Prototype only: tidak ada cryptographic signature verification; cukup SHA-256
atas canonical JSON encoding seperti didefinisikan spec.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Dict, Optional, Tuple


class IdempotencyConflictError(Exception):
    """Dipakai bila key dipakai ulang dengan canonical-payload yang berbeda."""

    def __init__(self, key: str):
        super().__init__(f"Idempotency-Key '{key}' reused with different canonical payload.")
        self.key = key


def canonical_hash(payload: Dict[str, Any]) -> str:
    """Sorted-keys JSON + UTF-8 + SHA-256. Cocok dengan spec §5."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class IdempotencyCache:
    def __init__(self) -> None:
        self._items: Dict[str, Tuple[str, Dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def lookup(self, key: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mengembalikan body yang tersimpan bila hash cocok.

        Raises IdempotencyConflictError bila key pernah dipakai dengan hash
        berbeda. Mengembalikan None bila belum ada entry.
        """
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            stored_hash, body = entry
            current_hash = canonical_hash(payload)
            if stored_hash != current_hash:
                raise IdempotencyConflictError(key)
            return body

    def store(self, key: str, payload: Dict[str, Any], body: Dict[str, Any]) -> None:
        with self._lock:
            self._items[key] = (canonical_hash(payload), body)
