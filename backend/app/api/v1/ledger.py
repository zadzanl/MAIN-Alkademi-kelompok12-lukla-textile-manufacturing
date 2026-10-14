import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Header, Path, Query, Request, status
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.auth import AuthContext, get_current_auth_context
from ...schemas.ledger import LedgerRequest, LedgerTransaction, ReversalRequest, LedgerPage
from ...schemas.problem import ProblemException
from ...services.ledger import post_transaction, reverse_transaction, get_ledger_entries

router = APIRouter(prefix="/ledger", tags=["ledger-audit"])

@router.post(
    "/transactions",
    response_model=LedgerTransaction,
    status_code=status.HTTP_201_CREATED,
    operation_id="appendLedgerTransaction",
    summary="Append balanced transaction"
)
def append_ledger_transaction(
    request: Request,
    body: LedgerRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=16, max_length=200),
    auth_context: AuthContext = Depends(get_current_auth_context),
    db: Session = Depends(get_db)
):
    request_id = getattr(request.state, "request_id", uuid.uuid4())
    return post_transaction(
        db=db,
        auth_context=auth_context,
        request=body,
        idempotency_key=idempotency_key,
        request_id=request_id,
        instance=request.url.path
    )

@router.post(
    "/transactions/{transactionId}/reversals",
    response_model=LedgerTransaction,
    status_code=status.HTTP_201_CREATED,
    operation_id="reverseLedgerTransaction",
    summary="Append compensating reversal"
)
def reverse_ledger_transaction(
    request: Request,
    body: ReversalRequest,
    transaction_id: uuid.UUID = Path(..., alias="transactionId"),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=16, max_length=200),
    auth_context: AuthContext = Depends(get_current_auth_context),
    db: Session = Depends(get_db)
):
    request_id = getattr(request.state, "request_id", uuid.uuid4())
    return reverse_transaction(
        db=db,
        auth_context=auth_context,
        transaction_id=transaction_id,
        request=body,
        idempotency_key=idempotency_key,
        request_id=request_id,
        instance=request.url.path
    )

@router.get(
    "/entries",
    response_model=LedgerPage,
    status_code=status.HTTP_200_OK,
    operation_id="getLedgerEntries",
    summary="Read scoped ledger"
)
def get_entries(
    request: Request,
    cursor: Optional[str] = Query(None),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    auth_context: AuthContext = Depends(get_current_auth_context),
    db: Session = Depends(get_db)
):
    return get_ledger_entries(
        db=db,
        auth_context=auth_context,
        cursor=cursor,
        page_size=page_size,
        instance=request.url.path
    )
