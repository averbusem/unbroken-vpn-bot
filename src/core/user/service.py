import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.referral.repository import ReferralRepository
from src.core.subscription.service import SubscriptionService
from src.core.user.repository import UserRepository
from src.exceptions import ReferralAlreadyExist, SelfReferralException, SubscriptionAlreadyExist


class UserService:
    """
    Сервис для работы с пользователями:
    - создание нового пользователя
    - применение реферального кода
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.ref_repo = ReferralRepository(session)
        self.sub_service = SubscriptionService(session)

    async def start(self, user_id: int, username: str, ref_code: str | None):
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                user = await self.user_repo.create(user_id, username)

            bonus_applied = False
            if ref_code:
                bonus_applied = await self._apply_referral(user_id, ref_code)
            return user, bonus_applied

        except (SubscriptionAlreadyExist, SelfReferralException, ReferralAlreadyExist) as e:
            logging.info("Referral exception for user %s: %s", user_id, e)
            raise

        except Exception as e:
            logging.exception("Unhandled exception in UserService.start for user %s", user_id, e)
            raise

    async def _apply_referral(self, user_id: int, ref_code: str) -> bool:
        if await self.sub_service.sub_repo.get_by_user_id(user_id):
            raise SubscriptionAlreadyExist(f"User {user_id} already has subscription")

        referrer = await self.user_repo.get_by_referral_code(ref_code)
        if not referrer or referrer.id == user_id:
            raise SelfReferralException(f"Invalid referral code for user_id: {user_id}")

        if await self.ref_repo.get_by_referred_id(user_id):
            raise ReferralAlreadyExist(f"User {user_id} already has referral")

        referral = await self.ref_repo.create(referrer.id, user_id)
        await self.sub_service.apply_referral_bonus(referral)
        return True
