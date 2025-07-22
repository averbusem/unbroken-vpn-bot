from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payment.models import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: int, tariff_id: int, amount: int, invoice_payload: str
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            tariff_id=tariff_id,
            amount=amount,
            invoice_payload=invoice_payload,
        )
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def update_status(
        self,
        payment: Payment,
        status: PaymentStatus,
        telegram_charge_id: str,
        provider_charge_id: str,
    ) -> None:
        payment.status = status
        payment.telegram_payment_charge_id = telegram_charge_id
        payment.provider_payment_charge_id = provider_charge_id
        payment.completed_at = datetime.now(timezone.utc)

        self.session.add(payment)
        await self.session.flush()

    async def get_by_payload(self, payload: str) -> Payment | None:
        query = select(Payment).where(Payment.invoice_payload == payload)
        payment = await self.session.execute(query)
        return payment.scalar_one_or_none()

    async def get_by_id(self, id: int):
        query = select(Payment).where(Payment.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
