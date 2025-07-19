import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import back_to_main_kb, help_kb
from src.bot.texts import INSTRUCTION_TEXT
from src.bot.utils.decorators import remove_last_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("help"))
@router.callback_query(F.data == "help")
@remove_last_keyboard
async def show_help_menu(
    event: Message | CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    await state.clear()
    if isinstance(event, CallbackQuery):
        message = event.message
    else:
        message = event

    return await message.answer("Выберите раздел помощи:", reply_markup=help_kb())


@router.callback_query(F.data == "send_instruction")
async def send_instruction(
    callback: CallbackQuery,
):
    return await callback.message.edit_text(
        INSTRUCTION_TEXT,
        reply_markup=back_to_main_kb(),
    )


@router.callback_query(F.data == "send_support")
async def send_support(
    callback: CallbackQuery,
):
    # TODO: уточните контакт поддержки (email, Telegram-канал или группа)
    support_text = (
        "Для поддержки обратитесь: \n"
        "• По электронной почте: support@example.com\n"
        "• Telegram: @YourSupportBot"
    )
    await callback.message.edit_text(
        support_text,
        reply_markup=back_to_main_kb(),
    )
