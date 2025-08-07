import pytest

from src.core.subscription.service import SubscriptionService


@pytest.fixture
async def sub_service(db_session, mock_outline):
    sub_service = SubscriptionService(db_session)
    sub_service.outline = mock_outline
    return sub_service


@pytest.fixture
async def mock_outline():
    class DummyOutline:
        def __init__(self):
            self.counter = 0

        async def create_key(self, name: str):
            self.counter += 1
            return {
                "accessUrl": (
                    "ss://Y3hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpYYkJTakp5Um9"
                    "MVjhUa0NZSGVacWY4@190.80.230.20:55000/?outline=1"
                ),
                "id": str(self.counter),
            }

        async def delete_key(self, key_id: str):
            # В продакшене удаляется на стороне сервера самим outline
            return None

    return DummyOutline()
