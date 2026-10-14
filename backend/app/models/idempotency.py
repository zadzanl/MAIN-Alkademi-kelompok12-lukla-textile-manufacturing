import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, SmallInteger, DateTime, LargeBinary, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), primary_key=True)
    key: Mapped[str] = mapped_column(String, nullable=False)
    operation_id: Mapped[str] = mapped_column(String, nullable=False)
    canonical_payload_hash: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    response_status: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "operation_id", "key", name="uq_idempotency_records"),
        CheckConstraint("status IN ('PENDING', 'COMPLETED', 'FAILED')", name="chk_idempotency_status"),
    )
