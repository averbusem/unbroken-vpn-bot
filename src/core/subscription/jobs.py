# src/core/subscription/jobs.py
import logging
from datetime import datetime

from src.core.subscription.scheduler import scheduler
from src.database import session_factory
from src.exceptions import ServiceException

logger = logging.getLogger(__name__)


async def _run_deactivate(sub_id: int):

    from src.core.subscription.service import SubscriptionService

    async with session_factory() as session:
        service = SubscriptionService(session)
        try:
            await service.deactivate_subscription(sub_id)
            await session.commit()
            logger.info(f"Successfully completed deactivation job for subscription {sub_id}")
        except ServiceException:
            await session.rollback()
        except Exception as e:
            await session.rollback()
            logger.exception(
                f"Unhandled exception in _run_deactivate for subscription {sub_id}: {e}"
            )


async def _run_notify(sub_id: int):
    from src.core.subscription.service import SubscriptionService

    async with session_factory() as session:
        service = SubscriptionService(session)
        try:
            await service.send_notification(sub_id)
            await session.commit()
            logger.info(f"Successfully completed notification job for subscription {sub_id}")
        except ServiceException:
            await session.rollback()
        except Exception as e:
            logger.exception(f"Unhandled exception in _run_notify for subscription {sub_id}: {e}")


def schedule_deactivation(sub_id: int, run_date: datetime):
    """
    Добавляет задачу деактивации подписки в заданное время.
    """
    try:
        job_id = f"deactivate_{sub_id}"
        scheduler.add_job(
            _run_deactivate, trigger="date", run_date=run_date, args=[sub_id], id=job_id
        )
    except Exception as e:
        logger.exception(
            f"Unhandled exception in schedule_deactivation for subscription {sub_id}: {e}"
        )


def schedule_notification(sub_id: int, run_date: datetime):
    """
    Добавляет задачу уведомления за 3 дня до окончания подписки.
    """
    try:
        job_id = f"notify_{sub_id}"
        scheduler.add_job(_run_notify, trigger="date", run_date=run_date, args=[sub_id], id=job_id)
    except Exception as e:
        logger.exception(
            f"Unhandled exception in schedule_notification for subscription {sub_id}: {e}"
        )


def reschedule_deactivation(sub_id: int, new_date: datetime):
    """
    Перепланирует задачу деактивации: удаляет старую и ставит новую.
    """
    try:
        job_id = f"deactivate_{sub_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        schedule_deactivation(sub_id, new_date)
    except Exception as e:
        logger.exception(
            f"Unhandled exception in reschedule_deactivation for subscription {sub_id}: {e}"
        )


def reschedule_notification(sub_id: int, new_date: datetime):
    """
    Перепланирует задачу уведомления: удаляет старую и ставит новую.
    """
    try:
        job_id = f"notify_{sub_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        schedule_notification(sub_id, new_date)
    except Exception as e:
        logger.exception(
            f"Unhandled exception in reschedule_notification for subscription {sub_id}: {e}"
        )


async def run_all_deactivations():
    """
    Выполнить все задачи деактивации, запланированные в APScheduler,
    и удалить их из планировщика после выполнения.
    """
    try:
        for job in list(scheduler.get_jobs()):
            if job.id.startswith("deactivate_"):
                sub_id = job.args[0]
                await _run_deactivate(sub_id)
                # Удаляем задачу после выполнения
                scheduler.remove_job(job.id)
    except Exception as e:
        logger.exception(f"Unhandled exception in run_all_deactivations: {e}")


async def run_all_notifications():
    """
    Выполнить все задачи уведомлений, запланированные в APScheduler,
    и удалить их из планировщика после выполнения.
    """
    try:
        for job in list(scheduler.get_jobs()):
            if job.id.startswith("notify_"):
                sub_id = job.args[0]
                await _run_notify(sub_id)
                # Удаляем задачу после выполнения
                scheduler.remove_job(job.id)
    except Exception as e:
        logger.exception(f"Unhandled exception in run_all_notifications: {e}")
