"""Assembly, allocation, and inspection tables owned by migration M007.

The state machine, the append-only log, and the defect rules are enforced by the
triggers in `backend/migrations/007_assemblies_and_qc.sql`; these models exist so the
API layer can read and insert through the same column contract.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

ASSEMBLY_STATUSES = ("ASSEMBLING", "MENUNGGU_QC", "QC_PASS", "REWORK", "REJECT_SCRAP")
DISPOSITIONS = ("PASS", "REPAIR", "REJECT")


class GarmentAssembly(Base):
    __tablename__ = "garment_assemblies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), primary_key=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    serial_code: Mapped[str] = mapped_column(String, nullable=False)
    # The fail-safe default is the state that cannot be inspected.
    status: Mapped[str] = mapped_column(String, default="ASSEMBLING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "serial_code", name="uq_garment_assemblies_serial"),
        ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["orders.tenant_id", "orders.id"],
            name="fk_garment_assemblies_order",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('ASSEMBLING', 'MENUNGGU_QC', 'QC_PASS', 'REWORK', 'REJECT_SCRAP')",
            name="chk_garment_assemblies_status",
        ),
        Index("idx_garment_assemblies_queue", "tenant_id", "status", "created_at", "id"),
    )


class AssemblyComponent(Base):
    """One allocated component piece; a piece belongs to exactly one assembly, ever."""

    __tablename__ = "assembly_components"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), primary_key=True
    )
    assembly_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    garment_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    component_code: Mapped[str] = mapped_column(String, nullable=False)
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "garment_unit_id", name="uq_assembly_components_unit"),
        ForeignKeyConstraint(
            ["tenant_id", "assembly_id"],
            ["garment_assemblies.tenant_id", "garment_assemblies.id"],
            name="fk_assembly_components_assembly",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "garment_unit_id"],
            ["garment_units.tenant_id", "garment_units.id"],
            name="fk_assembly_components_unit",
            ondelete="RESTRICT",
        ),
        Index("idx_assembly_components_assembly", "tenant_id", "assembly_id"),
    )


class QcInspection(Base):
    """One append-only inspection row. `sequence_no` is assigned by the insert trigger."""

    __tablename__ = "qc_inspections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), primary_key=True
    )
    assembly_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    inspector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actors.id", ondelete="RESTRICT"), nullable=False
    )
    disposition: Mapped[str] = mapped_column(String, nullable=False)
    # Sent as NULL on insert; `trg_qc_inspections_prepare` assigns the next sequence number.
    sequence_no: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "assembly_id", "sequence_no", name="uq_qc_inspections_sequence"),
        ForeignKeyConstraint(
            ["tenant_id", "assembly_id"],
            ["garment_assemblies.tenant_id", "garment_assemblies.id"],
            name="fk_qc_inspections_assembly",
            ondelete="RESTRICT",
        ),
        CheckConstraint("disposition IN ('PASS', 'REPAIR', 'REJECT')", name="chk_qc_inspections_disposition"),
        Index("idx_qc_inspections_assembly", "tenant_id", "assembly_id", "sequence_no"),
    )


class QcDefect(Base):
    """One defect on one component piece of the inspected assembly."""

    __tablename__ = "qc_defects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), primary_key=True
    )
    inspection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    garment_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    defect_code: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "inspection_id", "garment_unit_id", name="uq_qc_defects_piece"),
        ForeignKeyConstraint(
            ["tenant_id", "inspection_id"],
            ["qc_inspections.tenant_id", "qc_inspections.id"],
            name="fk_qc_defects_inspection",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "garment_unit_id"],
            ["garment_units.tenant_id", "garment_units.id"],
            name="fk_qc_defects_unit",
            ondelete="RESTRICT",
        ),
        Index("idx_qc_defects_inspection", "tenant_id", "inspection_id"),
    )
