from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.referral.models import Referral


class ReferralRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, referrer_id: int, referred_id: int) -> Referral:
        referral = Referral(referrer_id=referrer_id, referred_id=referred_id)
        self.session.add(referral)
        await self.session.flush()
        return referral

    async def get_by_referrer_id(self, referrer_id: int) -> list[Referral]:
        result = await self.session.execute(
            select(Referral).where(Referral.referrer_id == referrer_id)
        )
        return result.scalars().all()

    async def get_by_referred_id(self, referred_id: int) -> Referral | None:
        result = await self.session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return result.scalars().first()
