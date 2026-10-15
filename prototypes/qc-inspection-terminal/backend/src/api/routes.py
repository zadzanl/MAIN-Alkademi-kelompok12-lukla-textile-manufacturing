from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from ..models.qc_inspection import (
    Disposition,
    GarmentStatus,
    INSPECTABLE_STATUSES,
    TERMINAL_STATUSES,
)
from ..services.qc_workflow import QcWorkflow, WorkflowError


# Mirrors the contract envelope shape and the operation IDs declared in
# `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml`.
# Endpoints marked (prototype-only) are not part of the frozen contract;
# they are minimal extensions needed for inspection terminal UX.


def _error_payload(code: str, message: str) -> Dict[str, Any]:
    return {
        "type": "about:blank",
        "title": code,
        "status": 409 if code == "IDEMPOTENCY_CONFLICT" else 422,
        "code": code,
        "detail": message,
        "instance": "qc-inspection-terminal",
    }


def create_api_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/qc-inspection-terminal",
        tags=["qc-inspection-terminal"],
    )
    wf = QcWorkflow()

    @router.get("/health")
    def health() -> Dict[str, Any]:
        return {
            "status": "healthy",
            "module": "qc-inspection-terminal",
            "prototype": True,
            "runtime_state": "in-memory",
            "data_source": "FIXTURE (src/utils/seed_fixtures.py)",
            "now": datetime.utcnow().isoformat() + "Z",
        }

    # ── Pencarian unit berdasarkan serial (prototype-only) ──────────────────
    @router.get("/units/lookup")
    def lookup_unit(serial: str = Query(..., min_length=1, max_length=64)) -> Dict[str, Any]:
        unit = wf.find_by_serial(serial)
        if unit is None:
            raise HTTPException(
                status_code=404,
                detail=_error_payload(
                    "NOT_FOUND", f"Serial '{serial}' tidak ditemukan di fixture."
                ),
            )
        return {
            "success": True,
            "unit": unit.to_public_dict(),
            "data_source": "FIXTURE",
        }

    # ── List semua unit fixture (prototype-only) ─────────────────────────────
    @router.get("/units")
    def list_units(status: Optional[str] = Query(None)) -> Dict[str, Any]:
        status_filter: Optional[GarmentStatus] = None
        if status:
            try:
                status_filter = GarmentStatus(status)
            except ValueError as exc:
                raise HTTPException(
                    status_code=422,
                    detail=_error_payload(
                        "VALIDATION_ERROR", f"status '{status}' tidak dikenal."
                    ),
                ) from exc
        units = wf.list_units(status_filter)
        return {
            "success": True,
            "count": len(units),
            "items": [u.to_public_dict() for u in units],
            "data_source": "FIXTURE",
        }

    # ── Riwayat inspeksi per unit (prototype-only) ───────────────────────────
    @router.get("/units/{unit_id}/inspections")
    def unit_inspection_history(unit_id: str) -> Dict[str, Any]:
        unit = wf.find_by_id(unit_id)
        if unit is None:
            raise HTTPException(
                status_code=404,
                detail=_error_payload("NOT_FOUND", f"Unit '{unit_id}' tidak ditemukan."),
            )
        rows = wf.list_inspections_for_unit(unit_id)
        return {
            "success": True,
            "unit": unit.to_public_dict(),
            "history_count": len(rows),
            "history": [r.to_dict() for r in rows],
            "append_only": True,
        }

    # ── Catat hasil inspeksi (mirrors openapi.yaml POST /qc-inspections) ────
    @router.post("/inspections", status_code=201)
    def record_inspection(
        payload: Dict[str, Any],
        idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=16, max_length=200),
    ) -> Dict[str, Any]:
        disposition_raw = payload.get("disposition", "")
        try:
            disposition = Disposition(disposition_raw)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=_error_payload(
                    "VALIDATION_ERROR",
                    "disposition wajib salah satu dari: PASS, REPAIR, REJECT.",
                ),
            ) from exc

        unit_id = payload.get("unit_id") or payload.get("assemblyId") or ""
        if not unit_id:
            raise HTTPException(
                status_code=422,
                detail=_error_payload("VALIDATION_ERROR", "Field 'unit_id' wajib diisi."),
            )
        inspector_id = str(payload.get("inspector_id") or payload.get("inspectorId") or "").strip()
        if not inspector_id:
            inspector_id = "qc-unknown-prototype"
        defects = payload.get("defects") or []
        notes = str(payload.get("notes") or "")

        try:
            replayed, body = wf.record_inspection(
                unit_id=unit_id,
                disposition=disposition,
                inspector_id=inspector_id,
                defects_payload=defects,
                notes=notes,
                idempotency_key=idempotency_key,
            )
        except WorkflowError as e:
            msg = str(e)
            code = "IDEMPOTENCY_CONFLICT" if "IDEMPOTENCY_CONFLICT" in msg else "VALIDATION_ERROR"
            raise HTTPException(
                status_code=409 if code == "IDEMPOTENCY_CONFLICT" else 422,
                detail=_error_payload(code, msg),
            ) from e
        # re-stamp replay flag (idempotent replay retains identical body)
        body["idempotent_replay"] = replayed
        return body

    # ── Ringkasan untuk dashboard (prototype, mirrors Dashboard.qc) ─────────
    @router.get("/workflow/summary")
    def workflow_summary() -> Dict[str, Any]:
        return {
            "success": True,
            "prototype": True,
            "data_source": "FIXTURE",
            **wf.summary(),
        }

    return router
