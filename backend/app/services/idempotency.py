import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from ..models.idempotency import IdempotencyRecord
from ..schemas.problem import ProblemException

def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize object to deterministic JSON according to RFC 8785 (sorted keys, no whitespace)."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str
    ).encode("utf-8")

def compute_canonical_hash(payload: Any) -> bytes:
    """Compute SHA-256 digest of RFC 8785 canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(payload)).digest()

def reserve_or_get_idempotency(
    db: Session,
    tenant_id: uuid.UUID,
    operation_id: str,
    key: str,
    payload_hash: bytes,
    instance: str = ""
) -> Tuple[bool, Optional[Tuple[int, Dict[str, Any]]]]:
    """
    Atomically reserve an idempotency key or retrieve the completed result.
    Uses PostgreSQL row-level locking via INSERT ... ON CONFLICT DO UPDATE.
    
    Returns:
        (is_new, cached_response)
        If is_new is True:
            The key has been reserved (status='PENDING'). Caller proceeds with execution.
        If is_new is False:
            The key already existed and completed.
            cached_response is (response_status, response_body). Caller returns this immediately.
    Raises:
        ProblemException(409) if the payload hash does not match (IDEMPOTENCY_CONFLICT).
        ProblemException(409) if another operation with this key is pending or in unexpected state.
    """
    stmt = text("""
        INSERT INTO idempotency_records (
            id, tenant_id, operation_id, key, canonical_payload_hash, status, created_at
        ) VALUES (
            gen_random_uuid(), :tenant_id, :operation_id, :key, :payload_hash, 'PENDING', now()
        )
        ON CONFLICT (tenant_id, operation_id, key) DO UPDATE
            SET status = idempotency_records.status
        RETURNING id, status, canonical_payload_hash, response_status, response_body, (xmax = 0) AS is_new_insert;
    """)

    result = db.execute(
        stmt,
        {
            "tenant_id": str(tenant_id),
            "operation_id": operation_id,
            "key": key,
            "payload_hash": payload_hash
        }
    ).fetchone()

    if result is None:
        raise ProblemException(
            status=500,
            code="VALIDATION_ERROR",
            detail="Failed to reserve idempotency key",
            instance=instance
        )

    rec_id, status, rec_hash, resp_status, resp_body, is_new_insert = result

    if is_new_insert:
        return (True, None)

    # Collision detected; check payload hash against existing record
    if bytes(rec_hash) != payload_hash:
        raise ProblemException(
            status=409,
            code="IDEMPOTENCY_CONFLICT",
            detail="Idempotency key conflict: the same key was used with a different canonical payload",
            instance=instance
        )

    if status == "COMPLETED" and resp_status is not None:
        return (False, (resp_status, resp_body or {}))

    if status == "PENDING":
        raise ProblemException(
            status=409,
            code="IDEMPOTENCY_CONFLICT",
            detail="Operation with this idempotency key is currently pending execution",
            instance=instance
        )

    raise ProblemException(
        status=409,
        code="IDEMPOTENCY_CONFLICT",
        detail=f"Idempotency record is in unexpected status '{status}'",
        instance=instance
    )

def complete_idempotency(
    db: Session,
    tenant_id: uuid.UUID,
    operation_id: str,
    key: str,
    response_status: int,
    response_body: Dict[str, Any]
) -> None:
    """Update reserved idempotency record to COMPLETED with response payload."""
    stmt = text("""
        UPDATE idempotency_records
        SET status = 'COMPLETED',
            response_status = :response_status,
            response_body = CAST(:response_body AS jsonb),
            completed_at = now()
        WHERE tenant_id = :tenant_id AND operation_id = :operation_id AND key = :key
    """)
    db.execute(
        stmt,
        {
            "tenant_id": str(tenant_id),
            "operation_id": operation_id,
            "key": key,
            "response_status": response_status,
            "response_body": json.dumps(response_body, default=str)
        }
    )

def check_idempotency(
    db: Session,
    tenant_id: uuid.UUID,
    operation_id: str,
    key: str,
    payload_hash: bytes,
    instance: str = ""
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """Legacy check_idempotency kept for backward compatibility."""
    record = db.execute(
        select(IdempotencyRecord).filter_by(
            tenant_id=tenant_id,
            operation_id=operation_id,
            key=key
        )
    ).scalar_one_or_none()

    if record is not None:
        if bytes(record.canonical_payload_hash) != payload_hash:
            raise ProblemException(
                status=409,
                code="IDEMPOTENCY_CONFLICT",
                detail="Idempotency key conflict: the same key was used with a different canonical payload",
                instance=instance
            )
        if record.status == "COMPLETED" and record.response_status is not None:
            return (record.response_status, record.response_body or {})
        elif record.status == "PENDING":
            raise ProblemException(
                status=409,
                code="IDEMPOTENCY_CONFLICT",
                detail="Operation with this idempotency key is currently pending execution",
                instance=instance
            )

    return None

def record_idempotency_completion(
    db: Session,
    tenant_id: uuid.UUID,
    operation_id: str,
    key: str,
    payload_hash: bytes,
    response_status: int,
    response_body: Dict[str, Any]
) -> None:
    """Legacy record_idempotency_completion."""
    complete_idempotency(
        db=db,
        tenant_id=tenant_id,
        operation_id=operation_id,
        key=key,
        response_status=response_status,
        response_body=response_body
    )
