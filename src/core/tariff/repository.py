from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.tariff.models import Tariff


class TariffRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, price: float, duration_days: int) -> Tariff:
        tariff = Tariff(name=name, price=price, duration_days=duration_days)
        self.session.add(tariff)
        await self.session.flush()
        return tariff

    async def get_all_active(self) -> Sequence[Tariff]:
        query = select(Tariff).where(Tariff.is_active)
        tariffs = await self.session.execute(query)
        return tariffs.scalars().all()

    async def get_by_name(self, name: str) -> Tariff | None:
        query = select(Tariff).where(Tariff.name == name)
        tariff = await self.session.execute(query)
        return tariff.scalar_one_or_none()

    async def get_by_id(self, tariff_id: int) -> Tariff | None:
        query = select(Tariff).where(Tariff.id == tariff_id)
        tariff = await self.session.execute(query)
        return tariff.scalars().first()

    async def deactivate(self, tariff: Tariff) -> None:
        tariff.is_active = False
        await self.session.flush()

    async def update(
        self,
        tariff: Tariff,
        *,
        name: str | None = None,
        price: float | None = None,
        duration_days: int | None = None
    ) -> Tariff:
        if name:
            tariff.name = name
        if price:
            tariff.price = price
        if duration_days:
            tariff.duration_days = duration_days
        self.session.add(tariff)
        await self.session.flush()
        return tariff
