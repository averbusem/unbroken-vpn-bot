import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.referral.models import Referral
from src.core.subscription.models import Subscription
from src.core.subscription.repository import SubscriptionRepository
from src.core.subscription.scheduler import scheduler
from src.core.tariff.repository import TariffRepository
from src.core.user.repository import UserRepository
from src.db.database import session_factory
from src.outline.service import OutlineManager


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self.sub_repo = SubscriptionRepository(session)
        self.user_repo = UserRepository(session)
        self.tariff_repo = TariffRepository(session)
        self.outline = OutlineManager()
        self.scheduler = scheduler

    async def create_subscription(
        self,
        user_id: int,
        tariff_id: int,
    ) -> tuple[Subscription, str]:
        # Получаем тариф
        tariff = await self.tariff_repo.get_by_id(tariff_id)
        if not tariff:
            raise ValueError("Tariff not found")

        # Создаем ключ в Outline
        # TODO outline_key = await self.outline.create_key(name=f"user_{user_id}")
        outline_key = {
            "id": f"temp_outline_key_id_{user_id}",
            "accessUrl": f"temp_vpn_key_{user_id}",
        }
        # Рассчитываем дату окончания
        end_date = datetime.now(timezone.utc) + timedelta(days=tariff.duration_days)

        # Создаем подписку
        subscription = await self.sub_repo.create(
            user_id=user_id,
            tariff_id=tariff_id,
            vpn_key=outline_key["accessUrl"],
            outline_key_id=outline_key["id"],
            end_date=end_date,
        )

        # Планируем деактивацию
        self.schedule_deactivation(subscription.id, end_date)
        self.schedule_notification(subscription.id, end_date - timedelta(days=3))

        return subscription, outline_key["accessUrl"]

    async def extend_subscription(
        self, subscription: Subscription, tariff_id: int
    ) -> tuple[Subscription, str]:
        tariff = await self.tariff_repo.get_by_id(tariff_id)
        if not tariff:
            raise ValueError("Tariff not found")

        now = datetime.now(timezone.utc)

        # Если подписка активна - продлеваем от текущей даты окончания
        if subscription.is_active and subscription.end_date > now:
            new_end_date = subscription.end_date + timedelta(days=tariff.duration_days)
            await self.sub_repo.update_end_date(subscription, new_end_date)
            key = subscription.vpn_key
        else:
            # Для неактивной подписки создаем новый ключ
            # TODO outline_key = await self.outline.create_key(name=f"user_{subscription.user_id}")
            outline_key = {
                "id": f"temp_outline_key_id_{subscription.user_id}",
                "accessUrl": f"temp_vpn_key_{subscription.user_id}",
            }
            new_end_date = now + timedelta(days=tariff.duration_days)

            # Обновляем подписку
            await self.sub_repo.update(
                subscription,
                vpn_key=outline_key["accessUrl"],
                outline_key_id=outline_key["id"],
                end_date=new_end_date,
                is_active=True,
            )
            key = outline_key["accessUrl"]
        # Перепланируем деактивацию (даже если ее не было)
        self.reschedule_deactivation(subscription.id, new_end_date)
        self.reschedule_notification(subscription.id, new_end_date - timedelta(days=3))
        await self.sub_repo.increment_payments(subscription)

        return subscription, key

    def schedule_deactivation(self, sub_id: int, end_date: datetime):
        job_id = f"deactivate_{sub_id}"
        self.scheduler.add_job(
            self.deactivate_subscription, "date", run_date=end_date, args=[sub_id], id=job_id
        )

    def schedule_notification(self, sub_id: int, notify_date: datetime):
        job_id = f"notify_{sub_id}"
        self.scheduler.add_job(
            self.send_notification, "date", run_date=notify_date, args=[sub_id], id=job_id
        )

    def reschedule_deactivation(self, sub_id: int, new_end_date: datetime):
        job_id = f"deactivate_{sub_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        self.schedule_deactivation(sub_id, new_end_date)

    def reschedule_notification(self, sub_id: int, new_notify_date: datetime):
        job_id = f"notify_{sub_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        self.schedule_notification(sub_id, new_notify_date)

    async def deactivate_subscription(self, sub_id: int):
        async with session_factory() as session:
            repo = SubscriptionRepository(session)
            sub = await repo.get_by_id(sub_id)
            if sub and sub.is_active:
                # Удаляем ключ в Outline
                if sub.outline_key_id:
                    try:
                        # TODO await self.outline.delete_key(str(sub.outline_key_id))
                        pass
                    except Exception as e:
                        logging.error(f"Error deleting Outline key: {str(e)}")

                # Деактивируем подписку и очищаем ключи
                await repo.update(sub, vpn_key="", outline_key_id="", is_active=False)
                await session.commit()

    async def send_notification(self, sub_id: int):
        from src.bot import bot

        async with session_factory() as session:
            repo = SubscriptionRepository(session)
            sub = await repo.get_by_id(sub_id)
            if sub and sub.is_active:
                try:
                    await bot.send_message(
                        sub.user_id,
                        "Ваша подписка закончится через 3 дня. "
                        "Продлите ее, чтобы оставаться на связи!",
                    )
                except Exception as e:
                    logging.error(f"Failed to send notification: {e}")

    async def activate_trial(self, user_id: int) -> tuple[Subscription, str]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if user.trial_used:
            raise PermissionError("Trial already used")

        # Используем специальный тариф для пробного периода
        trial_tariff = await self.tariff_repo.get_by_name("trial")
        if not trial_tariff:
            raise ValueError("Trial tariff not configured")

        sub, key = await self.create_subscription(user_id, trial_tariff.id)
        await self.user_repo.mark_trial_used(user)
        self.schedule_deactivation(sub.id, sub.end_date)
        self.schedule_notification(sub.id, sub.end_date - timedelta(days=3))
        return sub, key

    async def apply_referral_bonus(self, referral: Referral) -> None:
        """
        Начисляет бонусы:
        - приглашённому:выдаём 14 дней : trial_tariff.duration_days + referral_bonus_days
        - пригласившему: +7 дней к текущей подписке
        Перепланируем задачи для деактивации и уведомления.
        """
        now = datetime.now(timezone.utc)
        try:
            # === Приглашённый ===
            # Если подписки нет — выдаём 14 дней (7 пробных + 7 за реф)
            trial_tariff = await self.tariff_repo.get_by_name("trial")
            if not trial_tariff:
                raise RuntimeError("Trial tariff not configured in the database")
            referral_bonus_days = referral.bonus_days

            end_date = now + timedelta(days=trial_tariff.duration_days + referral_bonus_days)
            # TODO outline_key = await self.outline.create_key(name=f"user_{subscription.user_id}")
            outline_key = {
                "id": f"temp_outline_key_id_{referral.referrer_id}",
                "accessUrl": f"temp_vpn_key_{referral.referrer_id}",
            }
            new_sub = await self.sub_repo.create(
                user_id=referral.referred_id,
                tariff_id=trial_tariff.id,
                vpn_key=outline_key["accessUrl"],
                outline_key_id=outline_key["id"],
                end_date=end_date,
            )
            await self.user_repo.mark_trial_used(referral.referred)
            # Планируем задачи для подписки приглашённого
            self.reschedule_deactivation(new_sub.id, end_date)
            self.reschedule_notification(new_sub.id, end_date - timedelta(days=3))
            logging.info(f"Applied 14-day bonus to referred user {referral.referred_id}")

        except Exception as e:
            logging.error(f"Error applying bonus to referred user {referral.referred_id}: {e}")

        # === Пригласивший ===
        # TODO а что делать если у пригласившего нет подписки
        try:
            referrer_sub = await self.sub_repo.get_by_user_id(referral.referrer_id)
            if referrer_sub:
                # Продлеваем на 7 дней от текущей даты или окончания подписки (что позже)
                end_date = max(referrer_sub.end_date, now) + timedelta(days=7)
                await self.sub_repo.update_end_date(referrer_sub, end_date)
            else:
                # Нет подписки — создаём пробную 7 дней + 7 за реф
                trial = await self.tariff_repo.get_by_name("trial")
                referral_bonus_days = referral.bonus_days
                end_date = now + timedelta(days=trial.duration_days + referral_bonus_days)

                # TODO outline_key = await self.outline.create_key(name=f"user_{subscription.user_id}")  # noqa
                outline_key = {
                    "id": f"temp_outline_key_id_{referral.referrer_id}",
                    "accessUrl": f"temp_vpn_key_{referral.referrer_id}",
                }
                await self.sub_repo.create(
                    user_id=referral.referrer_id,
                    tariff_id=trial.id,
                    vpn_key=outline_key["accessUrl"],
                    outline_key_id=outline_key["id"],
                    end_date=end_date,
                )
            # Планируем задачи для подписки пригласившего
            self.reschedule_deactivation(referrer_sub.id, end_date)
            self.reschedule_notification(referrer_sub.id, end_date - timedelta(days=3))
            logging.info(f"Applied 7-day bonus to referrer user {referral.referrer_id}")

        except Exception as e:
            logging.error(f"Error applying bonus to referrer user {referral.referrer_id}: {e}")
