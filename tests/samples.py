from dataclasses import dataclass


@dataclass(frozen=True)
class UserSchema:
    id: int
    username: str
    ref_code: str


user1_sample = UserSchema(id=1111111111, username="user1", ref_code="a1b1c1d1")
user2_sample = UserSchema(id=2222222222, username="user2", ref_code="a2b2c2d2")
user3_sample = UserSchema(id=3333333333, username="user3", ref_code="a3b3c3d3")
user4_sample = UserSchema(id=4444444444, username="user4", ref_code="a4b4c4d4")
user5_sample = UserSchema(id=5555555555, username="user5", ref_code="a5b5c5d5")


@dataclass(frozen=True)
class TariffSchema:
    id: int
    name: str
    price: float
    duration_days: int


trial_sample = TariffSchema(id=1, name="trial", price=0.0, duration_days=7)
month_sample = TariffSchema(id=2, name="month", price=100.0, duration_days=30)
three_months_sample = TariffSchema(id=3, name="3month", price=250.0, duration_days=90)
