from typing import TYPE_CHECKING, List

import sqlalchemy as sa
from sqlalchemy import Boolean, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base

if TYPE_CHECKING:
    # Эти импорты нужны только для проверки типов (flake8),
    # в рантайме они не будут выполняться
    from src.core.subscription.models import Subscription


class Tariff(Base):
    __tablename__ = "tariffs"
    __table_args__ = (UniqueConstraint("name", name="uq_tariff_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        server_default=sa.true(),
    )

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="tariff", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Tariff(id={self.id}, name='{self.name}', "
            f"duration_days={self.duration_days}, price={self.price})>"
        )
