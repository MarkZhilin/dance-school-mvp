from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards import MAIN_MENU_BUTTONS, main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer("Бот запущен ✅", reply_markup=main_menu_keyboard())


@router.message(F.text.in_(MAIN_MENU_BUTTONS))
async def handle_main_menu(message: Message) -> None:
    if not message.text:
        return
    await message.answer(f"В разработке: {message.text}")
