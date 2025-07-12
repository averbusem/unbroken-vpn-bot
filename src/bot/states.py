from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    TRIAL = State()
    TARIFF_SELECT = State()
    CREATE_PAYMENT = State()
    SUCCESSFUL_PAYMENT = State()
    SUBSCRIPTION_INFO = State()
    REFERRAL = State()
