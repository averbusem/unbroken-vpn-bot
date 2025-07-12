import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.keyboards import main_menu_kb
from src.core.referral.repository import ReferralRepository
from src.core.subscription.jobs import run_all_deactivations, run_all_notifications
from src.core.subscription.repository import SubscriptionRepository
from src.core.subscription.service import SubscriptionService
from src.core.user.repository import UserRepository
from src.db.database import session_factory

router = Router()
logger = logging.getLogger(__name__)


async def process_referral(session, user, ref_code, message):
    """
    Обработать реферальный код для нового пользователя без подписки.
    """
    sub_repo = SubscriptionRepository(session)
    if await sub_repo.get_by_user_id(user.id):
        await message.answer(
            "У вас уже есть подписка, повторный реферальный бонус недоступен.",
        )
        return

    ref_repo = ReferralRepository(session)
    referrer = await UserRepository(session).get_by_referral_code(ref_code)
    if not referrer or referrer.id == user.id:
        await message.answer(
            "Неверная реферальная ссылка.",
        )
        return

    if await ref_repo.get_by_referred_id(user.id):
        await message.answer(
            "Вы уже использовали реферальный код.",
        )
        return

    referral = await ref_repo.create(referrer.id, user.id)
    sub_service = SubscriptionService(session)
    await sub_service.apply_referral_bonus(referral)

    await message.answer(
        "Поздравляем! Вы получили реферальный бонус на подписку.",
    )


@router.message(CommandStart())
async def start_cmd(message: Message, command: CommandStart, state: FSMContext):
    await state.clear()

    async with session_factory() as session:
        user_repo = UserRepository(session)
        # Создание пользователя
        user = await user_repo.get_by_id(message.from_user.id)
        if not user:
            user = await user_repo.create(
                id=message.from_user.id, username=message.from_user.username
            )

        # Обработка реферального кода
        ref_code = (command.args or "").strip()
        if ref_code:
            await process_referral(session, user, ref_code, message)

        await session.commit()

    # Переход в главное меню
    await message.answer(
        "Привет! Я бот для управления подпиской VPN. Выберите действие:",
        reply_markup=main_menu_kb(user.trial_used),
    )


@router.message(F.text == "test")
async def test_jobs_handler(message: Message):
    """
    Тестовый хендлер: запускает все задачи уведомлений и деактивации
    по префиксам notify_ и deactivate_.
    """
    await run_all_notifications()
    await run_all_deactivations()
    await message.answer("✅ Все тестовые задачи выполнены!")
