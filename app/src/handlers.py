from __future__ import annotations

from datetime import datetime, date, timedelta
import re
import sqlite3
from typing import Optional

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import Config
from db import (
    create_client,
    create_group,
    create_single_visit_booked,
    deactivate_admin,
    get_client_by_id,
    get_client_by_phone,
    get_client_by_tg_username,
    is_admin_active,
    list_active_groups,
    list_admins,
    search_clients_by_name,
    upsert_client_group_active,
    upsert_admin,
)
from keyboards import (
    ADMIN_MENU_BUTTONS,
    ADD_GROUP_BUTTONS,
    BOOKING_CLIENT_SEARCH_BUTTONS,
    BOOKING_DATE_BUTTONS,
    BOOKING_TYPE_BUTTONS,
    CLIENT_ACTION_BUTTONS,
    CONFIRM_BUTTONS,
    MAIN_MENU_BUTTONS,
    NEW_CLIENT_PHONE_BUTTONS,
    SEARCH_MENU_BUTTONS,
    SKIP_BUTTONS,
    add_group_keyboard,
    admin_menu_keyboard,
    booking_client_search_keyboard,
    booking_date_keyboard,
    booking_type_keyboard,
    cancel_keyboard,
    client_actions_keyboard,
    confirm_keyboard,
    groups_keyboard,
    main_menu_keyboard,
    new_client_phone_keyboard,
    not_found_keyboard,
    search_menu_keyboard,
    search_results_keyboard,
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


class SearchStates(StatesGroup):
    menu = State()
    phone = State()
    name = State()
    tg_username = State()
    select = State()
    card = State()


class BookingStates(StatesGroup):
    select_client = State()
    client_phone = State()
    client_name = State()
    client_tg = State()
    client_select = State()
    select_type = State()
    select_group = State()
    add_group = State()
    select_date = State()
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


def _normalize_username(value: str) -> str:
    value = value.strip()
    if value.startswith("@"):
        value = value[1:]
    return value.lower()


def _parse_birth_date(value: str) -> Optional[str]:
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return parsed.strftime("%Y-%m-%d")
    return None


def _parse_iso_date(value: str) -> Optional[str]:
    value = value.strip()
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return parsed.strftime("%Y-%m-%d")


def _format_group_label(group_id: int, name: str) -> str:
    return f"{name} (id:{group_id})"


def _format_booking_summary(
    client_name: str,
    group_name: str,
    booking_type: str,
    booking_date: Optional[str],
) -> str:
    type_label = "Разовое" if booking_type == "single" else "По абонементу"
    date_line = f"Дата: {booking_date}" if booking_date else "Дата: —"
    return (
        "Проверьте данные:\n"
        f"Клиент: {client_name}\n"
        f"Группа: {group_name}\n"
        f"Тип: {type_label}\n"
        f"{date_line}"
    )


def _format_client_card(
    client_id: int,
    full_name: str,
    phone: str,
    tg_username: Optional[str],
    birth_date: Optional[str],
    comment: Optional[str],
) -> str:
    tg_value = tg_username or "—"
    if tg_value != "—" and not tg_value.startswith("@"):
        tg_value = f"@{tg_value}"
    return (
        "Карточка клиента:\n"
        f"ID: {client_id}\n"
        f"ФИО: {full_name}\n"
        f"Телефон: {phone}\n"
        f"Telegram: {tg_value}\n"
        f"Дата рождения: {birth_date or '—'}\n"
        f"Комментарий: {comment or '—'}"
    )


async def _show_client_card(message: Message, config: Config, client, state: Optional[FSMContext]) -> None:
    if not client:
        await message.answer("Клиент не найден", reply_markup=_main_menu_reply_markup(message, config))
        return
    if state is not None:
        await state.clear()
        await state.set_state(SearchStates.card)
    card = _format_client_card(
        client_id=client[0],
        full_name=client[1],
        phone=client[2],
        tg_username=client[3],
        birth_date=client[4],
        comment=client[5],
    )
    await message.answer(card, reply_markup=client_actions_keyboard())


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
        await state.clear()
        await message.answer(
            f"Клиент с таким телефоном уже существует: {existing[1]}, {existing[2]}",
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
        await state.clear()
        await message.answer(
            f"Клиент с таким телефоном уже существует: {existing[1]}, {existing[2]}",
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


@router.message(F.text == MAIN_MENU_BUTTONS[2])
async def handle_booking_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(BookingStates.select_client)
    await message.answer("Выберите способ поиска клиента", reply_markup=booking_client_search_keyboard())


@router.message(BookingStates.select_client)
async def handle_booking_select_client_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[0]:
        await state.set_state(BookingStates.client_phone)
        await message.answer("Введите телефон клиента", reply_markup=new_client_phone_keyboard())
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[1]:
        await state.set_state(BookingStates.client_name)
        await message.answer("Введите имя или часть имени", reply_markup=cancel_keyboard())
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[2]:
        await state.set_state(BookingStates.client_tg)
        await message.answer("Введите username (с @ или без)", reply_markup=cancel_keyboard())
        return
    await message.answer("Выберите способ поиска клиента", reply_markup=booking_client_search_keyboard())


@router.message(BookingStates.client_phone)
async def handle_booking_client_phone(message: Message, config: Config, state: FSMContext) -> None:
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

    client = get_client_by_phone(config.db_path, normalized)
    if not client:
        await state.clear()
        await message.answer("Не найдено", reply_markup=not_found_keyboard())
        return

    await state.update_data(client_id=client[0], client_name=client[1])
    await state.set_state(BookingStates.select_type)
    await message.answer("Выберите тип записи", reply_markup=booking_type_keyboard())


@router.message(BookingStates.client_name)
async def handle_booking_client_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите имя или часть имени")
        return

    results = search_clients_by_name(config.db_path, message.text.strip(), limit=11)
    if len(results) == 0:
        await state.clear()
        await message.answer("Не найдено", reply_markup=not_found_keyboard())
        return
    if len(results) == 1:
        await state.update_data(client_id=results[0][0], client_name=results[0][1])
        await state.set_state(BookingStates.select_type)
        await message.answer("Выберите тип записи", reply_markup=booking_type_keyboard())
        return
    if len(results) > 10:
        await message.answer("Слишком много результатов, уточните запрос")
        return

    labels = [f"{row[1]} ({row[2]})" for row in results]
    mapping = {label: row[0] for label, row in zip(labels, results)}
    await state.update_data(search_results=mapping)
    await state.set_state(BookingStates.client_select)
    await message.answer("Выберите клиента", reply_markup=search_results_keyboard(labels))


@router.message(BookingStates.client_tg)
async def handle_booking_client_tg(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите username")
        return

    normalized = _normalize_username(message.text)
    if not normalized:
        await message.answer("Введите username")
        return

    client = get_client_by_tg_username(config.db_path, normalized)
    if not client:
        await state.clear()
        await message.answer("Не найдено", reply_markup=not_found_keyboard())
        return

    await state.update_data(client_id=client[0], client_name=client[1])
    await state.set_state(BookingStates.select_type)
    await message.answer("Выберите тип записи", reply_markup=booking_type_keyboard())


@router.message(BookingStates.client_select)
async def handle_booking_client_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    data = await state.get_data()
    mapping = data.get("search_results", {})
    if message.text not in mapping:
        await message.answer("Выберите клиента из списка")
        return
    client_id = int(mapping[message.text])
    client = get_client_by_id(config.db_path, client_id)
    if not client:
        await state.clear()
        await message.answer("Клиент не найден", reply_markup=_main_menu_reply_markup(message, config))
        return
    await state.update_data(client_id=client_id, client_name=client[1])
    await state.set_state(BookingStates.select_type)
    await message.answer("Выберите тип записи", reply_markup=booking_type_keyboard())


@router.message(BookingStates.select_type)
async def handle_booking_select_type(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == BOOKING_TYPE_BUTTONS[2]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == BOOKING_TYPE_BUTTONS[0]:
        await state.update_data(booking_type="single")
    elif message.text == BOOKING_TYPE_BUTTONS[1]:
        await state.update_data(booking_type="pass")
    else:
        await message.answer("Выберите тип записи", reply_markup=booking_type_keyboard())
        return

    groups = list_active_groups(config.db_path)
    if not groups:
        await state.set_state(BookingStates.add_group)
        await message.answer("Групп пока нет", reply_markup=add_group_keyboard())
        return

    labels = [_format_group_label(group[0], group[1]) for group in groups]
    mapping = {label: group[0] for label, group in zip(labels, groups)}
    await state.update_data(group_map=mapping, group_names={group[0]: group[1] for group in groups})
    await state.set_state(BookingStates.select_group)
    await message.answer("Выберите группу", reply_markup=groups_keyboard(labels))


@router.message(BookingStates.add_group)
async def handle_booking_add_group(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == ADD_GROUP_BUTTONS[1]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == ADD_GROUP_BUTTONS[0]:
        await message.answer("Введите название группы")
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите название группы")
        return
    group_id = create_group(config.db_path, name=message.text.strip())
    groups = list_active_groups(config.db_path)
    labels = [_format_group_label(group[0], group[1]) for group in groups]
    mapping = {label: group[0] for label, group in zip(labels, groups)}
    await state.update_data(group_map=mapping, group_names={group[0]: group[1] for group in groups})
    await state.set_state(BookingStates.select_group)
    await message.answer("Выберите группу", reply_markup=groups_keyboard(labels))


@router.message(BookingStates.select_group)
async def handle_booking_select_group(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    data = await state.get_data()
    mapping = data.get("group_map", {})
    group_names = data.get("group_names", {})
    if message.text not in mapping:
        await message.answer("Выберите группу из списка")
        return
    group_id = int(mapping[message.text])
    group_name = group_names.get(group_id, message.text)
    await state.update_data(group_id=group_id, group_name=group_name)

    booking_type = data.get("booking_type")
    if booking_type == "single":
        await state.set_state(BookingStates.select_date)
        await message.answer("Выберите дату", reply_markup=booking_date_keyboard())
        return

    summary = _format_booking_summary(
        client_name=data.get("client_name"),
        group_name=group_name,
        booking_type="pass",
        booking_date=None,
    )
    await state.set_state(BookingStates.confirm)
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(BookingStates.select_date)
async def handle_booking_select_date(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == BOOKING_DATE_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == BOOKING_DATE_BUTTONS[0]:
        selected_date = date.today().strftime("%Y-%m-%d")
    elif message.text == BOOKING_DATE_BUTTONS[1]:
        selected_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif message.text == BOOKING_DATE_BUTTONS[2]:
        await message.answer("Введите дату в формате YYYY-MM-DD")
        return
    else:
        parsed = _parse_iso_date(message.text or "")
        if not parsed:
            await message.answer("Неверный формат даты, используйте YYYY-MM-DD")
            return
        selected_date = parsed

    data = await state.get_data()
    await state.update_data(booking_date=selected_date)
    summary = _format_booking_summary(
        client_name=data.get("client_name"),
        group_name=data.get("group_name"),
        booking_type="single",
        booking_date=selected_date,
    )
    await state.set_state(BookingStates.confirm)
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(BookingStates.confirm)
async def handle_booking_confirm(message: Message, config: Config, state: FSMContext) -> None:
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
    booking_type = data.get("booking_type")
    client_id = int(data.get("client_id"))
    group_id = int(data.get("group_id"))

    if booking_type == "single":
        booking_date = data.get("booking_date")
        created_by = message.from_user.id if message.from_user else None
        created = create_single_visit_booked(
            config.db_path,
            date=booking_date,
            group_id=group_id,
            client_id=client_id,
            created_by=created_by,
        )
        await state.clear()
        if not created:
            await message.answer("Запись уже существует", reply_markup=_main_menu_reply_markup(message, config))
            return
        await message.answer("Готово ✅", reply_markup=_main_menu_reply_markup(message, config))
        return

    upsert_client_group_active(config.db_path, client_id=client_id, group_id=group_id)
    await state.clear()
    await message.answer("Готово ✅", reply_markup=_main_menu_reply_markup(message, config))


@router.message(F.text == MAIN_MENU_BUTTONS[1])
async def handle_search_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(SearchStates.menu)
    await message.answer("Выберите способ поиска", reply_markup=search_menu_keyboard())


@router.message(SearchStates.menu)
async def handle_search_menu_choice(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SEARCH_MENU_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == SEARCH_MENU_BUTTONS[0]:
        await state.set_state(SearchStates.phone)
        await message.answer("Введите телефон клиента", reply_markup=new_client_phone_keyboard())
        return
    if message.text == SEARCH_MENU_BUTTONS[1]:
        await state.set_state(SearchStates.name)
        await message.answer("Введите имя или часть имени", reply_markup=cancel_keyboard())
        return
    if message.text == SEARCH_MENU_BUTTONS[2]:
        await state.set_state(SearchStates.tg_username)
        await message.answer("Введите username (с @ или без)", reply_markup=cancel_keyboard())
        return
    await message.answer("Выберите способ поиска", reply_markup=search_menu_keyboard())


@router.message(SearchStates.phone)
async def handle_search_phone(message: Message, config: Config, state: FSMContext) -> None:
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

    client = get_client_by_phone(config.db_path, normalized)
    if not client:
        await state.clear()
        await message.answer("Не найдено", reply_markup=not_found_keyboard())
        return

    await _show_client_card(message, config, client, state)


@router.message(SearchStates.name)
async def handle_search_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите имя или часть имени")
        return

    results = search_clients_by_name(config.db_path, message.text.strip(), limit=11)
    if len(results) == 0:
        await state.clear()
        await message.answer("Не найдено", reply_markup=not_found_keyboard())
        return
    if len(results) == 1:
        client = get_client_by_id(config.db_path, results[0][0])
        await _show_client_card(message, config, client, state)
        return
    if len(results) > 10:
        await message.answer("Слишком много результатов, уточните запрос")
        return

    labels = [f"{row[1]} ({row[2]})" for row in results]
    mapping = {label: row[0] for label, row in zip(labels, results)}
    await state.update_data(search_results=mapping)
    await state.set_state(SearchStates.select)
    await message.answer("Выберите клиента", reply_markup=search_results_keyboard(labels))


@router.message(SearchStates.tg_username)
async def handle_search_tg(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите username")
        return

    normalized = _normalize_username(message.text)
    if not normalized:
        await message.answer("Введите username")
        return

    client = get_client_by_tg_username(config.db_path, normalized)
    if not client:
        await state.clear()
        await message.answer("Не найдено", reply_markup=not_found_keyboard())
        return

    await _show_client_card(message, config, client, state)


@router.message(SearchStates.select)
async def handle_search_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    data = await state.get_data()
    mapping = data.get("search_results", {})
    if message.text not in mapping:
        await message.answer("Выберите клиента из списка")
        return
    client = get_client_by_id(config.db_path, int(mapping[message.text]))
    await _show_client_card(message, config, client, state)


@router.message(SearchStates.card, F.text == CLIENT_ACTION_BUTTONS[4])
async def handle_client_back_to_search(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(SearchStates.menu)
    await message.answer("Выберите способ поиска", reply_markup=search_menu_keyboard())


@router.message(SearchStates.card, F.text.in_(CLIENT_ACTION_BUTTONS[:4]))
async def handle_client_actions_stub(message: Message) -> None:
    if not message.text:
        return
    await message.answer(f"В разработке: {message.text}")


@router.message(SearchStates.card, F.text == CLIENT_ACTION_BUTTONS[5])
async def handle_client_actions_cancel(message: Message, config: Config, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))


@router.message(F.text == "❌ Отмена", StateFilter(None))
async def handle_cancel_any(message: Message, config: Config, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))


@router.message(
    F.text.in_(MAIN_MENU_BUTTONS)
    & (F.text != MAIN_MENU_BUTTONS[0])
    & (F.text != MAIN_MENU_BUTTONS[1])
    & (F.text != MAIN_MENU_BUTTONS[2])
)
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
