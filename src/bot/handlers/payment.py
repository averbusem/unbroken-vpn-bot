from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import back_to_main_kb, tariff_selection_kb
from src.bot.states import UserStates
from src.bot.utils.datetime_formatter import format_utc_to_moscow
from src.bot.utils.decorators import remove_last_keyboard
from src.config import settings
from src.core.payment.service import PaymentService
from src.core.tariff.repository import TariffRepository
from src.exceptions import TariffNotFoundException

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
    user_id = callback.from_user.id
    tariff_id = int(callback.data.split("_")[1])
    pay_service = PaymentService(session)
    try:
        invoice_data = await pay_service.create_invoice(user_id=user_id, tariff_id=tariff_id)
    except TariffNotFoundException:
        return await callback.message.answer(
            "Выбранный тариф не найден. Пожалуйста, попробуйте ещё раз.",
            reply_markup=back_to_main_kb(),
        )
    labeled_price = LabeledPrice(
        label=invoice_data["label"],
        amount=int(invoice_data["amount"] * 100),
    )
    await state.update_data(payment_id=invoice_data["payment_id"])
    await state.set_state(UserStates.SUCCESSFUL_PAYMENT)
    return await callback.message.answer_invoice(
        title="Покупка VPN-подписки",
        description=invoice_data["label"],
        payload=invoice_data["payload"],
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
    payment_id = data.get("payment_id")
    service = PaymentService(session)

    try:
        action, end_datetime_utc, key = await service.process_success(
            payment_id,
            message.successful_payment.telegram_payment_charge_id,
            message.successful_payment.provider_payment_charge_id,
        )
    except TariffNotFoundException:
        return await message.answer(
            "Тариф не найден. Обратитесь в поддержку.",
            reply_markup=back_to_main_kb(),
        )

    # Ответ пользователю
    end_datetime = format_utc_to_moscow(end_datetime_utc)
    return await message.answer(
        f"✅ Ваша подписка {action} успешно!\n"
        f"📆 Окончание: {end_datetime}\n"
        f"🔑 Ваш VPN-ключ: <code>{key}</code>",
        reply_markup=back_to_main_kb(),
    )
