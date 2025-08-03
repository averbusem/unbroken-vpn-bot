from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.core.user.models import User


class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (
        UniqueConstraint("referrer_id", "referred_id", name="uq_referral_pair"),
        UniqueConstraint("referred_id", name="uq_referred_user"),
        Index("idx_referrer_referred", "referrer_id", "referred_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    referred_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bonus_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.timezone("utc", func.now()), nullable=False
    )

    # Relationships
    referrer: Mapped["User"] = relationship(
        "User", foreign_keys=[referrer_id], back_populates="sent_referrals", lazy="select"
    )
    referred: Mapped["User"] = relationship(
        "User", foreign_keys=[referred_id], back_populates="received_referral", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<ReferralProgram(id={self.id}, referrer_id={self.referrer_id}, "
            f"referred_id={self.referred_id}, bonus_days={self.bonus_days})>"
        )
