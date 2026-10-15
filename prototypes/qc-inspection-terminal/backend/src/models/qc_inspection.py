from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from dataclasses import dataclass, field


class Disposition(str, Enum):
    """QC outcome. Mirrors `QcRequest.disposition` enum in
    `openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml` line 887.
    """

    PASS = "PASS"
    REPAIR = "REPAIR"
    REJECT = "REJECT"


class GarmentStatus(str, Enum):
    """Mirrors `garment_assemblies.status` enum in
    `openspec/changes/lukla-ops-engine-planning/11-database-schema-spec.md` §3."""

    ASSEMBLING = "ASSEMBLING"
    MENUNGGU_QC = "MENUNGGU_QC"
    QC_PASS = "QC_PASS"
    REWORK = "REWORK"
    REJECT_SCRAP = "REJECT_SCRAP"


# Statuses yang boleh diinspeksi (transisi outgoing).
INSPECTABLE_STATUSES = {GarmentStatus.MENUNGGU_QC, GarmentStatus.REWORK}

# Statuses yang tidak boleh diinspeksi ulang (terminal).
TERMINAL_STATUSES = {GarmentStatus.QC_PASS, GarmentStatus.REJECT_SCRAP}


@dataclass
class OperatorRef:
    """Operator (penjahit) yang merakit sebuah komponen. Disimpan di unit
    sehingga repair attribution (FR-8.2) bisa dilacak."""

    operator_id: str
    display_name: str
    component_code: str


@dataclass
class GarmentUnit:
    """Fixture garment unit. Kolom `serial_code` adalah `.serial_code` di
    `garment_assemblies` (planDB). `source_label='FIXTURE'` menandai asal data.
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    serial_code: str = ""
    order_id: str = ""
    article_code: str = ""
    client_code: str = ""
    operators: List[OperatorRef] = field(default_factory=list)
    status: GarmentStatus = GarmentStatus.MENUNGGU_QC
    created_at: datetime = field(default_factory=datetime.utcnow)
    source_label: str = "FIXTURE"

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "serial_code": self.serial_code,
            "order_id": self.order_id,
            "article_code": self.article_code,
            "client_code": self.client_code,
            "operators": [
                {"operator_id": op.operator_id, "display_name": op.display_name,
                 "component_code": op.component_code}
                for op in self.operators
            ],
            "status": self.status.value,
            "pending_qc": self.status in INSPECTABLE_STATUSES,
            "is_pass": self.status == GarmentStatus.QC_PASS,
            "terminal": self.status in TERMINAL_STATUSES,
            "created_at": self.created_at.isoformat() + "Z",
            "source": self.source_label,
        }


@dataclass
class Defect:
    """Mirrors `qc_defects` row in planDB §3."""

    component_code: str
    code: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"component_code": self.component_code, "code": self.code, "notes": self.notes}


@dataclass
class QcInspection:
    """Append-only record. Mirrors `qc_inspections` (planDB §3).
    Tidak pernah di-update atau dihapus."""

    id: str = field(default_factory=lambda: str(uuid4()))
    unit_id: str = ""
    inspector_id: str = ""
    disposition: Disposition = Disposition.PASS
    defects: List[Defect] = field(default_factory=list)
    notes: str = ""
    sequence_no: int = 0
    idempotency_key: str = ""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    prev_status: GarmentStatus = GarmentStatus.MENUNGGU_QC
    new_status: GarmentStatus = GarmentStatus.QC_PASS
    source_label: str = "PROTOTYPE_INSPECTION"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "inspector_id": self.inspector_id,
            "disposition": self.disposition.value,
            "defects": [d.to_dict() for d in self.defects],
            "notes": self.notes,
            "sequence_no": self.sequence_no,
            "occurred_at": self.occurred_at.isoformat() + "Z",
            "prev_status": self.prev_status.value,
            "new_status": self.new_status.value,
            "idempotency_key": self.idempotency_key,
            "source": self.source_label,
        }


def map_disposition_to_status(d: Disposition) -> GarmentStatus:
    if d == Disposition.PASS:
        return GarmentStatus.QC_PASS
    if d == Disposition.REPAIR:
        return GarmentStatus.REWORK
    if d == Disposition.REJECT:
        return GarmentStatus.REJECT_SCRAP
    raise ValueError(f"Unknown disposition: {d}")
