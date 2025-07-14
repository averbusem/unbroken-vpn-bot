from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.user.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_by_referral_code(self, code: str) -> User | None:
        result = await self.session.execute(select(User).where(User.referral_code == code))
        return result.scalars().first()

    async def create(self, id: int, username: str, ref_code: str) -> User:
        user = User(id=id, username=username, referral_code=ref_code)
        self.session.add(user)
        await self.session.flush()
        return user

    async def mark_trial_used(self, user: User) -> None:
        user.trial_used = True
        self.session.add(user)
        await self.session.flush()

    async def set_admin(self, user: User, is_admin: bool = True) -> None:
        user.is_admin = is_admin
        self.session.add(user)
        await self.session.flush()
