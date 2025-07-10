import json

import pytest

from src.config import settings
from src.db.database import Base, engine


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    assert settings.MODE == "TEST"

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    def open_mock_json(model: str):
        path = f"src/tests/mock_{model}.json"
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    # users = open_mock_json("user")
    # tariffs = open_mock_json("tariff")
    # subscriptions = open_mock_json("subscription")
    # referrals = open_mock_json("referral")
