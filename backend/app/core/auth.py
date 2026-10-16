import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Any, Dict
from dataclasses import dataclass
import jwt
from fastapi import Request, Header, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from .config import settings
from .database import get_db, set_db_tenant_context
from ..models.identities import Tenant, Actor
from ..schemas.problem import ProblemException

@dataclass
class AuthContext:
    actor_id: Optional[uuid.UUID]
    tenant_id: uuid.UUID
    roles: List[str]

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT token pinned strictly to HS256."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def _get_auth_context(
    request: Request,
    authorization: Optional[str],
    db: Session,
    allowed_roles: set[str],
    operation_name: str,
) -> AuthContext:
    """
    Authenticate Bearer JWT, enforce HS256, verify Owner or FinancePayroll roles,
    and derive tenant context strictly from verified token claims.
    """
    if not authorization:
        raise ProblemException(
            status=401,
            code="AUTH_REQUIRED",
            detail="Authorization header with Bearer token is required",
            instance=request.url.path
        )

    parts = authorization.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise ProblemException(
            status=401,
            code="AUTH_REQUIRED",
            detail="Authorization header with Bearer token is required",
            instance=request.url.path
        )

    token = parts[1].strip()

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp"]}
        )
    except jwt.ExpiredSignatureError:
        raise ProblemException(
            status=401,
            code="AUTH_REQUIRED",
            detail="Authentication token has expired",
            instance=request.url.path
        )
    except jwt.MissingRequiredClaimError:
        raise ProblemException(
            status=401,
            code="AUTH_REQUIRED",
            detail="Authentication token is missing required 'exp' claim",
            instance=request.url.path
        )
    except jwt.InvalidTokenError as e:
        raise ProblemException(
            status=401,
            code="AUTH_REQUIRED",
            detail=f"Invalid authentication token: {str(e)}",
            instance=request.url.path
        )

    # Extract roles
    raw_roles = payload.get("roles") or payload.get("role") or []
    if isinstance(raw_roles, str):
        roles = [raw_roles]
    elif isinstance(raw_roles, list):
        roles = [str(r) for r in raw_roles]
    else:
        roles = []

    if not any(r in allowed_roles for r in roles):
        raise ProblemException(
            status=403,
            code="FORBIDDEN",
            detail=f"Forbidden: caller roles {roles} do not have permission for {operation_name}",
            instance=request.url.path
        )

    # Derive tenant_id strictly from token claims; never trust caller-supplied headers
    raw_tenant = payload.get("tenant_id") or payload.get("tenantId")
    if not raw_tenant and payload.get("tenantScopes"):
        scopes = payload.get("tenantScopes")
        if isinstance(scopes, list) and len(scopes) > 0:
            raw_tenant = scopes[0]

    if not raw_tenant:
        raise ProblemException(
            status=403,
            code="TENANT_CONTEXT_MISSING",
            detail="Token does not contain required tenant claim",
            instance=request.url.path
        )

    try:
        tenant_id = uuid.UUID(str(raw_tenant))
    except (ValueError, TypeError):
        raise ProblemException(
            status=400,
            code="VALIDATION_ERROR",
            detail=f"Invalid tenant UUID format in token: {raw_tenant}",
            instance=request.url.path
        )

    tenant_row = db.execute(
        select(Tenant.id).filter(Tenant.id == tenant_id, Tenant.active == True)
    ).scalar_one_or_none()
    if not tenant_row:
        raise ProblemException(
            status=403,
            code="FORBIDDEN",
            detail=f"Tenant '{tenant_id}' not found or inactive",
            instance=request.url.path
        )

    # Derive actor_id
    raw_actor = payload.get("sub") or payload.get("actor_id") or payload.get("actorId")
    actor_id: Optional[uuid.UUID] = None
    if raw_actor:
        try:
            actor_id = uuid.UUID(str(raw_actor))
        except (ValueError, TypeError):
            raise ProblemException(
                status=401,
                code="AUTH_REQUIRED",
                detail=f"Invalid actor UUID format in token: {raw_actor}",
                instance=request.url.path
            )
        actor_row = db.execute(
            select(Actor.id).filter(Actor.id == actor_id, Actor.active == True)
        ).scalar_one_or_none()
        if not actor_row:
            raise ProblemException(
                status=401,
                code="AUTH_REQUIRED",
                detail=f"Actor '{actor_id}' not found or inactive",
                instance=request.url.path
            )

    # Set PostgreSQL transaction-local tenant context
    set_db_tenant_context(db, tenant_id=tenant_id, actor_id=actor_id, role=roles[0] if roles else None)

    return AuthContext(actor_id=actor_id, tenant_id=tenant_id, roles=roles)


def get_current_auth_context(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
) -> AuthContext:
    """Authenticate payroll/ledger callers without changing their role boundary."""
    return _get_auth_context(
        request,
        authorization,
        db,
        {"Owner", "FinancePayroll"},
        "ledger operations",
    )


def get_current_stock_auth_context(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
) -> AuthContext:
    """Authenticate stock callers with the narrower warehouse route boundary."""
    return _get_auth_context(
        request,
        authorization,
        db,
        {"Owner", "Warehouse"},
        "warehouse stock operations",
    )
