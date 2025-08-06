from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import back_to_main_kb, main_menu_kb
from src.core.user.service import UserService
from src.exceptions import (
    ReferralAlreadyExistException,
    SelfReferralException,
    SubscriptionAlreadyExistException,
)

router = Router()


@router.message(CommandStart())
async def start_cmd(
    message: Message, state: FSMContext, command: CommandStart, session: AsyncSession
):
    await state.clear()
    ref_code = (command.args or "").strip() or None
    user_service = UserService(session)
    try:
        user, bonus = await user_service.start(
            user_id=message.from_user.id,
            username=message.from_user.username or "",
            ref_code=ref_code,
        )
    except SubscriptionAlreadyExistException:
        return await message.answer(
            "У вас уже есть подписка, повторный реферальный бонус недоступен.",
            reply_markup=back_to_main_kb(),
        )

    except SelfReferralException:
        return await message.answer(
            "Вы не можете использовать свою собственную реферальную ссылку.",
            reply_markup=back_to_main_kb(),
        )

    except ReferralAlreadyExistException:
        return await message.answer(
            "Вы уже использовали реферальную ссылку.", reply_markup=back_to_main_kb()
        )

    text = (
        "<b>Внимание!</b>\n"
        "Этот бот — учебный пет-проект и не предназначен для реальной эксплуатации.\n"
        "Привет! Я бот для управления подпиской VPN.\n"
    )

    if bonus:
        await message.answer(text)
        return await message.answer(
            "Поздравляем! Вы получили 14 дней бесплатной подписки.",
            reply_markup=main_menu_kb(user.trial_used),
        )

    return await message.answer(text, reply_markup=main_menu_kb(user.trial_used))


# from src.core.subscription.jobs import run_all_deactivations, run_all_notifications
# from aiogram import F
#
# @router.message(F.text == "test")
# async def test_jobs_handler(message: Message):
#     """
#     Тестовый хендлер: запускает все задачи уведомлений и деактивации
#     по префиксам notify_ и deactivate_.
#     """
#     await run_all_notifications()
#     await run_all_deactivations()
#     await message.answer("✅ Все тестовые задачи выполнены!")
