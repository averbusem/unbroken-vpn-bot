import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.referral.models import Referral
from src.core.subscription.jobs import (
    reschedule_deactivation,
    reschedule_notification,
    schedule_deactivation,
    schedule_notification,
)
from src.core.subscription.models import Subscription
from src.core.subscription.repository import SubscriptionRepository
from src.core.tariff.repository import TariffRepository
from src.core.user.repository import UserRepository
from src.exceptions import (
    ServiceException,
    SubscriptionException,
    SubscriptionNotActiveException,
    SubscriptionNotFoundException,
    TariffNotFoundException,
    TrialAlreadyUsedException,
    UserNotFoundException,
)
from src.outline.service import OutlineManager

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Сервис для управления подписками пользователей.

    Обеспечивает создание, продление, деактивацию подписок,
    управление VPN ключами и планирование задач.
    """

    def __init__(self, session: AsyncSession):
        self.sub_repo = SubscriptionRepository(session)
        self.user_repo = UserRepository(session)
        self.tariff_repo = TariffRepository(session)
        self.outline = OutlineManager()

    async def create_or_extend_subscription(
        self, user_id: int, tariff_id: int
    ) -> tuple[Subscription, str]:
        """
        Создает новую подписку или продлевает существующую.

        Args:
            user_id: ID пользователя
            tariff_id: ID тарифа

        Returns:
            tuple: (subscription, vpn_key)

        Raises:
            TariffNotFoundException: Если тариф не найден
            SubscriptionException: При других ошибках сервиса
        """
        try:
            existing_sub = await self.sub_repo.get_by_user_id(user_id)

            if existing_sub:
                sub, key = await self._extend_subscription(existing_sub, tariff_id)
                logger.info(f"Extended subscription {sub.id} for user {user_id}")
            else:
                sub, key = await self._create_subscription(user_id, tariff_id)
                logger.info(f"Created subscription {sub.id} for user {user_id}")

            return sub, key

        except TariffNotFoundException:
            raise
        except Exception as e:
            logger.exception(
                f"Unhandled exception in create_or_extend_subscription for user {user_id}: {e}"
            )
            raise SubscriptionException(
                f"Failed to create or extend subscription for user {user_id}: {str(e)}"
            )

    async def _create_subscription(
        self,
        user_id: int,
        tariff_id: int,
    ) -> tuple[Subscription, str]:
        """
        Создает новую подписку для пользователя.

        Args:
            user_id: ID пользователя
            tariff_id: ID тарифа

        Returns:
            tuple: (subscription, vpn_key)

        Raises:
            TariffNotFoundException: Если тариф не найден
        """
        # Получаем тариф
        tariff = await self.tariff_repo.get_by_id(tariff_id)
        if not tariff:
            logger.info(f"Tariff {tariff_id} not found for user {user_id}")
            raise TariffNotFoundException("Tariff not found")

        outline_key = await self.outline.create_key(name=f"user_{user_id}")

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
        self._schedule_tasks(subscription.id, end_date)
        return subscription, outline_key["accessUrl"]

    async def _extend_subscription(
        self, subscription: Subscription, tariff_id: int
    ) -> tuple[Subscription, str]:
        """
        Продлевает существующую активную/неактивную подписку.

        Args:
            subscription: Существующая подписка
            tariff_id: ID тарифа для продления

        Returns:
            tuple: (subscription, vpn_key)

        Raises:
            TariffNotFoundException: Если тариф не найден
        """
        tariff = await self.tariff_repo.get_by_id(tariff_id)
        if not tariff:
            logger.info(f"Tariff {tariff_id} not found for subscription {subscription.id}")
            raise TariffNotFoundException("Tariff not found")

        now = datetime.now(timezone.utc)

        # Если подписка активна - продлеваем от текущей даты окончания
        if subscription.is_active and subscription.end_date > now:
            new_end_date = subscription.end_date + timedelta(days=tariff.duration_days)
            await self.sub_repo.update_end_date(subscription, new_end_date)
            key = subscription.vpn_key
        else:
            outline_key = await self.outline.create_key(name=f"user_{subscription.user_id}")
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
        self._schedule_tasks(subscription.id, new_end_date, reschedule=True)
        await self.sub_repo.increment_payments(subscription)

        return subscription, key

    async def deactivate_subscription(self, sub_id: int) -> None:
        """
        Деактивирует подписку и удаляет VPN ключ.

        Args:
            sub_id: ID подписки для деактивации
        """
        try:
            sub = await self.sub_repo.get_by_id(sub_id)
            if sub and sub.is_active:
                # Удаляем ключ в Outline
                if sub.outline_key_id:
                    await self.outline.delete_key(str(sub.outline_key_id))
                # Деактивируем подписку и очищаем ключи
                await self.sub_repo.update(sub, vpn_key="", outline_key_id="", is_active=False)
        except Exception as e:
            logger.exception(
                "Unhandled exception in SubscriptionService.deactivate_subscription "
                f"for sub {sub_id}: {e}"
            )
            raise SubscriptionException(f"Failed to deactivate subscription {sub_id}: {str(e)}")

    async def get_subscription_info(self, user_id: int) -> dict:
        """
        Получает информацию о подписке пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            dict: Словарь с полями:
                - end_date: datetime окончания подписки в UTC
                - vpn_key: строка VPN ключа
                - device_limit: int лимит устройств

        Raises:
            SubscriptionNotFoundException: Если подписка не найдена
            SubscriptionNotActiveException: Если подписка не активна
        """
        try:
            sub = await self.sub_repo.get_by_user_id(user_id)
            if not sub:
                raise SubscriptionNotFoundException(f"Subscription for user {user_id} not found")
            if not sub.is_active:
                raise SubscriptionNotActiveException(f"Subscription for user {user_id} not active")
            end_date_utc = sub.end_date.astimezone(timezone.utc)
            info = {
                "end_date": end_date_utc,
                "vpn_key": sub.vpn_key,
                "device_limit": 3,
            }
            logging.debug(
                "Retrieved subscription info for user %s: end_date=%s, key=%s",
                user_id,
                end_date_utc.isoformat(),
                sub.vpn_key,
            )
            return info
        except (SubscriptionNotFoundException, SubscriptionNotActiveException):
            raise
        except Exception as e:
            logger.exception(
                "Unhandled exception in SubscriptionService.get_subscription_info "
                f"for user {user_id}: {e}"
            )
            raise SubscriptionException(
                f"Failed to get subscription info for user {user_id}: {str(e)}"
            )

    async def send_notification(self, sub_id: int) -> None:
        """
        Отправляет пользователю сообщение о скором окончании подписки.

        Args:
            sub_id: ID подписки
        """
        try:
            from src.bot import bot

            sub = await self.sub_repo.get_by_id(sub_id)
            if sub and sub.is_active:
                await bot.send_message(
                    sub.user_id,
                    "Ваша подписка закончится через 3 дня\n"
                    "Продлите ее, чтобы оставаться на связи!",
                )
        except Exception as e:
            logger.exception(f"Unhandled exception in send_notification {sub_id}: {e}")
            raise SubscriptionException(
                f"Failed to send notification for subscription {sub_id}: {str(e)}"
            )

    async def activate_trial(self, user_id: int) -> tuple[Subscription, str]:
        """
        Активирует пробный период для пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            tuple: (subscription, vpn_key)

        Raises:
            TariffNotFoundException:  Если тариф trial не найден
            UserNotFoundException: Если пользователь не найден
            PermissionError: Если пробный период уже использован
        """
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundException("User not found")
            if user.trial_used:
                raise TrialAlreadyUsedException("Trial already used")

            # Используем специальный тариф для пробного периода
            trial_tariff = await self.tariff_repo.get_by_name("trial")
            if not trial_tariff:
                raise TariffNotFoundException("Trial tariff not configured")

            sub, key = await self.create_or_extend_subscription(user_id, trial_tariff.id)
            await self.user_repo.mark_trial_used(user)
            return sub, key
        except (TariffNotFoundException, UserNotFoundException, TrialAlreadyUsedException):
            raise
        except ServiceException:
            raise
        except Exception as e:
            logger.exception(f"Unhandled exception in activate_trial for user {user_id}: {e}")
            raise SubscriptionException(f"Failed to activate trial for user {user_id}: {str(e)}")

    async def apply_referral_bonus(self, referral: Referral) -> None:
        try:
            now = datetime.now(timezone.utc)
            await self._apply_bonus_to_referred(referral, now)
            await self._apply_bonus_to_referrer(referral, now)
        except TariffNotFoundException:
            raise
        except Exception as e:
            logger.exception(
                f"Unhandled exception in apply_referral_bonus for referral {referral.id}: {e}"
            )
            raise SubscriptionException(
                f"Failed to apply referral bonus for referral {referral.id}: {str(e)}"
            )

    async def _apply_bonus_to_referred(self, referral: Referral, now: datetime) -> None:
        """
        Применяет бонус для приглашенного пользователя.

        Args:
            referral: Объект реферальной программы
            now: Текущее время в UTC
        """

        trial = await self.tariff_repo.get_by_name("trial")
        if not trial:
            raise TariffNotFoundException("Trial tariff not configured")
        days = trial.duration_days + referral.bonus_days
        end = now + timedelta(days=days)
        outline = await self._create_outline_key(referral.referred_id)

        new_sub = await self.sub_repo.create(
            user_id=referral.referred_id,
            tariff_id=trial.id,
            vpn_key=outline["accessUrl"],
            outline_key_id=outline["id"],
            end_date=end,
        )
        await self.user_repo.mark_trial_used(referral.referred)
        self._schedule_tasks(new_sub.id, end, reschedule=True)
        logging.info(f"Applied {days}-day bonus to referred {referral.referred_id}")

    async def _apply_bonus_to_referrer(self, referral: Referral, now: datetime) -> None:
        """
        Применяет бонус для пригласившего пользователя.

        Args:
            referral: Объект реферальной программы
            now: Текущее время в UTC
        """
        referrer_sub = await self.sub_repo.get_by_user_id(referral.referrer_id)
        if referrer_sub:
            end_date = max(referrer_sub.end_date, now) + timedelta(days=7)
            await self.sub_repo.update_end_date(referrer_sub, end_date)
            sub_id = referrer_sub.id
        else:
            trial = await self.tariff_repo.get_by_name("trial")
            days = trial.duration_days + referral.bonus_days
            end_date = now + timedelta(days=days)
            outline = await self._create_outline_key(referral.referrer_id)
            sub = await self.sub_repo.create(
                user_id=referral.referrer_id,
                tariff_id=trial.id,
                vpn_key=outline["accessUrl"],
                outline_key_id=outline["id"],
                end_date=end_date,
            )
            await self.user_repo.mark_trial_used(referral.referrer)
            sub_id = sub.id

        self._schedule_tasks(sub_id, end_date, reschedule=True)
        logging.info(f"Applied 7-day bonus to referrer {referral.referrer_id}")

    async def _create_outline_key(self, user_id: int) -> dict:
        """
        Создает VPN ключ в Outline для пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            dict: Словарь с данными созданного ключа
        """
        return await self.outline.create_key(name=f"user_{user_id}")

    def _schedule_tasks(self, sub_id: int, end_date: datetime, reschedule: bool = False) -> None:
        """
        Планирует или перепланирует задачи деактивации и уведомления.

        Args:
            sub_id: ID подписки
            end_date: Дата окончания подписки
            reschedule: Флаг перепланирования существующих задач
        """
        if reschedule:
            reschedule_deactivation(sub_id, end_date)
            reschedule_notification(sub_id, end_date - timedelta(days=3))
        else:
            schedule_deactivation(sub_id, end_date)
            schedule_notification(sub_id, end_date - timedelta(days=3))
