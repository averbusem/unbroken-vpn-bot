from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    await message.answer("Hi!")
