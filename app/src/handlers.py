from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import Config
from db import deactivate_admin, list_admins, upsert_admin
from keyboards import ADMIN_MENU_BUTTONS, MAIN_MENU_BUTTONS, admin_menu_keyboard, main_menu_keyboard

router = Router()


class AdminStates(StatesGroup):
    add_tg_id = State()
    add_name = State()
    disable_tg_id = State()


def _is_owner(message: Message, config: Config) -> bool:
    return message.from_user is not None and message.from_user.id == config.owner_tg_user_id


@router.message(CommandStart())
async def handle_start(message: Message, config: Config) -> None:
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        "Бот запущен ✅",
        reply_markup=main_menu_keyboard(user_id=user_id, owner_id=config.owner_tg_user_id),
    )


@router.message(F.text.in_(MAIN_MENU_BUTTONS))
async def handle_main_menu(message: Message, config: Config) -> None:
    if not message.text:
        return
    await message.answer(f"В разработке: {message.text}")


@router.message(F.text == "👑 Админы")
async def handle_admin_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    await state.clear()
    await message.answer("Меню админов", reply_markup=admin_menu_keyboard())


@router.message(F.text == ADMIN_MENU_BUTTONS[0])
async def handle_admin_add_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    await state.set_state(AdminStates.add_tg_id)
    await message.answer("Введите tg_user_id числом")


@router.message(AdminStates.add_tg_id)
async def handle_admin_add_tg_id(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Нужен tg_user_id числом")
        return
    await state.update_data(tg_user_id=int(message.text))
    await state.set_state(AdminStates.add_name)
    await message.answer("Введите имя админа")


@router.message(AdminStates.add_name)
async def handle_admin_add_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Имя не может быть пустым")
        return
    data = await state.get_data()
    tg_user_id = int(data["tg_user_id"])
    upsert_admin(config.db_path, tg_user_id=tg_user_id, name=message.text.strip())
    await state.clear()
    await message.answer("Админ сохранен и активирован ✅", reply_markup=admin_menu_keyboard())


@router.message(F.text == ADMIN_MENU_BUTTONS[1])
async def handle_admin_disable_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    await state.set_state(AdminStates.disable_tg_id)
    await message.answer("Введите tg_user_id для отключения")


@router.message(AdminStates.disable_tg_id)
async def handle_admin_disable_tg_id(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Нужен tg_user_id числом")
        return
    success = deactivate_admin(config.db_path, tg_user_id=int(message.text))
    await state.clear()
    if success:
        await message.answer("Админ отключен ✅", reply_markup=admin_menu_keyboard())
    else:
        await message.answer("Админ не найден", reply_markup=admin_menu_keyboard())


@router.message(F.text == ADMIN_MENU_BUTTONS[2])
async def handle_admin_list(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    active, inactive = list_admins(config.db_path)
    active_lines = [f"- {rec.name} ({rec.tg_user_id})" for rec in active] or ["- нет"]
    inactive_lines = [f"- {rec.name} ({rec.tg_user_id})" for rec in inactive] or ["- нет"]
    text = "Активные:\n" + "\n".join(active_lines) + "\n\nНеактивные:\n" + "\n".join(inactive_lines)
    await message.answer(text, reply_markup=admin_menu_keyboard())


@router.message(F.text == ADMIN_MENU_BUTTONS[3])
async def handle_admin_back(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    await state.clear()
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        "Главное меню",
        reply_markup=main_menu_keyboard(user_id=user_id, owner_id=config.owner_tg_user_id),
    )
