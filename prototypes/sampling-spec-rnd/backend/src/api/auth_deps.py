"""Reusable server-side authentication and scope dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from ..services.auth_store import PortalUser, get_store
from ..services.ops_store import StoreScope


# No client mapping has been verified for this prototype. Client access stays
# deny-by-default until an authoritative mapping is supplied.
SUPPORTED_CLIENT_IDS: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SessionContext:
    user_id: str
    tenant_id: str
    client_id: str | None
    role: str

    @property
    def effective_scope(self) -> "EffectiveScope":
        if self.role == "client":
            if self.client_id is None or self.client_id not in SUPPORTED_CLIENT_IDS:
                raise HTTPException(status_code=403, detail="Client mapping is unavailable")
            return _scope_from_session(self.tenant_id, self.client_id, self.user_id, self.role)
        return _scope_from_session(self.tenant_id, None, self.user_id, self.role)


EffectiveScope = StoreScope


def _scope_from_session(tenant_id: str, client_id: str | None, actor_id: str, role: str) -> StoreScope:
    """Only the authenticated session dependency may issue a runtime scope."""
    from ..services.ops_store import OpsStore
    return OpsStore._issue_scope(tenant_id, client_id, actor_id, role)


def can_access_record(context: SessionContext, tenant_id: str, client_id: str | None) -> bool:
    """Apply server-derived scope; request query parameters never enter this check."""
    if context.tenant_id != tenant_id:
        return False
    if context.role == "client":
        return context.client_id in SUPPORTED_CLIENT_IDS and context.client_id == client_id
    return True


def bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Header Authorization wajib diisi.")
    parts = authorization.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Format token Bearer tidak valid.")
    return parts[1].strip()


def session_context(authorization: str | None = Header(None, alias="Authorization")) -> SessionContext:
    user: PortalUser | None = get_store().get_session_user(bearer_token(authorization))
    if user is None:
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau telah berakhir.")
    if user.role == "client" and user.client_id not in SUPPORTED_CLIENT_IDS:
        raise HTTPException(status_code=403, detail="Client mapping is not supported.")
    return SessionContext(user.user_id, user.tenant_id, user.client_id, user.role)


def require_roles(*roles: str):
    def dependency(context: SessionContext = Depends(session_context)) -> SessionContext:
        if context.role not in roles:
            raise HTTPException(status_code=403, detail="Peran tidak diizinkan untuk tindakan ini.")
        return context

    return dependency
