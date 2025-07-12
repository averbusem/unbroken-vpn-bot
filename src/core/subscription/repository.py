from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.subscription.models import Subscription


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: int, tariff_id: int, vpn_key: str, outline_key_id: str, end_date: datetime
    ) -> Subscription:
        sub = Subscription(
            user_id=user_id,
            tariff_id=tariff_id,
            vpn_key=vpn_key,
            outline_key_id=outline_key_id,
            end_date=end_date,
        )
        self.session.add(sub)
        await self.session.flush()
        return sub

    async def get_by_user_id(self, user_id: int) -> Subscription | None:
        query = select(Subscription).where(Subscription.user_id == user_id)
        subscription = await self.session.execute(query)
        return subscription.scalars().first()

    async def get_by_id(self, sub_id: int) -> Subscription | None:
        query = select(Subscription).where(Subscription.id == sub_id)
        subscription = await self.session.execute(query)
        return subscription.scalars().first()

    async def get_active(self) -> Sequence[Subscription]:
        query = select(Subscription).where(
            Subscription.is_active,
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_end_date(self, sub: Subscription, new_date: datetime) -> None:
        sub.end_date = new_date
        self.session.add(sub)
        await self.session.flush()

    async def increment_payments(self, sub: Subscription) -> None:
        sub.cnt_payments += 1
        self.session.add(sub)
        await self.session.flush()

    async def deactivate(self, sub: Subscription) -> None:
        sub.is_active = False
        self.session.add(sub)
        await self.session.flush()

    async def update(
        self,
        subscription: Subscription,
        *,
        vpn_key: str | None = None,
        outline_key_id: str | None = None,
        end_date: datetime | None = None,
        is_active: bool | None = None,
    ) -> None:
        if vpn_key is not None:
            subscription.vpn_key = vpn_key
        if outline_key_id is not None:
            subscription.outline_key_id = outline_key_id
        if end_date is not None:
            subscription.end_date = end_date
        if is_active is not None:
            subscription.is_active = is_active

        self.session.add(subscription)
        await self.session.flush()
