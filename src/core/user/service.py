import logging
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.referral.repository import ReferralRepository
from src.core.subscription.service import SubscriptionService
from src.core.user.repository import UserRepository
from src.exceptions import (
    ReferralAlreadyExistException,
    ReferralCodeGenerationException,
    SelfReferralException,
    ServiceException,
    SubscriptionAlreadyExistException,
)

logger = logging.getLogger(__name__)


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
                code = await self._generate_unique_referral_code()
                user = await self.user_repo.create(user_id, username, code)

            bonus_applied = False
            if ref_code:
                bonus_applied = await self._apply_referral(user_id, ref_code)
            return user, bonus_applied

        except (
            SubscriptionAlreadyExistException,
            SelfReferralException,
            ReferralAlreadyExistException,
        ):
            raise
        # чтобы избежать двойное логирование
        # т.к. сервис self.sub_service.apply_referral_bonus(referral)
        # так же при неожиданной ошибке выкинет ServiceException
        except (ServiceException, ReferralCodeGenerationException):
            raise
        except Exception as e:
            logger.exception(f"Unhandled exception in UserService.start for user {user_id}: {e}")
            raise ServiceException(f"Failed to start user {user_id}: {str(e)}")

    async def _apply_referral(self, user_id: int, ref_code: str) -> bool:
        existing_sub = await self.sub_service.sub_repo.get_by_user_id(user_id)
        if existing_sub:
            logger.info(
                f"Referral blocked - user {user_id} already has subscription id={existing_sub.id}"
            )
            raise SubscriptionAlreadyExistException(f"User {user_id} already has subscription")

        referrer = await self.user_repo.get_by_referral_code(ref_code)
        if not referrer or referrer.id == user_id:
            logger.info(f"Referral code {ref_code} not found for user {user_id}")
            raise SelfReferralException(f"Invalid referral code for user_id: {user_id}")

        existing_referral = await self.ref_repo.get_by_referred_id(user_id)
        if existing_referral:
            logger.info(
                f"User {user_id} already used ref code referrer: {existing_referral.referrer_id}"
            )
            raise ReferralAlreadyExistException(f"User {user_id} already used referral code")

        referral = await self.ref_repo.create(referrer.id, user_id)
        await self.sub_service.apply_referral_bonus(referral)
        return True

    async def _generate_unique_referral_code(self) -> str:
        for _ in range(5):
            code = secrets.token_urlsafe(6)  # 8 символов
            exists = await self.user_repo.get_by_referral_code(code)
            if not exists:
                return code
        # после 5 неудачных попыток
        logger.warning("Failed to generate unique referral code after 5 attempts")
        raise ReferralCodeGenerationException(
            "Failed to generate unique referral code after 5 attempts"
        )
