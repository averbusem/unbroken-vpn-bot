from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.bot.keyboards import back_to_main_kb, trial_confirmation_kb
from src.bot.states import UserStates
from src.core.subscription.service import SubscriptionService
from src.db.database import session_factory

router = Router()


@router.callback_query(F.data == "trial")
async def trial(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Пробная подписка даётся один раз\n"
        "Вы уверены, что хотите активировать пробную подписку?",
        reply_markup=trial_confirmation_kb(),
    )
    await state.set_state(UserStates.TRIAL)


@router.callback_query(F.data == "get_trial", UserStates.TRIAL)
async def get_trial(callback: CallbackQuery, state: FSMContext):
    async with session_factory() as session:
        # TODO хранить часто испол данные в состояниях, например user id
        user_id = callback.from_user.id
        sub_service = SubscriptionService(session)
        sub, vpn_key = await sub_service.activate_trial(user_id)
        await session.commit()
        await callback.message.edit_text(
            "Подписка активирована\n" f"Ваш ключ доступа: {vpn_key}", reply_markup=back_to_main_kb()
        )
