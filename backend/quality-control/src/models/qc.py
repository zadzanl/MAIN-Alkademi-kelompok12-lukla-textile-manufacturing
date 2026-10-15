"""QC contract schemas and the assembly status vocabulary.

The vocabulary is the one frozen in ``11-database-schema-spec.md`` §2 and in the
OpenAPI enums, and the transition table below is the state machine from
``11-database-schema-spec.md`` §6:

    MENUNGGU_QC -> PASS | REPAIR | REJECT
    REWORK      -> PASS | REPAIR | REJECT
    PASS, REJECT are terminal

``ASSEMBLING`` is not inspectable: an assembly that has not finished its pieces
is not a quality target yet.
"""

from collections.abc import Mapping
from enum import StrEnum
from typing import Final
from uuid import UUID

from pydantic import Field, field_validator

from src.models.base import ContractModel


class Disposition(StrEnum):
    """The QC inspector's decision for one assembly."""

    PASS = "PASS"
    REPAIR = "REPAIR"
    REJECT = "REJECT"


class AssemblyStatus(StrEnum):
    """``garment_assemblies.status``, the QC target's own status."""

    ASSEMBLING = "ASSEMBLING"
    MENUNGGU_QC = "MENUNGGU_QC"
    QC_PASS = "QC_PASS"
    REWORK = "REWORK"
    REJECT_SCRAP = "REJECT_SCRAP"


DISPOSITION_STATUS: Final[Mapping[Disposition, AssemblyStatus]] = {
    Disposition.PASS: AssemblyStatus.QC_PASS,
    Disposition.REPAIR: AssemblyStatus.REWORK,
    Disposition.REJECT: AssemblyStatus.REJECT_SCRAP,
}

INSPECTABLE_STATUSES: Final[frozenset[AssemblyStatus]] = frozenset(
    {AssemblyStatus.MENUNGGU_QC, AssemblyStatus.REWORK}
)

TERMINAL_STATUSES: Final[frozenset[AssemblyStatus]] = frozenset(
    {AssemblyStatus.QC_PASS, AssemblyStatus.REJECT_SCRAP}
)

DEFECT_REQUIRED_DISPOSITIONS: Final[frozenset[Disposition]] = frozenset(
    {Disposition.REPAIR, Disposition.REJECT}
)


class Defect(ContractModel):
    """One defect against one component piece of the inspected assembly."""

    component_unit_id: UUID
    code: str = Field(min_length=1)
    notes: str | None = None


class QcRequest(ContractModel):
    """Body of ``inspectUnit``: classify one finished assembly."""

    assembly_id: UUID
    disposition: Disposition
    defects: list[Defect]


class QcInspection(QcRequest):
    """The stored, append-only inspection the operation returns."""

    id: UUID


class AssemblyRequest(ContractModel):
    """Body of ``createAssembly``."""

    order_id: UUID
    serial_code: str = Field(min_length=1)
    component_unit_ids: list[UUID] = Field(min_length=1)

    @field_validator("component_unit_ids")
    @classmethod
    def _pieces_are_distinct(cls, value: list[UUID]) -> list[UUID]:
        if len(set(value)) != len(value):
            raise ValueError("componentUnitIds must be distinct")
        return value


class Assembly(AssemblyRequest):
    """An assembly as ``listAssemblies`` returns it."""

    id: UUID
    status: AssemblyStatus


class AssemblyPage(ContractModel):
    """Body of ``listAssemblies``."""

    items: list[Assembly]
    next_cursor: str | None = None


class QcSummary(ContractModel):
    """The ``qc`` section of ``getDashboard``."""

    pass_count: int = Field(ge=0)
    repair_count: int = Field(ge=0)
    reject_count: int = Field(ge=0)
