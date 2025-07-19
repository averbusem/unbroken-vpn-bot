from aiogram import Router

from src.bot.handlers.commands import router as router_cmd
from src.bot.handlers.help import router as router_help
from src.bot.handlers.main_menu import router as router_main_menu
from src.bot.handlers.payment import router as router_payment
from src.bot.handlers.privacy_policy import router as router_privacy_policy
from src.bot.handlers.referral_info import router as router_referral_info
from src.bot.handlers.subscription_info import router as router_subscription_info
from src.bot.handlers.trial_period import router as router_trial_period

router = Router()


def get_handlers_router() -> Router:
    router.include_router(router_cmd)
    router.include_router(router_main_menu)
    router.include_router(router_trial_period)
    router.include_router(router_subscription_info)
    router.include_router(router_payment)
    router.include_router(router_referral_info)
    router.include_router(router_help)
    router.include_router(router_privacy_policy)
    return router
