import logging
from typing import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core import models  # noqa: F401
from src.core.subscription.scheduler import scheduler
from src.core.tariff.models import Tariff
from src.core.tariff.repository import TariffRepository
from src.core.user.repository import UserRepository
from src.database import DATABASE_URL, Base, engine, session_factory
from tests.samples import (
    month_sample,
    three_months_sample,
    trial_sample,
    user1_sample,
    user2_sample,
    user3_sample,
    user4_sample,
    user5_sample,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
async def setup_db() -> None:
    """Фикстура для инициализации и очистки тестовой базы данных."""
    # MODE автоматически устанавливается в "TEST" благодаря pytest-env
    assert settings.MODE == "TEST"
    assert settings.TEST_DATABASE_URL == DATABASE_URL

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS apscheduler_jobs"))
        logger.info("Все таблицы удалены")

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Все таблицы созданы")

    scheduler.start()


@pytest.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    - создаёт сессию для каждого теста
    - откатывает изменения после каждого теста
    """
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="session")
async def shared_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Открывает одну базовую сессию перед всеми тестами
    и закрывает её после их завершения.
    """
    async with session_factory() as session:
        yield session


@pytest.fixture
async def user_repo(db_session):
    return UserRepository(db_session)


@pytest.fixture
async def tariff_repo(db_session):
    return TariffRepository(db_session)


@pytest.fixture
async def sample_user(user_repo):
    user = await user_repo.create(id=1000000000, username="sample_user", ref_code="a1m2uH3n")
    return user


@pytest.fixture
async def setup_users(user_repo):
    await user_repo.create(
        id=user1_sample.id, username=user1_sample.username, ref_code=user1_sample.ref_code
    )
    await user_repo.create(
        id=user2_sample.id, username=user2_sample.username, ref_code=user2_sample.ref_code
    )
    await user_repo.create(
        id=user3_sample.id, username=user3_sample.username, ref_code=user3_sample.ref_code
    )
    await user_repo.create(
        id=user4_sample.id, username=user4_sample.username, ref_code=user4_sample.ref_code
    )
    await user_repo.create(
        id=user5_sample.id, username=user5_sample.username, ref_code=user5_sample.ref_code
    )


@pytest.fixture(scope="session")
async def setup_tariffs(shared_db_session) -> dict[str, Tariff]:
    """
    Однократное создание тарифов для всех тестов.
    """
    tariff_repo = TariffRepository(shared_db_session)
    trial = await tariff_repo.create(
        name=trial_sample.name, price=trial_sample.price, duration_days=trial_sample.duration_days
    )
    month = await tariff_repo.create(
        name=month_sample.name, price=month_sample.price, duration_days=month_sample.duration_days
    )
    three_months = await tariff_repo.create(
        name=three_months_sample.name,
        price=three_months_sample.price,
        duration_days=three_months_sample.duration_days,
    )
    await shared_db_session.commit()
    return {
        trial.name: trial,  # "trial"
        month.name: month,  # "month"
        three_months.name: three_months,  # "3month"
    }
