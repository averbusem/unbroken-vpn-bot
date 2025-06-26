from aiogram import Router

from src.bot.handlers.commands import router as cmd_router

router = Router()


def get_handlers_router() -> Router:
    router.include_router(cmd_router)
    return router
