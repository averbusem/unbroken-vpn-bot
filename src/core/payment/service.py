import logging
from time import time
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payment.models import PaymentStatus
from src.core.payment.repository import PaymentRepository
from src.core.subscription.service import SubscriptionService
from src.core.tariff.repository import TariffRepository
from src.db.database import session_factory
from src.exceptions import PaymentNotFoundException, TariffNotFoundException

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tariff_repo = TariffRepository(session)
        self.sub_service = SubscriptionService(session)

    async def create_invoice(
        self,
        user_id: int,
        tariff_id: int,
    ) -> Dict[str, Any]:
        try:
            tariff = await self.tariff_repo.get_by_id(tariff_id)
            if not tariff:
                logger.warning("User %s request non-existent tariff %s", user_id, tariff_id)
                raise TariffNotFoundException
            amount = int(tariff.price)
            payload = f"{user_id}_{tariff_id}_{int(time())}"

            # Создание отдельной сессии и коммита чтобы точно создать потенциальный платеж
            async with session_factory() as pay_sess:
                pay_repo = PaymentRepository(pay_sess)
                payment = await pay_repo.create(
                    user_id=user_id, tariff_id=tariff_id, invoice_payload=payload, amount=amount
                )
                await pay_sess.commit()
                logger.info(
                    "Create invoice %s for user %s: tariff=%s amount=%s",
                    payment.id,
                    user_id,
                    tariff_id,
                    amount,
                )
            return {
                "payment_id": payment.id,
                "payload": payload,
                "amount": amount,
                "duration_days": tariff.duration_days,
                "label": f"{tariff.duration_days} дн. — {tariff.price}₽",
            }
        except TariffNotFoundException:
            raise

    async def process_success(
        self,
        payment_id: int,
        telegram_charge_id: str,
        provider_charge_id: str,
    ):
        """
        Обрабатывает успешный платеж по payment_id: обновляет статус, создает/продлевает подписку.
        Возвращает (action, end_datetime, vpn_key).
        """
        try:
            # Создание отдельной сессии для успешного платежа (иначе в middleware может быть откат)
            async with session_factory() as pay_sess:
                pay_repo = PaymentRepository(pay_sess)
                payment = await pay_repo.get_by_id(payment_id)
                if not payment:
                    logger.error("Payment not found: id=%s", payment_id)
                    raise PaymentNotFoundException(f"Payment {payment_id} not found")
                await pay_repo.update_status(
                    payment,
                    PaymentStatus.SUCCESS,
                    telegram_charge_id=telegram_charge_id,
                    provider_charge_id=provider_charge_id,
                )
                await pay_sess.commit()
                logger.info("Payment marked SUCCESS: id=%s", payment.id)

            user_id = payment.user_id
            tariff_id = payment.tariff_id
            existing = await self.sub_service.sub_repo.get_by_user_id(user_id)

            if existing:
                sub, key = await self.sub_service.extend_subscription(existing, tariff_id)
                action = "продлена"
                end_datetime = sub.end_date
                logger.info(
                    "Subscription extended: id=%s user=%s payment=%s",
                    sub.id,
                    user_id,
                    payment.id,
                )
            else:
                sub, key = await self.sub_service.create_subscription(user_id, tariff_id)
                action = "оформлена"
                end_datetime = sub.end_date
                logger.info(
                    "Subscription created: id=%s user=%s payment=%s",
                    sub.id,
                    user_id,
                    payment.id,
                )

            return action, end_datetime, key
        except (PaymentNotFoundException,):
            raise
