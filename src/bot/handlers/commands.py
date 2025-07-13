import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import back_to_main_kb, main_menu_kb
from src.bot.utils.decorators import remove_last_keyboard
from src.core.user.service import UserService
from src.exceptions import ReferralAlreadyExist, SelfReferralException, SubscriptionAlreadyExist

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
@remove_last_keyboard
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
    except SubscriptionAlreadyExist:
        return await message.answer(
            "У вас уже есть подписка, повторный реферальный бонус недоступен",
            reply_markup=back_to_main_kb(),
        )

    except SelfReferralException:
        return await message.answer(
            "Вы не можете использовать свою собственную реферальную ссылку",
            reply_markup=back_to_main_kb(),
        )

    except ReferralAlreadyExist:
        return await message.answer(
            "Вы уже использовали реферальную ссылку", reply_markup=back_to_main_kb()
        )

    except Exception:
        return await message.answer(
            "Ошибка, уже передали разработчикам", reply_markup=back_to_main_kb()
        )

    text = "Привет! Я бот для управления подпиской VPN"
    if bonus:
        text += "\nПоздравляем! Вы получили реферальный бонус"

    return await message.answer(text, reply_markup=main_menu_kb(user.trial_used))


# from src.core.subscription.jobs import run_all_deactivations, run_all_notifications
# @router.message(F.text == "test")
# async def test_jobs_handler(message: Message):
#     """
#     Тестовый хендлер: запускает все задачи уведомлений и деактивации
#     по префиксам notify_ и deactivate_.
#     """
#     await run_all_notifications()
#     await run_all_deactivations()
#     await message.answer("✅ Все тестовые задачи выполнены!")
