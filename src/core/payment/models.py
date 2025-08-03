# src/core/payment/models.py

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.core.tariff.models import Tariff
    from src.core.user.models import User


class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tariff_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tariffs.id", ondelete="RESTRICT"), nullable=False
    )
    amount: Mapped[Numeric] = mapped_column(Numeric(7, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    invoice_payload: Mapped[str] = mapped_column(String, nullable=False)
    telegram_payment_charge_id: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
    )
    provider_payment_charge_id: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.timezone("utc", func.now()), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments", lazy="selectin")
    tariff: Mapped["Tariff"] = relationship("Tariff", back_populates="payments", lazy="selectin")

    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, "
            f"tariff_id={self.tariff_id}, amount={self.amount}, "
            f"status={self.status.value})>"
        )
