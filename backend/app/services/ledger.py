import uuid
import json
import base64
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, text
from ..models.ledger import LedgerAccount, LedgerTransaction, LedgerEntry
from ..models.audit import AuditEvent
from ..core.auth import AuthContext
from ..schemas.ledger import (
    LedgerRequest, LedgerTransaction as LedgerTransactionSchema,
    LedgerEntry as LedgerEntrySchema, ReversalRequest, LedgerPage
)
from ..schemas.problem import ProblemException
from .idempotency import compute_canonical_hash, reserve_or_get_idempotency, complete_idempotency

def encode_cursor(posted_at_iso: str, tx_id: str) -> str:
    raw = f"{posted_at_iso}|{tx_id}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")

def decode_cursor(cursor_str: str) -> Tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8")).decode("utf-8")
        parts = raw.split("|", 1)
        if len(parts) != 2:
            raise ValueError("Invalid cursor format")
        posted_at = datetime.fromisoformat(parts[0])
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        tx_id = uuid.UUID(parts[1])
        return posted_at, tx_id
    except Exception as e:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail=f"Invalid pagination cursor: {str(e)}"
        )

def post_transaction(
    db: Session,
    auth_context: AuthContext,
    request: LedgerRequest,
    idempotency_key: str,
    request_id: uuid.UUID,
    instance: str = "/api/v1/ledger/transactions"
) -> LedgerTransactionSchema:
    """
    Append a balanced double-entry transaction atomically.
    Validates accounts, enforces zero-sum balance, records audit event,
    and guarantees RFC 8785 idempotency.
    """
    # 1. Pre-validation: Mathematical Balancing & Non-Empty Headers
    if len(request.entries) < 2:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail="Transaction must contain at least two entries",
            instance=instance
        )

    debit_count = sum(1 for e in request.entries if e.direction == "DEBIT")
    credit_count = sum(1 for e in request.entries if e.direction == "CREDIT")
    if debit_count < 1 or credit_count < 1:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail="Transaction must contain at least one DEBIT and at least one CREDIT entry",
            instance=instance
        )

    debit_total = sum(e.amountMinor for e in request.entries if e.direction == "DEBIT")
    credit_total = sum(e.amountMinor for e in request.entries if e.direction == "CREDIT")
    if debit_total != credit_total:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail=f"Transaction is unbalanced: debit total ({debit_total}) does not equal credit total ({credit_total})",
            instance=instance
        )

    # 2. Account Code Resolution & Currency Validation
    codes = list(set(e.accountCode for e in request.entries))
    accounts = db.execute(
        select(LedgerAccount).filter(
            LedgerAccount.tenant_id == auth_context.tenant_id,
            LedgerAccount.code.in_(codes)
        )
    ).scalars().all()

    acct_by_code = {a.code: a for a in accounts}

    for entry in request.entries:
        if entry.accountCode not in acct_by_code:
            raise ProblemException(
                status=400,
                code="VALIDATION_ERROR",
                detail=f"Unknown accountCode '{entry.accountCode}' for tenant",
                instance=instance
            )
        acct = acct_by_code[entry.accountCode]
        if not acct.active:
            raise ProblemException(
                status=400,
                code="VALIDATION_ERROR",
                detail=f"Account '{entry.accountCode}' is inactive",
                instance=instance
            )
        if acct.currency != request.currency:
            raise ProblemException(
                status=400,
                code="VALIDATION_ERROR",
                detail=f"Account '{entry.accountCode}' currency '{acct.currency}' does not match transaction currency '{request.currency}'",
                instance=instance
            )

    # 3. Reserve Idempotency Key Atomically
    payload_dict = request.model_dump(mode="json", by_alias=True)
    payload_hash = compute_canonical_hash(payload_dict)

    is_new, cached = reserve_or_get_idempotency(
        db,
        tenant_id=auth_context.tenant_id,
        operation_id="appendLedgerTransaction",
        key=idempotency_key,
        payload_hash=payload_hash,
        instance=instance
    )
    if not is_new:
        assert cached is not None
        status_code, body = cached
        return LedgerTransactionSchema.model_validate(body)

    # 4. Atomic Execution via Stored Procedure
    new_tx_id = uuid.uuid4()
    entries_json = [
        {
            "account_id": str(acct_by_code[e.accountCode].id),
            "direction": e.direction,
            "amount_minor": e.amountMinor,
            "currency": request.currency,
            "memo": f"Entry for {e.accountCode}"
        }
        for e in request.entries
    ]

    try:
        db.execute(
            text("""
                SELECT append_ledger_transaction(
                    :tx_id, :tenant_id, :tx_type, :currency, CAST(:entries AS jsonb), :posted_by, NULL, 'MANUAL', NULL
                )
            """),
            {
                "tx_id": str(new_tx_id),
                "tenant_id": str(auth_context.tenant_id),
                "tx_type": request.transactionType,
                "currency": request.currency,
                "entries": json.dumps(entries_json),
                "posted_by": str(auth_context.actor_id)
            }
        )

        # 5. Persist Audit Event
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            tenant_id=auth_context.tenant_id,
            actor_id=auth_context.actor_id,
            action="LEDGER_TRANSACTION_APPENDED",
            entity_type="ledger_transactions",
            entity_id=new_tx_id,
            request_id=request_id,
            payload=payload_dict,
            occurred_at=datetime.now(timezone.utc)
        )
        db.add(audit_event)

        # 6. Complete Idempotency Record
        result = LedgerTransactionSchema(
            id=new_tx_id,
            tenantId=auth_context.tenant_id,
            entries=request.entries,
            reversalOf=None
        )

        complete_idempotency(
            db=db,
            tenant_id=auth_context.tenant_id,
            operation_id="appendLedgerTransaction",
            key=idempotency_key,
            response_status=201,
            response_body=result.model_dump(mode="json", by_alias=True)
        )

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        err_msg = str(e)
        if "EMPTY_OR_ONE_SIDED_TRANSACTION" in err_msg or "TRANSACTION_UNBALANCED" in err_msg:
            raise ProblemException(
                status=400,
                code="VALIDATION_ERROR",
                detail="Transaction is unbalanced or missing required debit/credit entries",
                instance=instance
            )
        if "LATE_LINE_INSERTION_BLOCKED" in err_msg:
            raise ProblemException(
                status=409,
                code="LEDGER_IMMUTABLE",
                detail="Cannot append entries to a previously committed ledger transaction",
                instance=instance
            )
        if "LEDGER_IMMUTABLE" in err_msg:
            raise ProblemException(
                status=409,
                code="LEDGER_IMMUTABLE",
                detail="Ledger transactions and entries are strictly immutable and cannot be updated or deleted",
                instance=instance
            )
        if "chk_entry_amount_positive" in err_msg or "chk_entry_direction" in err_msg:
            raise ProblemException(
                status=400,
                code="VALIDATION_ERROR",
                detail="Entry amount must be positive and direction must be DEBIT or CREDIT",
                instance=instance
            )
        if "fk_ledger_entries_account" in err_msg or "fk_ledger_entries_transaction" in err_msg or "TRANSACTION_NOT_FOUND" in err_msg:
            raise ProblemException(
                status=400,
                code="VALIDATION_ERROR",
                detail="Account or transaction reference is invalid or violates multi-tenant boundary",
                instance=instance
            )
        if "ledger_transactions_posted_by_fkey" in err_msg or "fk_audit_events_actor" in err_msg:
            raise ProblemException(
                status=401,
                code="AUTH_REQUIRED",
                detail="Actor referenced in token does not exist in actors catalog",
                instance=instance
            )
        raise

