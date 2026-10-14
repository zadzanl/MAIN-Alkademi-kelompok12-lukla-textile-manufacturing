import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Boolean, DateTime, BigInteger, ForeignKey, ForeignKeyConstraint,
    UniqueConstraint, CheckConstraint, Index, CHAR
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    account_class: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ledger_accounts_code"),
        CheckConstraint("account_class IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')", name="chk_account_class"),
        Index("idx_ledger_accounts_lookup", "tenant_id", "code", "active"),
    )

class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), primary_key=True)
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, default="MANUAL", nullable=False)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    posted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("actors.id", ondelete="RESTRICT"), nullable=True)
    reversal_of: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    entries: Mapped[List["LedgerEntry"]] = relationship(
        "LedgerEntry",
        back_populates="transaction",
        cascade="all, delete-orphan",
        order_by="LedgerEntry.id",
        foreign_keys="[LedgerEntry.tenant_id, LedgerEntry.transaction_id]"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "reversal_of"],
            ["ledger_transactions.tenant_id", "ledger_transactions.id"],
            name="fk_ledger_transactions_reversal",
            ondelete="RESTRICT"
        ),
    )

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    memo: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    transaction: Mapped["LedgerTransaction"] = relationship(
        "LedgerTransaction",
        back_populates="entries",
        foreign_keys=[tenant_id, transaction_id]
    )

    account: Mapped["LedgerAccount"] = relationship(
        "LedgerAccount",
        foreign_keys=[tenant_id, account_id],
        overlaps="entries,transaction"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "transaction_id"],
            ["ledger_transactions.tenant_id", "ledger_transactions.id"],
            name="fk_ledger_entries_transaction",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "account_id"],
            ["ledger_accounts.tenant_id", "ledger_accounts.id"],
            name="fk_ledger_entries_account",
            ondelete="RESTRICT"
        ),
        CheckConstraint("direction IN ('DEBIT', 'CREDIT')", name="chk_entry_direction"),
        CheckConstraint("amount_minor > 0", name="chk_entry_amount_positive"),
        Index("idx_ledger_entries_tx", "tenant_id", "transaction_id"),
        Index("idx_ledger_entries_account", "tenant_id", "account_id"),
    )
