"""QC Inspection workflow orchestrator (in-memory).

Aturan transisi state (mengikuti planning contract
`openspec/changes/lukla-ops-engine-planning/specs/quality-control-and-inspection/spec.md` dan
`11-database-schema-spec.md` §3):

- MENUNGGU_QC -> {PASS, REPAIR, REJECT}
- REWORK      -> {PASS, REPAIR, REJECT}   (siklus kedua REPAIR->PASS tanpa
                                            kredit borongan ganda, FR-8.2)
- QC_PASS, REJECT_SCRAP: terminal — inspeksi berikutnya ditolak.

Side-effects yang **TIDAK** dilakukan oleh QC module (per constraint user):
  - REPAIR tidak menghasilkan kredit borongan baru untuk operator.
  - REJECT tidak memicu potongan gaji otomatis (OQ-7 masih PENDING/BLOCKED).
  - PASS tidak otomatis membuat wage_credit atau qc_bonus_accrual.

Side-effects finansial sepenuhnya menjadi wewenang modul Payroll
(`proposed=PENDING_RULE` → `FINANCIAL_RULE_PENDING` dihitung di sana).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..models.qc_inspection import (
    Defect,
    Disposition,
    GarmentStatus,
    GarmentUnit,
    QcInspection,
    TERMINAL_STATUSES,
    INSPECTABLE_STATUSES,
    map_disposition_to_status,
)
from ..utils.idempotency import IdempotencyCache, IdempotencyConflictError
from ..utils.seed_fixtures import FIXTURE_UNITS


class WorkflowError(Exception):
    """Domain validation error sebelum flow service berkomunikasi keluar."""


class QcWorkflow:
    """In-memory implementation of the QC inspection workflow."""

    def __init__(self) -> None:
        self._units: List[GarmentUnit] = list(FIXTURE_UNITS)
        self._by_id: Dict[str, GarmentUnit] = {u.id: u for u in self._units}
        self._by_serial: Dict[str, str] = {u.serial_code: u.id for u in self._units}
        self._inspections: List[QcInspection] = []
        self._seq: Dict[str, int] = {}
        self._idem = IdempotencyCache()

    # ── Read ─────────────────────────────────────────────────────────────────
    def find_by_serial(self, serial: str) -> Optional[GarmentUnit]:
        uid = self._by_serial.get(serial)
        return self._by_id.get(uid) if uid else None

    def find_by_id(self, unit_id: str) -> Optional[GarmentUnit]:
        return self._by_id.get(unit_id)

    def list_units(self, status_filter: Optional[GarmentStatus] = None) -> List[GarmentUnit]:
        if status_filter is None:
            return list(self._units)
        return [u for u in self._units if u.status == status_filter]

    def list_inspections_for_unit(self, unit_id: str) -> List[QcInspection]:
        return [i for i in self._inspections if i.unit_id == unit_id]

    # ── Write ────────────────────────────────────────────────────────────────
    def record_inspection(
        self,
        *,
        unit_id: str,
        disposition: Disposition,
        inspector_id: str,
        defects_payload: List[Dict[str, Any]],
        notes: str,
        idempotency_key: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Return (replayed, body). replayed=True berarti replay idempotent.

        Raises WorkflowError untuk kesalahan domain.
        """
        # 1. Validasi input dasar (key + inspector).
        #    Idempotency lookup sengaja dilakukan SETELAH basic validation
        #    dan SETELAH defect-normalization (sebagai bagian dari
        #    validasi payload), tapi SEBELUM state guard. Urutan ini
        #    menjamin:
        #      - key/payload tidak valid -> 422 VALIDATION_ERROR
        #      - key baru atau key sama dengan payload identik -> apply
        #      - key sama dengan payload berbeda -> 409 IDEMPOTENCY_CONFLICT
        #      - replay (key+payload identik dengan sebelumnya) -> cached body
        #        dikembalikan tanpa menyentuh state, sehingga unit yang sudah
        #        terminal akibat request pertama tetap me-replay dengan benar.
        if not idempotency_key or len(idempotency_key) < 16:
            raise WorkflowError("Idempotency-Key wajib diisi (min 16 karakter).")
        if not inspector_id:
            raise WorkflowError("inspector_id wajib diisi.")

        # 3. Disposition-specific validation
        defects: List[Defect] = []
        if disposition in (Disposition.REPAIR, Disposition.REJECT):
            if not defects_payload:
                raise WorkflowError(
                    f"Disposition {disposition.value} wajib menyertakan minimal 1 defect."
                )
            for d in defects_payload:
                if not isinstance(d, dict):
                    raise WorkflowError("defects items must be objects.")
                comp = str(d.get("component_code") or d.get("componentCode") or "")
                code = str(d.get("code", ""))
                dnotes = str(d.get("notes", ""))
                if not comp or not code:
                    raise WorkflowError("defect butuh component_code & code non-empty.")
                defects.append(Defect(component_code=comp, code=code, notes=dnotes))

        # 4. Canonical payload untuk idempotency key
        canonical: Dict[str, Any] = {
            "unit_id": unit_id,
            "disposition": disposition.value,
            "inspector_id": inspector_id,
            "defects": [
                {"component_code": d.component_code, "code": d.code, "notes": d.notes}
                for d in defects
            ],
            "notes": notes,
        }

        # 5. Idempotency check
        try:
            stored = self._idem.lookup(idempotency_key, canonical)
        except IdempotencyConflictError:
            raise WorkflowError(
                f"IDEMPOTENCY_CONFLICT: key '{idempotency_key}' dipakai ulang "
                "dengan payload berbeda (signature beda)."
            )
        if stored is not None:
            return True, stored

        # State guard hanya berlaku untuk first-write (replay sudah return di
        # atas). Urutan dipertahankan agar inspeksi pertama tetap menolak
        # jika unit sudah terminal / bukan inspectable / tidak ditemukan.
        unit = self._by_id.get(unit_id)
        if unit is None:
            raise WorkflowError(f"Unit '{unit_id}' tidak ditemukan di fixture.")
        if unit.status in TERMINAL_STATUSES:
            raise WorkflowError(
                f"Unit '{unit.serial_code}' berstatus terminal "
                f"({unit.status.value}); inspeksi berikutnya ditolak."
            )
        if unit.status not in INSPECTABLE_STATUSES:
            raise WorkflowError(
                f"Unit '{unit.serial_code}' berstatus '{unit.status.value}'; "
                "tidak dapat diinspeksi."
            )

        # Apply state transition + store cache (append-only,no re-write).
        prev_status = unit.status
        new_status = map_disposition_to_status(disposition)
        seq = self._seq.get(unit_id, 0) + 1
        self._seq[unit_id] = seq

        ins = QcInspection(
            unit_id=unit_id,
            inspector_id=inspector_id,
            disposition=disposition,
            defects=defects,
            notes=notes,
            sequence_no=seq,
            idempotency_key=idempotency_key,
            prev_status=prev_status,
            new_status=new_status,
        )
        self._inspections.append(ins)  # append-only; tidak pernah dihapus, replay tidak menambah inspeksi baru.
        unit.status = new_status

        body: Dict[str, Any] = {
            "success": True,
            "inspection": ins.to_dict(),
            "unit_after": unit.to_public_dict(),
            "side_effects": {
                "wage_credit_created": False,
                "qc_bonus_accrual_created": False,
                "wage_deducted": False,
                "reason": (
                    "OQ-7 (reject_compensation_policy=NO_AUTOMATIC_DEDUCTION) "
                    "and bonus pool ÷3 remain PRODUCTION_BLOCKED. Payroll "
                    "module creates financial side-effects under an approved "
                    "FinancialRule."
                ),
            },
        }
        self._idem.store(idempotency_key, canonical, body)
        return False, body

    # ── Aggregate ────────────────────────────────────────────────────────────
    def summary(self) -> Dict[str, Any]:
        units = self._units
        return {
            "qc": {
                "pass_count": sum(1 for u in units if u.status == GarmentStatus.QC_PASS),
                "repair_count": sum(1 for u in units if u.status == GarmentStatus.REWORK),
                "reject_count": sum(1 for u in units if u.status == GarmentStatus.REJECT_SCRAP),
                "pending_count": sum(1 for u in units if u.status in INSPECTABLE_STATUSES),
            },
            "total_units": len(units),
            "total_inspections_recorded": len(self._inspections),
        }
