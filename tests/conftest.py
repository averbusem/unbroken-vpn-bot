import logging
from typing import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core import models  # noqa: F401
from src.core.subscription.scheduler import scheduler
from src.database import DATABASE_URL, Base, engine, session_factory

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
async def setup_db() -> None:
    """Фикстура для инициализации и очистки тестовой базы данных на уровне сессии."""
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

    # import json
    # def open_mock_json(model: str):
    #     path = f"tests/mock_{model}.json"
    #     with open(path, "r", encoding="utf-8") as file:
    #         return json.load(file)
    #
    # users = open_mock_json("user")
    # tariffs = open_mock_json("tariff")
    # subscriptions = open_mock_json("subscription")
    # referrals = open_mock_json("referral")
