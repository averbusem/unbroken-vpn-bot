from contextlib import nullcontext as does_not_raise
from datetime import datetime, timedelta, timezone

import pytest

from src.exceptions import TariffNotFoundException
from tests.samples import (
    month_sample,
    three_months_sample,
    trial_sample,
    user1_sample,
    user2_sample,
    user3_sample,
    user4_sample,
)


class TestSubscriptionService:
    """Тесты для SubscriptionService._create_subscription"""

    @pytest.mark.parametrize(
        "user_id, tariff_id, expectation",
        [
            # Успешные сценарии
            (user1_sample.id, month_sample.id, does_not_raise()),
            (user2_sample.id, trial_sample.id, does_not_raise()),
            (user3_sample.id, three_months_sample.id, does_not_raise()),
            # Ошибочные сценарии
            (user4_sample.id, 999, pytest.raises(TariffNotFoundException)),
        ],
    )
    async def test_create_subscription(
        self, sub_service, setup_tariffs, setup_users, user_id, tariff_id, expectation
    ):
        with expectation:
            subscription, vpn_key = await sub_service._create_subscription(user_id, tariff_id)

            assert subscription is not None
            assert subscription.user_id == user_id
            assert subscription.tariff_id == tariff_id
            assert subscription.is_active is True
            assert vpn_key is not None
            assert vpn_key.startswith("ss://")
            assert "@190.80.230.20:55000" in vpn_key

            durations = {
                trial_sample.id: trial_sample.duration_days,
                month_sample.id: month_sample.duration_days,
                three_months_sample.id: three_months_sample.duration_days,
            }
            expected_date = (
                datetime.now(timezone.utc) + timedelta(days=durations.get(tariff_id, 0))
            ).date()
            assert subscription.end_date.date() == expected_date
