from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.bot.keyboards import main_menu_kb
from src.core.user.repository import UserRepository
from src.db.database import session_factory

router = Router()


@router.callback_query(F.data == "back_to_main")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    async with session_factory() as session:
        user_id = callback.from_user.id
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        await callback.message.edit_text(
            "Главное меню:", reply_markup=main_menu_kb(user.trial_used)
        )
