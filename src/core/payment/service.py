import logging
from time import time
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payment.models import PaymentStatus
from src.core.payment.repository import PaymentRepository
from src.core.subscription.service import SubscriptionService
from src.core.tariff.repository import TariffRepository
from src.database import session_factory
from src.exceptions import (
    PaymentException,
    PaymentNotFoundException,
    ServiceException,
    TariffNotFoundException,
)

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
        """
        Создает инвойс для платежа.

        Args:
            user_id: ID пользователя
            tariff_id: ID тарифа

        Returns:
            Dict: Данные инвойса

        Raises:
            TariffNotFoundException: Если тариф не найден
            PaymentException: При других ошибках создания инвойса
        """
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
        except Exception as e:
            logger.exception(f"Unhandled exception in create_invoice for user {user_id}: {e}")
            raise PaymentException(f"Failed to create invoice for user {user_id}: {str(e)}")

    async def process_success(
        self,
        payment_id: int,
        telegram_charge_id: str,
        provider_charge_id: str,
    ):
        """
        Обрабатывает успешный платеж по payment_id: обновляет статус, создает/продлевает подписку.

        Args:
            payment_id: ID платежа
            telegram_charge_id: ID платежа в Telegram
            provider_charge_id: ID платежа у провайдера

        Returns:
            tuple: (action, end_datetime, vpn_key)

        Raises:
            PaymentNotFoundException: Если платеж не найден
            TariffNotFoundException: Если тариф не найден при создании подписки
            PaymentException: При других ошибках обработки платежа
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

            sub, key = await self.sub_service.create_or_extend_subscription(user_id, tariff_id)

            existing_sub = await self.sub_service.sub_repo.get_by_user_id(user_id)
            action = "продлена" if existing_sub else "создана"

            return action, sub.end_date, key

        except (PaymentNotFoundException, TariffNotFoundException):
            raise
        except ServiceException:
            raise
        except Exception as e:
            logger.exception(
                f"Unhandled exception in process_success for payment {payment_id}: {e}"
            )
            raise PaymentException(f"Failed to process successful payment {payment_id}: {str(e)}")
