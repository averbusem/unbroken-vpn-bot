import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.referral.repository import ReferralRepository
from src.core.user.repository import UserRepository
from src.exceptions import UserNotFoundException

logger = logging.getLogger(__name__)


class ReferralService:
    """
    Сервис для получения информации по реферальной программе.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ref_repo = ReferralRepository(session)
        self.user_repo = UserRepository(session)

    async def get_info(self, user_id: int, bot_username: str) -> dict:

        # Проверяем, что пользователь существует
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.info("UserNotFound in get_info for user %s", user_id)
            raise UserNotFoundException(f"User {user_id} not found")

        # Формируем ссылку
        ref_link = f"https://t.me/{bot_username}?start={user.referral_code}"

        # Получаем статистику
        referrals = await self.ref_repo.get_by_referrer_id(user_id)
        total = len(referrals)
        usernames: list[str] = []
        for ref in referrals:
            try:
                referred_user = await self.user_repo.get_by_id(ref.referred_id)
                if referred_user and referred_user.username:
                    usernames.append(f"@{referred_user.username}")
                else:
                    usernames.append(str(ref.referred_id))
            except Exception as e:
                logger.warning("Failed to fetch referred user %s: %s", ref.referred_id, e)
                usernames.append(str(ref.referred_id))

        return {"ref_link": ref_link, "total": total, "referred_usernames": usernames}
