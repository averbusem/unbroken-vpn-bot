from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import back_to_main_kb, trial_confirmation_kb
from src.bot.states import UserStates
from src.bot.texts import INSTRUCTION_TEXT
from src.bot.utils.datetime_formatter import format_days_string, format_utc_to_moscow
from src.core.subscription.service import SubscriptionService
from src.core.tariff.repository import TariffRepository

router = Router()


@router.callback_query(F.data == "trial")
async def trial(callback: CallbackQuery, state: FSMContext, session: AsyncSession):

    trial_tariff = await TariffRepository(session).get_by_name("trial")
    if not trial_tariff:
        return await callback.message.edit_text(
            "Ошибка: пробный тариф не настроен. Обратитесь в поддержку.",
            reply_markup=back_to_main_kb(),
        )

    days = trial_tariff.duration_days
    days_string = format_days_string(days)
    text = f"🎁 Вы можете получить бесплатный пробный доступ к VPN на {days_string}."

    await state.set_state(UserStates.TRIAL)
    return await callback.message.edit_text(
        text,
        reply_markup=trial_confirmation_kb(),
    )


@router.callback_query(F.data == "get_trial", UserStates.TRIAL)
async def get_trial(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback.from_user.id
    sub_service = SubscriptionService(session)
    sub, vpn_key = await sub_service.activate_trial(user_id)
    end_datetime = format_utc_to_moscow(sub.end_date)
    await callback.message.edit_text(
        "✅ Пробная подписка активирована успешно\n"
        f"📆 Окончание: {end_datetime}\n"
        f"🔑 Ваш VPN-ключ: <code>{vpn_key}</code>\n\n\n" + INSTRUCTION_TEXT,
        reply_markup=back_to_main_kb(),
    )
