from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

import sqlalchemy as sa
from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base

if TYPE_CHECKING:
    # Эти импорты нужны только для проверки типов (flake8),
    # в рантайме они не будут выполняться
    from src.core.payment.models import Payment
    from src.core.referral.models import Referral
    from src.core.subscription.models import Subscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    referral_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    trial_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=sa.false(),
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=sa.false(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.timezone("utc", func.now()), nullable=False
    )

    # Relationships
    subscriptions: Mapped[Optional["Subscription"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="select"
    )
    # One-to-Many: пользователь может приглашать многих
    sent_referrals: Mapped[List["Referral"]] = relationship(
        back_populates="referrer", foreign_keys="Referral.referrer_id", lazy="select"
    )

    # One-to-One: пользователь может быть приглашён только одним
    received_referral: Mapped[Optional["Referral"]] = relationship(
        back_populates="referred", foreign_keys="Referral.referred_id", uselist=False, lazy="select"
    )
    payments: Mapped[List["Payment"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def referrer(self) -> Optional["User"]:
        """Пользователь, который пригласил текущего (если есть)"""
        return self.received_referral.referrer if self.received_referral else None

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