def reverse_transaction(
    db: Session,
    auth_context: AuthContext,
    transaction_id: uuid.UUID,
    request: ReversalRequest,
    idempotency_key: str,
    request_id: uuid.UUID,
    instance: str = ""
) -> LedgerTransactionSchema:
    """
    Append a balanced compensating reversal transaction.
    Inverts all directions (DEBIT <-> CREDIT), ensures forward-only reversal,
    rejects double-reversal and reversing a reversal, and preserves audit trail.
    """
    # 1. Reserve Idempotency Key Atomically
    payload_dict = {
        "transactionId": str(transaction_id),
        "reason": request.reason
    }
    payload_hash = compute_canonical_hash(payload_dict)

    is_new, cached = reserve_or_get_idempotency(
        db,
        tenant_id=auth_context.tenant_id,
        operation_id="reverseLedgerTransaction",
        key=idempotency_key,
        payload_hash=payload_hash,
        instance=instance
    )
    if not is_new:
        assert cached is not None
        status_code, body = cached
        return LedgerTransactionSchema.model_validate(body)

    # 2. Query target transaction
    orig_tx = db.execute(
        select(LedgerTransaction).filter_by(
            id=transaction_id,
            tenant_id=auth_context.tenant_id
        )
    ).scalar_one_or_none()

    if orig_tx is None:
        raise ProblemException(
            status=404,
            code="VALIDATION_ERROR",
            detail=f"Transaction '{transaction_id}' not found",
            instance=instance
        )

    if orig_tx.reversal_of is not None:
        raise ProblemException(
            status=409,
            code="INVALID_STATE",
            detail=f"Transaction '{transaction_id}' is itself a reversal and cannot be reversed",
            instance=instance
        )

    # Check if target transaction has already been reversed
    existing_rev = db.execute(
        select(LedgerTransaction).filter_by(
            tenant_id=auth_context.tenant_id,
            reversal_of=transaction_id
        )
    ).scalar_one_or_none()

    if existing_rev is not None:
        raise ProblemException(
            status=409,
            code="INVALID_STATE",
            detail=f"Transaction '{transaction_id}' has already been reversed by transaction '{existing_rev.id}'",
            instance=instance
        )

    # 3. Query original entries with accounts
    orig_entries = db.execute(
        select(LedgerEntry, LedgerAccount)
        .join(
            LedgerAccount,
            and_(
                LedgerEntry.tenant_id == LedgerAccount.tenant_id,
                LedgerEntry.account_id == LedgerAccount.id
            )
        )
        .filter(
            LedgerEntry.tenant_id == auth_context.tenant_id,
            LedgerEntry.transaction_id == transaction_id
        )
        .order_by(LedgerEntry.id.asc())
    ).all()

    if not orig_entries:
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail="Original transaction has no entries to reverse",
            instance=instance
        )

    # 4. Invert entries
    reversal_entries_schema: List[LedgerEntrySchema] = []
    entries_json: List[Dict[str, Any]] = []

    for entry, account in orig_entries:
        inverted_dir = "CREDIT" if entry.direction == "DEBIT" else "DEBIT"
        reversal_entries_schema.append(
            LedgerEntrySchema(
                accountCode=account.code,
                direction=inverted_dir,
                amountMinor=entry.amount_minor
            )
        )
        entries_json.append({
            "account_id": str(account.id),
            "direction": inverted_dir,
            "amount_minor": entry.amount_minor,
            "currency": entry.currency,
            "memo": f"Compensating reversal of {transaction_id}: {request.reason}"
        })

    # 5. Atomic Execution
    new_rev_id = uuid.uuid4()
    currency = orig_entries[0][0].currency

    try:
        db.execute(
            text("""
                SELECT append_ledger_transaction(
                    :tx_id, :tenant_id, :tx_type, :currency, CAST(:entries AS jsonb), :posted_by, :reversal_of, 'REVERSAL', :source_id
                )
            """),
            {
                "tx_id": str(new_rev_id),
                "tenant_id": str(auth_context.tenant_id),
                "tx_type": f"{orig_tx.transaction_type}_REVERSAL",
                "currency": currency,
                "entries": json.dumps(entries_json),
                "posted_by": str(auth_context.actor_id) if auth_context.actor_id else None,
                "reversal_of": str(transaction_id),
                "source_id": str(transaction_id)
            }
        )

        # 6. Persist Audit Event
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            tenant_id=auth_context.tenant_id,
            actor_id=auth_context.actor_id,
            action="LEDGER_TRANSACTION_REVERSED",
            entity_type="ledger_transactions",
            entity_id=new_rev_id,
            request_id=request_id,
            payload={
                "reversal_of": str(transaction_id),
                "reason": request.reason
            },
            occurred_at=datetime.now(timezone.utc)
        )
        db.add(audit_event)

        # 7. Complete Idempotency Record
        result = LedgerTransactionSchema(
            id=new_rev_id,
            tenantId=auth_context.tenant_id,
            entries=reversal_entries_schema,
            reversalOf=transaction_id
        )

        complete_idempotency(
            db=db,
            tenant_id=auth_context.tenant_id,
            operation_id="reverseLedgerTransaction",
            key=idempotency_key,
            response_status=201,
            response_body=result.model_dump(mode="json", by_alias=True)
        )

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        err_msg = str(e)
        if "uq_ledger_tx_reversal" in err_msg or "CANNOT_REVERSE_REVERSAL" in err_msg or "already been reversed" in err_msg:
            raise ProblemException(
                status=409,
                code="INVALID_STATE",
                detail="Transaction has already been reversed or target transaction is a reversal",
                instance=instance
            )
        if "LATE_LINE_INSERTION_BLOCKED" in err_msg:
            raise ProblemException(
                status=409,
                code="LEDGER_IMMUTABLE",
                detail="Cannot append entries to a previously committed ledger transaction",
                instance=instance
            )
        if "LEDGER_IMMUTABLE" in err_msg:
            raise ProblemException(
                status=409,
                code="LEDGER_IMMUTABLE",
                detail="Ledger transactions and entries are strictly immutable and cannot be updated or deleted",
                instance=instance
            )
        if "ledger_transactions_posted_by_fkey" in err_msg or "fk_audit_events_actor" in err_msg:
            raise ProblemException(
                status=401,
                code="AUTH_REQUIRED",
                detail="Actor referenced in token does not exist in actors catalog",
                instance=instance
            )
        raise

