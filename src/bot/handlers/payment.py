import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import back_to_main_kb, tariff_selection_kb
from src.bot.states import UserStates
from src.bot.utils.datetime_formatter import format_utc_to_moscow
from src.bot.utils.decorators import remove_last_keyboard
from src.config import settings
from src.core.subscription.service import SubscriptionService
from src.core.tariff.repository import TariffRepository

router = Router()


@router.callback_query(F.data == "select_tariff")
async def select_tariff(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    tariff_repo = TariffRepository(session)
    tariffs = await tariff_repo.get_all_active()
    await state.set_state(UserStates.CREATE_PAYMENT)
    return await callback.message.edit_text(
        "Выберите тариф для покупки/продления:", reply_markup=tariff_selection_kb(tariffs)
    )


@router.callback_query(F.data.startswith("tariff_"), UserStates.CREATE_PAYMENT)
@remove_last_keyboard
async def create_payment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    tariff_id = int(callback.data.split("_")[1])

    tariff_repo = TariffRepository(session)
    tariff = await tariff_repo.get_by_id(tariff_id)
    if not tariff:
        await callback.message.answer("Тариф не найден", reply_markup=back_to_main_kb(False))
        return
    await state.update_data(tariff_id=tariff_id)

    labeled_price = LabeledPrice(
        label=f"{tariff.duration_days} дней — {tariff.price}₽", amount=int(tariff.price * 100)
    )

    payload = f"{callback.from_user.id}:{tariff_id}:{int(time.time())}"
    await state.set_state(UserStates.SUCCESSFUL_PAYMENT)
    return await callback.message.answer_invoice(
        title="Покупка VPN-подписки",
        description=f"{tariff.duration_days}-дневный доступ к VPN",
        payload=payload,
        provider_token=settings.PAYMASTER_MERCHANT_ID,
        currency="RUB",
        prices=[labeled_price],
    )


@router.pre_checkout_query(lambda q: True)
async def pre_checkout(query: PreCheckoutQuery):
    # Подтверждаем переходим к оплате
    await query.answer(ok=True)


@router.message(F.content_type == "successful_payment", UserStates.SUCCESSFUL_PAYMENT)
@remove_last_keyboard
async def successful_payment(message: Message, state: FSMContext, session: AsyncSession):
    """
    После успешной оплаты создаём или продлеваем подписку.
    """
    data = await state.get_data()
    tariff_id = data.get("tariff_id")
    user_id = message.from_user.id

    sub_service = SubscriptionService(session)
    # проверим есть ли активная подписка
    from src.core.subscription.repository import SubscriptionRepository

    sub_repo = SubscriptionRepository(session)
    existing = await sub_repo.get_by_user_id(user_id)

    if existing:
        subscription, key = await sub_service.extend_subscription(existing, tariff_id)
        action = "продлена"
    else:
        subscription, key = await sub_service.create_subscription(user_id, tariff_id)
        action = "оформлена"

    # Ответ пользователю
    end_datetime = format_utc_to_moscow(subscription.end_date)
    return await message.answer(
        f"✅ Ваша подписка {action} успешно!\n"
        f"🔑 Ваш VPN-ключ: <code>{key}</code>\n"
        f"📆 Действительна до: {end_datetime}",
        reply_markup=back_to_main_kb(),
    )
