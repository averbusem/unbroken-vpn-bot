import logging

from aiogram import BaseMiddleware, Bot, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.bot.keyboards import back_to_main_kb
from src.db.database import session_factory


async def _remove_keyboard(bot: Bot, chat_id: int, message_id: int) -> None:
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=message_id, reply_markup=None
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logging.debug(f"Keyboard already removed: {chat_id}:{message_id}")
            return
        logging.error(f"Error removing keyboard {chat_id}:{message_id}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error removing keyboard {chat_id}:{message_id}: {e}")


class DBSessionMiddleware(BaseMiddleware):
    """
    Открывает AsyncSession перед обработкой и коммитит/роллбекает после.
    """

    async def __call__(self, handler, event: TelegramObject, data: dict):
        async with session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result

            except Exception:
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


class RemoveLastKeyboardMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        state: FSMContext = data.get("state")
        data_state = await state.get_data()
        last_message_id = data_state.get("last_message_id")

        result = await handler(event, data)

        current_message_id = None
        if isinstance(result, types.Message):
            current_message_id = result.message_id
        elif isinstance(event, types.CallbackQuery):
            current_message_id = event.message.message_id

        if last_message_id and current_message_id and last_message_id != current_message_id:
            chat_id = (
                event.message.chat.id if isinstance(event, types.CallbackQuery) else event.chat.id
            )
            await _remove_keyboard(event.bot, chat_id, last_message_id)

        if state and current_message_id:
            logging.debug(f"Обновление last_message_id = {current_message_id}")
            await state.update_data(last_message_id=current_message_id)
        return result
