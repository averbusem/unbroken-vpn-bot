import asyncio
import logging

import src.core.models  # noqa: F401
from src.bot import bot, dp, setup_bot
from src.core.subscription.scheduler import scheduler


# TODO московское время
async def main():
    scheduler.start()

    await setup_bot()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
