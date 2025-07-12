from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.bot.keyboards import subscription_info_kb
from src.bot.states import UserStates
from src.core.subscription.repository import SubscriptionRepository
from src.db.database import session_factory

router = Router()


@router.callback_query(F.data == "subscription_info")
async def subscription_info(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.SUBSCRIPTION_INFO)
    async with session_factory() as session:
        sub_repo = SubscriptionRepository(session)
        sub = await sub_repo.get_by_user_id(callback.from_user.id)
        end_date = sub.end_date.strftime("%d.%m.%Y %H:%M")
        text = (
            "🌐 Информация о подписке:\n"
            f"📆 Окончание: {end_date}\n"
            "📱 Можно подключить устройств: 3\n"
            f"🔑 Ключ: {sub.vpn_key}"
        )
        await callback.message.edit_text(text, reply_markup=subscription_info_kb())