def get_ledger_entries(
    db: Session,
    auth_context: AuthContext,
    cursor: Optional[str] = None,
    page_size: int = 50,
    instance: str = "/api/v1/ledger/entries"
) -> LedgerPage:
    """
    Read ledger transactions for the caller's tenant with deterministic cursor pagination.
    """
    query = (
        select(LedgerTransaction)
        .filter(LedgerTransaction.tenant_id == auth_context.tenant_id)
        .order_by(LedgerTransaction.posted_at.asc(), LedgerTransaction.id.asc())
    )

    if cursor and cursor.strip():
        cursor_posted_at, cursor_id = decode_cursor(cursor.strip())
        query = query.filter(
            (LedgerTransaction.posted_at > cursor_posted_at) |
            and_(
                LedgerTransaction.posted_at == cursor_posted_at,
                LedgerTransaction.id > cursor_id
            )
        )

    # Fetch page_size + 1 to check nextCursor
    transactions = db.execute(query.limit(page_size + 1)).scalars().all()

    has_more = len(transactions) > page_size
    items_to_process = transactions[:page_size] if has_more else transactions

    tx_ids = [tx.id for tx in items_to_process]

    # Pre-fetch entries and accounts for these transactions
    entries_map: Dict[uuid.UUID, List[LedgerEntrySchema]] = {tx_id: [] for tx_id in tx_ids}
    if tx_ids:
        rows = db.execute(
            select(LedgerEntry, LedgerAccount)
            .join(
                LedgerAccount,
                and_(
                    LedgerEntry.tenant_id == LedgerAccount.tenant_id,
                    LedgerEntry.account_id == LedgerAccount.id
                )
            )
            .filter(
                LedgerEntry.tenant_id == auth_context.tenant_id,
                LedgerEntry.transaction_id.in_(tx_ids)
            )
            .order_by(LedgerEntry.id.asc())
        ).all()

        for entry, account in rows:
            entries_map[entry.transaction_id].append(
                LedgerEntrySchema(
                    accountCode=account.code,
                    direction=entry.direction,
                    amountMinor=entry.amount_minor
                )
            )

    result_items: List[LedgerTransactionSchema] = []
    for tx in items_to_process:
        result_items.append(
            LedgerTransactionSchema(
                id=tx.id,
                tenantId=tx.tenant_id,
                entries=entries_map.get(tx.id, []),
                reversalOf=tx.reversal_of
            )
        )

    next_cursor = None
    if has_more and items_to_process:
        last_tx = items_to_process[-1]
        next_cursor = encode_cursor(last_tx.posted_at.isoformat(), str(last_tx.id))

    return LedgerPage(items=result_items, nextCursor=next_cursor)
