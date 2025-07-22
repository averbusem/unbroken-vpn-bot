import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import back_to_main_kb, referral_info_kb
from src.core.referral.service import ReferralService
from src.exceptions import UserNotFoundException

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "ref_program")
async def referral_info(callback: CallbackQuery, session: AsyncSession):
    bot_username = (await callback.bot.get_me()).username
    ref_service = ReferralService(session)

    try:
        info = await ref_service.get_info(callback.from_user.id, bot_username)
    except UserNotFoundException:
        return await callback.message.answer(
            "Пользователь не найден", reply_markup=back_to_main_kb()
        )

    text = (
        "Приглашайте друзей и получайте бонусы!\n\n"
        f"🔗 Ваша реферальная ссылка: <code>{info['ref_link']}</code>\n\n"
        "📊 Ваша статистика:\n"
        f"Всего приглашенных: {info['total']}\n"
    )

    if info["referred_usernames"]:
        text += "Список рефералов:\n"
        text += "\n".join(f"{username}" for username in info["referred_usernames"])
        text += "\n"

    text += "\n🎁 Вы получаете +7 дней к подписке, а приглашенный человек 14 дней!"

    return await callback.message.edit_text(text, reply_markup=referral_info_kb())
