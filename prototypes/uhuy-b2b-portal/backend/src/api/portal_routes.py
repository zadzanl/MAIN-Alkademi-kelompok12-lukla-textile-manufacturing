"""portal_routes.py — Client-scoped data API for the UHUY B2B external portal.

Endpoints (prefix ``/api/portal``), all requiring a client bearer session:
  GET  /health              status modul
  GET  /summary             KPI milik klien yang login
  GET  /orders              daftar order milik klien
  GET  /orders/{order_id}   detail order milik klien
  GET  /stock               stok bahan titipan milik klien
  GET  /requests            riwayat pengajuan milik klien
  POST /requests/order      ajukan order produksi baru
  POST /requests/sample     ajukan permintaan desain/sample baru

The ``client_id`` is always resolved from the authenticated session — never from
the request body or query — so one client can never read or write another
client's rows (RBAC "Klien Maklon/Ext"; AT-R08). Static routes are registered
before parameterised ones.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ..services.portal_store import ClientUser, get_store

SCHEMES = {"CMT", "Semi-CMT", "Full Package"}


# ── Auth dependency ──────────────────────────────────────────────────────────


def _client_user(authorization: str | None) -> ClientUser:
    if not authorization:
        raise HTTPException(status_code=401, detail="Header Authorization wajib diisi.")
    parts = authorization.split(maxsplit=1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Format token Bearer tidak valid.")
    user = get_store().get_session_user(parts[1].strip())
    if user is None:
        raise HTTPException(status_code=401, detail="Sesi tidak valid atau telah berakhir.")
    if user.role != "client":
        raise HTTPException(status_code=403, detail="Endpoint ini khusus akun klien eksternal.")
    return user


# ── Request models ───────────────────────────────────────────────────────────


class OrderRequestCreate(BaseModel):
    article_name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(gt=0, le=1_000_000)
    scheme: str = Field(min_length=1, max_length=40)
    target_date: str = Field(default="", max_length=40)
    notes: str = Field(default="", max_length=1000)


class SampleRequestCreate(BaseModel):
    article_name: str = Field(min_length=1, max_length=120)
    quantity: int = Field(default=1, gt=0, le=10_000)
    scheme: str = Field(default="Semi-CMT", max_length=40)
    target_date: str = Field(default="", max_length=40)
    notes: str = Field(default="", max_length=1000)


def _validate_scheme(scheme: str) -> None:
    if scheme not in SCHEMES:
        raise HTTPException(
            status_code=400,
            detail=f"Skema maklon tidak valid. Pilih salah satu: {', '.join(sorted(SCHEMES))}.",
        )


# ── Router factory ───────────────────────────────────────────────────────────


def create_portal_router() -> APIRouter:
    router = APIRouter(prefix="/api/portal", tags=["portal"])

    @router.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "healthy", "module": "uhuy-b2b-portal", "scope": "external"}

    @router.get("/summary")
    def get_summary(
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, Any]:
        user = _client_user(authorization)
        return {"success": True, "summary": get_store().summary(user.client_id)}

    @router.get("/orders")
    def list_orders(
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, Any]:
        user = _client_user(authorization)
        rows = [o.to_dict() for o in get_store().list_orders(user.client_id)]
        return {"success": True, "data": rows, "count": len(rows)}

    @router.get("/stock")
    def list_stock(
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, Any]:
        user = _client_user(authorization)
        rows = [s.to_dict() for s in get_store().list_stock(user.client_id)]
        return {"success": True, "data": rows, "count": len(rows)}

    @router.get("/requests")
    def list_requests(
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, Any]:
        user = _client_user(authorization)
        rows = [r.to_dict() for r in get_store().list_requests(user.client_id)]
        return {"success": True, "data": rows, "count": len(rows)}

    @router.post("/requests/order", status_code=201)
    def create_order_request(
        payload: OrderRequestCreate,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, Any]:
        user = _client_user(authorization)
        _validate_scheme(payload.scheme)
        req = get_store().create_request(
            client_id=user.client_id,
            kind="order",
            article_name=payload.article_name,
            quantity=payload.quantity,
            scheme=payload.scheme,
            target_date=payload.target_date,
            notes=payload.notes,
        )
        return {
            "success": True,
            "request_id": req.request_id,
            "status": req.status,
            "message": "Pengajuan order diterima dan menunggu peninjauan tim internal.",
        }

    @router.post("/requests/sample", status_code=201)
    def create_sample_request(
        payload: SampleRequestCreate,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, Any]:
        user = _client_user(authorization)
        _validate_scheme(payload.scheme)
        req = get_store().create_request(
            client_id=user.client_id,
            kind="sample",
            article_name=payload.article_name,
            quantity=payload.quantity,
            scheme=payload.scheme,
            target_date=payload.target_date,
            notes=payload.notes,
        )
        return {
            "success": True,
            "request_id": req.request_id,
            "status": req.status,
            "message": "Permintaan sample diterima dan menunggu peninjauan tim internal.",
        }

    @router.get("/orders/{order_id}")
    def get_order(
        order_id: str,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, Any]:
        user = _client_user(authorization)
        order = get_store().get_order(user.client_id, order_id)
        if order is None:
            # 404 (not 403) so an inaccessible id never confirms it exists elsewhere.
            raise HTTPException(status_code=404, detail="Order tidak ditemukan.")
        return {"success": True, "data": order.to_dict()}

    @router.get("/requests/{request_id}")
    def get_request(
        request_id: str,
        authorization: str | None = Header(None, alias="Authorization"),
    ) -> dict[str, Any]:
        user = _client_user(authorization)
        req = get_store().get_request(user.client_id, request_id)
        if req is None:
            raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan.")
        return {"success": True, "data": req.to_dict()}

    return router
