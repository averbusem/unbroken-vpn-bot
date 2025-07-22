import logging

from aiogram import BaseMiddleware, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.bot.keyboards import back_to_main_kb
from src.db.database import session_factory


class DBSessionMiddleware(BaseMiddleware):
    """
    Открывает AsyncSession перед обработкой и коммитит/роллбекает после.
    Сессия доступна в хендлерах через параметр `session: AsyncSession`.
    При любой ошибке бот отправляет пользователю единое уведомление,
    корректно работая и для Message, и для CallbackQuery.
    """

    async def __call__(self, handler, event: TelegramObject, data: dict):
        async with session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result

            except Exception:
                # Откатываем
                await session.rollback()
                logging.exception("Error in middleware %s for event %s", handler.__name__, event)

                if isinstance(event, CallbackQuery) and event.message:
                    return await event.message.answer(
                        "⚠️ Произошла ошибка при обработке запроса. Напишите в поддержку.",
                        reply_markup=back_to_main_kb(),
                    )

                if isinstance(event, Message):
                    return await event.answer(
                        "⚠️ Произошла ошибка при обработке запроса. Напишите в поддержку.",
                        reply_markup=back_to_main_kb(),
                    )

                return None


class UpdateLastMessageIdMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        state: FSMContext = data.get("state")

        result = await handler(event, data)

        current_message_id = None
        if isinstance(result, types.Message):
            current_message_id = result.message_id
        elif isinstance(event, types.CallbackQuery):
            current_message_id = event.message.message_id

        if state and current_message_id:
            logging.debug(f"Обновление last_message_id = {current_message_id}")
            await state.update_data(last_message_id=current_message_id)
        return result
