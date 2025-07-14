from datetime import datetime
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base

if TYPE_CHECKING:
    # Эти импорты нужны только для проверки типов (flake8),
    # в рантайме они не будут выполняться
    from src.core.tariff.models import Tariff
    from src.core.user.models import User


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("idx_sub_user_active", "user_id", "is_active"),
        Index("idx_sub_end_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    tariff_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tariffs.id", ondelete="RESTRICT"), nullable=False
    )
    vpn_key: Mapped[str] = mapped_column(String(80), nullable=False)
    outline_key_id: Mapped[str] = mapped_column(String(64), nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True, server_default=sa.true()
    )
    cnt_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=None,
        server_onupdate=func.timezone("utc", func.now()),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.timezone("utc", func.now()), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions", lazy="select")
    tariff: Mapped["Tariff"] = relationship("Tariff", back_populates="subscriptions", lazy="select")

    def __repr__(self) -> str:
        return (
            f"<Subscription(id={self.id}, user_id={self.user_id}, "
            f"tariff_id={self.tariff_id}, end_date={self.end_date}, "
            f"active={self.is_active})>"
        )
