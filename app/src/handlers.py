from __future__ import annotations

from datetime import datetime
import re
import sqlite3
from typing import Optional

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import Config
from db import (
    create_client,
    deactivate_admin,
    get_client_by_phone,
    is_admin_active,
    list_admins,
    upsert_admin,
)
from keyboards import (
    ADMIN_MENU_BUTTONS,
    CONFIRM_BUTTONS,
    MAIN_MENU_BUTTONS,
    NEW_CLIENT_PHONE_BUTTONS,
    SKIP_BUTTONS,
    admin_menu_keyboard,
    confirm_keyboard,
    main_menu_keyboard,
    new_client_phone_keyboard,
    skip_keyboard,
)

router = Router()


class AdminStates(StatesGroup):
    add_tg_id = State()
    add_name = State()
    disable_tg_id = State()


class NewClientStates(StatesGroup):
    phone = State()
    full_name = State()
    tg_username = State()
    birth_date = State()
    comment = State()
    confirm = State()


def _is_owner(message: Message, config: Config) -> bool:
    return message.from_user is not None and message.from_user.id == config.owner_tg_user_id


def _has_access(message: Message, config: Config) -> bool:
    if message.from_user is None:
        return False
    if message.from_user.id == config.owner_tg_user_id:
        return True
    return is_admin_active(config.db_path, message.from_user.id)


def _main_menu_reply_markup(message: Message, config: Config):
    user_id = message.from_user.id if message.from_user else 0
    return main_menu_keyboard(user_id=user_id, owner_id=config.owner_tg_user_id)


async def _deny_and_menu(message: Message, config: Config, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Нет доступа", reply_markup=_main_menu_reply_markup(message, config))


def _normalize_phone(raw: str) -> str:
    trimmed = raw.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
    digits = re.sub(r"\D", "", trimmed)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        return f"+7{digits[1:]}"
    if trimmed.startswith("+") and digits:
        return f"+{digits}"
    return digits


def _parse_birth_date(value: str) -> Optional[str]:
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return parsed.strftime("%Y-%m-%d")
    return None


@router.message(CommandStart())
async def handle_start(message: Message, config: Config) -> None:
    await message.answer(
        "Бот запущен ✅",
        reply_markup=_main_menu_reply_markup(message, config),
    )


@router.message(F.text == MAIN_MENU_BUTTONS[0])
async def handle_new_client_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(NewClientStates.phone)
    await message.answer("Введите телефон клиента", reply_markup=new_client_phone_keyboard())


@router.message(NewClientStates.phone)
async def handle_new_client_phone(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == NEW_CLIENT_PHONE_BUTTONS[2]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == NEW_CLIENT_PHONE_BUTTONS[1]:
        await message.answer("Введите телефон вручную")
        return

    raw_phone = None
    if message.contact and message.contact.phone_number:
        raw_phone = message.contact.phone_number
    elif message.text:
        raw_phone = message.text

    if not raw_phone:
        await message.answer("Введите телефон клиента")
        return

    normalized = _normalize_phone(raw_phone)
    if not normalized:
        await message.answer("Не удалось распознать телефон, попробуйте еще раз")
        return

    existing = get_client_by_phone(config.db_path, normalized)
    if existing:
        _, full_name, phone = existing
        await state.clear()
        await message.answer(
            f"Клиент с таким телефоном уже существует: {full_name}, {phone}",
            reply_markup=_main_menu_reply_markup(message, config),
        )
        return

    await state.update_data(phone=normalized)
    await state.set_state(NewClientStates.full_name)
    await message.answer("Введите ФИО клиента")


@router.message(NewClientStates.full_name)
async def handle_new_client_full_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("ФИО не может быть пустым")
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(NewClientStates.tg_username)
    await message.answer("Введите tg_username (опционально)", reply_markup=skip_keyboard())


@router.message(NewClientStates.tg_username)
async def handle_new_client_tg_username(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[1]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return

    tg_username = None
    if message.text and message.text.strip() not in (SKIP_BUTTONS[0], "-"):
        tg_username = message.text.strip()

    await state.update_data(tg_username=tg_username)
    await state.set_state(NewClientStates.birth_date)
    await message.answer("Введите дату рождения (ДД.ММ.ГГГГ или YYYY-MM-DD)", reply_markup=skip_keyboard())


@router.message(NewClientStates.birth_date)
async def handle_new_client_birth_date(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[1]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return

    birth_date = None
    if message.text and message.text.strip() not in (SKIP_BUTTONS[0], "-"):
        parsed = _parse_birth_date(message.text)
        if not parsed:
            await message.answer("Неверный формат даты, попробуйте еще раз или нажмите Пропустить")
            return
        birth_date = parsed

    await state.update_data(birth_date=birth_date)
    await state.set_state(NewClientStates.comment)
    await message.answer("Комментарий (опционально)", reply_markup=skip_keyboard())


@router.message(NewClientStates.comment)
async def handle_new_client_comment(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[1]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return

    comment = None
    if message.text and message.text.strip() not in (SKIP_BUTTONS[0], "-"):
        comment = message.text.strip()

    await state.update_data(comment=comment)
    data = await state.get_data()
    summary = (
        "Проверьте данные:\n"
        f"Телефон: {data.get('phone')}\n"
        f"ФИО: {data.get('full_name')}\n"
        f"tg_username: {data.get('tg_username') or '—'}\n"
        f"Дата рождения: {data.get('birth_date') or '—'}\n"
        f"Комментарий: {data.get('comment') or '—'}"
    )
    await state.set_state(NewClientStates.confirm)
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(NewClientStates.confirm)
async def handle_new_client_confirm(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text not in CONFIRM_BUTTONS:
        await message.answer("Выберите действие", reply_markup=confirm_keyboard())
        return
    if message.text == CONFIRM_BUTTONS[1]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return

    data = await state.get_data()
    phone = data.get("phone")
    full_name = data.get("full_name")
    tg_username = data.get("tg_username")
    birth_date = data.get("birth_date")
    comment = data.get("comment")

    existing = get_client_by_phone(config.db_path, phone)
    if existing:
        _, existing_name, existing_phone = existing
        await state.clear()
        await message.answer(
            f"Клиент с таким телефоном уже существует: {existing_name}, {existing_phone}",
            reply_markup=_main_menu_reply_markup(message, config),
        )
        return

    try:
        create_client(
            config.db_path,
            full_name=full_name,
            phone=phone,
            tg_user_id=None,
            tg_username=tg_username,
            birth_date=birth_date,
            comment=comment,
        )
    except sqlite3.IntegrityError:
        await state.clear()
        await message.answer(
            "Клиент с таким телефоном уже существует",
            reply_markup=_main_menu_reply_markup(message, config),
        )
        return

    await state.clear()
    await message.answer("Клиент добавлен ✅", reply_markup=_main_menu_reply_markup(message, config))


@router.message(F.text.in_(MAIN_MENU_BUTTONS) & (F.text != MAIN_MENU_BUTTONS[0]))
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
    await message.answer(
        "Главное меню",
        reply_markup=_main_menu_reply_markup(message, config),
    )
