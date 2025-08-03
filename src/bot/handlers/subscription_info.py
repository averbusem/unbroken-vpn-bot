from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import subscription_info_kb
from src.bot.states import UserStates
from src.bot.utils.datetime_formatter import format_utc_to_moscow
from src.core.subscription.service import SubscriptionService
from src.exceptions import SubscriptionNotActiveException, SubscriptionNotFoundException

router = Router()


@router.callback_query(F.data == "subscription_info")
async def subscription_info(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(UserStates.SUBSCRIPTION_INFO)
    user_id = callback.from_user.id
    service = SubscriptionService(session)

    try:
        info = await service.get_subscription_info(user_id)
    except SubscriptionNotFoundException:
        return await callback.message.edit_text(
            "У вас пока нет подписки.\n" "Вы можете оформить подписку через меню ниже.",
            reply_markup=subscription_info_kb(),
        )
    except SubscriptionNotActiveException:
        return await callback.message.edit_text(
            "Ваша подписка просрочена.\n" "Вы можете продлить подписку через меню ниже.",
            reply_markup=subscription_info_kb(),
        )

    end_datetime = format_utc_to_moscow(info["end_date"])
    text = (
        "🌐 Информация о подписке:\n\n"
        f"📆 Окончание: {end_datetime}\n"
        f"📱 Можно подключить устройств: {info['device_limit']}\n"
        f"🔑 Ключ: <code>{info['vpn_key']}</code>"
    )
    return await callback.message.edit_text(text, reply_markup=subscription_info_kb())
