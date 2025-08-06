from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import main_menu_kb
from src.core.user.repository import UserRepository

router = Router()


@router.callback_query(F.data == "back_to_main")
async def main_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()

    user_id = callback.from_user.id
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    return await callback.message.edit_text(
        "<b>Внимание!</b>\n"
        "Этот бот — учебный пет-проект и не предназначен для реальной эксплуатации.\n"
        "Главное меню:",
        reply_markup=main_menu_kb(user.trial_used),
    )
