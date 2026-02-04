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
    create_payment_pass,
    create_payment_single,
    create_single_visit_booked,
    create_pass,
    create_expense,
    create_expense_category,
    deactivate_admin,
    get_client_by_id,
    get_client_by_phone,
    get_client_by_tg_username,
    get_active_pass,
    get_expense_by_id,
    get_last_expense,
    get_or_create_single_visit,
    is_admin_active,
    list_clients_for_attendance,
    list_active_groups,
    list_active_passes,
    list_admins,
    list_deferred_payments_by_client,
    list_expense_categories,
    list_expenses,
    search_clients_by_name,
    close_deferred_payment,
    get_payment_by_id,
    get_defer_summary,
    rename_expense_category,
    set_expense_category_active,
    update_expense,
    delete_expense,
    upsert_client_group_active,
    upsert_visit_status,
    upsert_admin,
)
from keyboards import (
    ADMIN_MENU_BUTTONS,
    ADD_GROUP_BUTTONS,
    ATTENDANCE_DATE_BUTTONS,
    ATTENDANCE_STATUS_BUTTONS,
    BOOKING_CLIENT_SEARCH_BUTTONS,
    BOOKING_DATE_BUTTONS,
    BOOKING_TYPE_BUTTONS,
    CLIENT_ACTION_BUTTONS,
    CONFIRM_BUTTONS,
    MAIN_MENU_BUTTONS,
    NEW_CLIENT_PHONE_BUTTONS,
    PAYMENT_CLOSE_DATE_BUTTONS,
    PAYMENT_CLOSE_METHOD_BUTTONS,
    PAYMENT_DATE_BUTTONS,
    PAYMENT_MENU_BUTTONS,
    PAYMENT_METHOD_BUTTONS,
    PAYMENT_TYPE_BUTTONS,
    DEFER_DUE_DATE_BUTTONS,
    EXPENSE_CARD_BUTTONS,
    EXPENSE_CATEGORY_MENU_BUTTONS,
    EXPENSE_COMMENT_BUTTONS,
    EXPENSE_CONFIRM_BUTTONS,
    EXPENSE_DATE_BUTTONS,
    EXPENSE_EDIT_BUTTONS,
    EXPENSE_LIST_PERIOD_BUTTONS,
    EXPENSE_MENU_BUTTONS,
    EXPENSE_METHOD_BUTTONS,
    EXPENSE_CATEGORY_SELECT_ADD,
    EXPENSE_CATEGORY_SELECT_BACK,
    EXPENSE_CATEGORY_SELECT_PREV,
    EXPENSE_CATEGORY_SELECT_NEXT,
    PASS_AFTER_SAVE_BUTTONS,
    PASS_MENU_BUTTONS,
    PASS_PAY_METHOD_BUTTONS,
    SEARCH_MENU_BUTTONS,
    SKIP_BUTTONS,
    add_group_keyboard,
    admin_menu_keyboard,
    attendance_date_keyboard,
    attendance_status_keyboard,
    booking_client_search_keyboard,
    booking_date_keyboard,
    booking_type_keyboard,
    cancel_keyboard,
    client_actions_keyboard,
    confirm_keyboard,
    defer_due_date_keyboard,
    groups_keyboard,
    main_menu_keyboard,
    new_client_phone_keyboard,
    not_found_keyboard,
    payment_close_date_keyboard,
    payment_close_method_keyboard,
    payment_date_keyboard,
    payment_menu_keyboard,
    payment_method_keyboard,
    payment_type_keyboard,
    pass_menu_keyboard,
    passes_after_save_menu_kb,
    pass_pay_method_keyboard,
    categories_selection_keyboard,
    expense_card_keyboard,
    expense_category_menu_keyboard,
    expense_comment_keyboard,
    expense_confirm_keyboard,
    expense_date_keyboard,
    expense_edit_keyboard,
    expense_list_period_keyboard,
    expense_menu_keyboard,
    expense_method_keyboard,
    expense_category_select_keyboard,
    expenses_selection_keyboard,
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


class AttendanceStates(StatesGroup):
    select_group = State()
    select_date = State()
    select_client = State()
    select_status = State()


class PaymentStates(StatesGroup):
    menu = State()
    create_type = State()
    create_client_method = State()
    create_client_phone = State()
    create_client_name = State()
    create_client_tg = State()
    create_client_select = State()
    create_group = State()
    create_date = State()
    create_pass_select = State()
    create_amount = State()
    create_method = State()
    create_due_date = State()
    create_confirm = State()
    close_client_method = State()
    close_client_phone = State()
    close_client_name = State()
    close_client_tg = State()
    close_client_select = State()
    close_payment_select = State()
    close_method = State()
    close_date = State()
    close_confirm = State()


class PassStates(StatesGroup):
    menu = State()
    action = State()
    client_method = State()
    client_phone = State()
    client_name = State()
    client_tg = State()
    client_select = State()
    group_select = State()
    confirm = State()


class PassAfterSave(StatesGroup):
    wait_action = State()


class PassPayStates(StatesGroup):
    choose_method = State()
    enter_amount = State()


class ExpenseStates(StatesGroup):
    menu = State()
    add_date = State()
    add_category = State()
    add_category_create = State()
    add_amount = State()
    add_method = State()
    add_comment = State()
    add_confirm = State()
    add_edit = State()
    list_period = State()
    list_custom_from = State()
    list_custom_to = State()
    list_select = State()
    card = State()
    edit_menu = State()
    edit_category = State()
    edit_amount = State()
    edit_method = State()
    edit_comment = State()
    category_menu = State()
    category_add = State()
    category_rename_select = State()
    category_rename_name = State()
    category_hide_select = State()
    category_show_hidden_select = State()


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


def _format_payment_method_label(method: str) -> str:
    labels = {
        "cash": "Наличные",
        "transfer": "Перевод",
        "qr": "QR",
        "defer": "Отсрочка",
    }
    return labels.get(method, method)


def _parse_amount(text: str) -> Optional[int]:
    if not text:
        return None
    value = text.strip()
    if not value.isdigit():
        return None
    amount = int(value)
    if amount <= 0:
        return None
    return amount


def _last_day_of_month(current: date) -> date:
    next_month = current.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def _next_month_range(current: date) -> tuple[date, date]:
    year = current.year + (1 if current.month == 12 else 0)
    month = 1 if current.month == 12 else current.month + 1
    first_next = date(year, month, 1)
    last_next = _last_day_of_month(first_next)
    return first_next, last_next


def _current_week_range(today_date: date) -> tuple[str, str]:
    start = today_date - timedelta(days=today_date.weekday())
    return start.strftime("%Y-%m-%d"), today_date.strftime("%Y-%m-%d")


def _current_month_range(today_date: date) -> tuple[str, str]:
    start = today_date.replace(day=1)
    return start.strftime("%Y-%m-%d"), today_date.strftime("%Y-%m-%d")


def _expense_categories_page(
    categories: list[list], page: int, page_size: int
) -> tuple[list[list], int]:
    total = len(categories)
    total_pages = max(1, (total + page_size - 1) // page_size)
    safe_page = max(0, min(page, total_pages - 1))
    start_idx = safe_page * page_size
    end_idx = start_idx + page_size
    return categories[start_idx:end_idx], total_pages


async def _show_expense_category_selection(
    message: Message, config: Config, state: FSMContext
) -> None:
    categories = list_expense_categories(config.db_path, include_inactive=False)
    categories_data = [[row[0], row[1]] for row in categories]
    page_size = 12
    page = (await state.get_data()).get("category_page", 0)
    page_items, total_pages = _expense_categories_page(categories_data, page, page_size)
    await state.update_data(categories=categories_data, category_page=page)
    labels = [f"{row[0]}) {row[1]}" for row in page_items]
    show_nav = total_pages > 1
    if not labels:
        await message.answer("Активных категорий нет. Добавьте категорию.")
    await message.answer(
        "Выберите категорию:",
        reply_markup=expense_category_select_keyboard(labels, show_nav),
    )


def _format_payment_summary(
    client_name: str,
    group_name: str,
    payment_type: str,
    amount: int,
    method: str,
    visit_date: Optional[str],
    due_date: Optional[str],
    pass_id: Optional[int],
) -> str:
    type_label = "Разовое" if payment_type == "single" else "Абонемент"
    date_line = f"Дата: {visit_date}" if visit_date else "Дата: —"
    pass_line = f"Абонемент ID: {pass_id}" if pass_id else "Абонемент ID: —"
    due_line = f"Когда оплатят: {due_date}" if due_date else "Когда оплатят: —"
    return (
        "Проверьте данные:\n"
        f"Клиент: {client_name}\n"
        f"Группа: {group_name}\n"
        f"Тип: {type_label}\n"
        f"{date_line}\n"
        f"{pass_line}\n"
        f"Сумма: {amount}\n"
        f"Метод: {_format_payment_method_label(method)}\n"
        f"{due_line}"
    )


def _format_deferred_payment_label(
    pay_id: int,
    amount: int,
    purpose: str,
    group_name: Optional[str],
    due_date: Optional[str],
    created_at: str,
) -> str:
    purpose_label = "Разовое" if purpose == "single" else "Абонемент" if purpose == "pass" else purpose
    group_label = group_name or "—"
    due_label = due_date or "—"
    created_label = created_at.split(" ")[0]
    return f"#{pay_id} {amount} {purpose_label} {group_label} до {due_label} ({created_label})"


def _format_close_payment_summary(
    amount: int,
    purpose: str,
    group_name: Optional[str],
    due_date: Optional[str],
    method: str,
    pay_date: str,
) -> str:
    purpose_label = "Разовое" if purpose == "single" else "Абонемент" if purpose == "pass" else purpose
    group_label = group_name or "—"
    due_label = due_date or "—"
    return (
        "Проверьте данные:\n"
        f"Сумма: {amount}\n"
        f"Тип: {purpose_label}\n"
        f"Группа: {group_label}\n"
        f"Отсрочка до: {due_label}\n"
        f"Метод: {_format_payment_method_label(method)}\n"
        f"Дата оплаты: {pay_date}"
    )


def _format_pass_summary(
    client_name: str,
    group_name: str,
    start_date: str,
    end_date: str,
    is_active: int,
) -> str:
    active_label = "Да" if is_active == 1 else "Нет"
    return (
        "Проверьте данные:\n"
        f"Клиент: {client_name}\n"
        f"Группа: {group_name}\n"
        f"Старт: {start_date}\n"
        f"Конец: {end_date}\n"
        f"Активный: {active_label}"
    )


def _format_expense_method_label(method: str) -> str:
    labels = {
        "cash": "Наличные",
        "transfer": "Перевод",
        "qr": "QR",
    }
    return labels.get(method, method)


def _format_expense_summary(
    exp_date: str,
    category_name: str,
    amount: int,
    method: str,
    comment: Optional[str],
) -> str:
    comment_line = comment if comment else "—"
    return (
        "Проверьте данные:\n"
        f"Дата: {exp_date}\n"
        f"Категория: {category_name}\n"
        f"Сумма: {amount}\n"
        f"Метод: {_format_expense_method_label(method)}\n"
        f"Комментарий: {comment_line}"
    )


def _format_expense_card(
    exp_date: str,
    category_name: str,
    amount: int,
    method: str,
    comment: Optional[str],
) -> str:
    comment_line = comment if comment else "—"
    return (
        "Расход:\n"
        f"Дата: {exp_date}\n"
        f"Категория: {category_name}\n"
        f"Сумма: {amount}\n"
        f"Метод: {_format_expense_method_label(method)}\n"
        f"Комментарий: {comment_line}"
    )


def _active_expense_categories_text(categories: list[tuple[int, str, int]]) -> str:
    if not categories:
        return "Активных категорий нет"
    lines = [f"{row[0]}) {row[1]}" for row in categories]
    return "Активные категории:\n" + "\n".join(lines)




async def _prepare_payment_group_selection(
    message: Message, config: Config, state: FSMContext
) -> bool:
    groups = list_active_groups(config.db_path)
    if not groups:
        await state.clear()
        await message.answer("Групп пока нет", reply_markup=_main_menu_reply_markup(message, config))
        return False
    labels = [_format_group_label(group[0], group[1]) for group in groups]
    mapping = {label: group[0] for label, group in zip(labels, groups)}
    await state.update_data(group_map=mapping, group_names={group[0]: group[1] for group in groups})
    await state.set_state(PaymentStates.create_group)
    await message.answer("Выберите группу", reply_markup=groups_keyboard(labels))
    return True


def _format_attendance_client_label(full_name: str, phone: str) -> str:
    return f"{full_name} ({phone})"


def _format_client_card(
    client_id: int,
    full_name: str,
    phone: str,
    tg_username: Optional[str],
    birth_date: Optional[str],
    comment: Optional[str],
    defer_summary: Optional[tuple[int, int, Optional[str], int]] = None,
) -> str:
    tg_value = tg_username or "—"
    if tg_value != "—" and not tg_value.startswith("@"):
        tg_value = f"@{tg_value}"
    card = (
        "Карточка клиента:\n"
        f"ID: {client_id}\n"
        f"ФИО: {full_name}\n"
        f"Телефон: {phone}\n"
        f"Telegram: {tg_value}\n"
        f"Дата рождения: {birth_date or '—'}\n"
        f"Комментарий: {comment or '—'}"
    )
    if defer_summary:
        cnt, total_amount, nearest_due, overdue_cnt = defer_summary
        if cnt > 0:
            due_label = nearest_due or "без срока"
            card += f"\n\n🕒 Отсрочка: {cnt} / {total_amount} ₽, Ближайший срок: {due_label}"
            if overdue_cnt > 0:
                card += f"\n⚠️ Просрочено: {overdue_cnt}"
    return card


async def _show_client_card(message: Message, config: Config, client, state: Optional[FSMContext]) -> None:
    if not client:
        await message.answer("Клиент не найден", reply_markup=_main_menu_reply_markup(message, config))
        return
    if state is not None:
        await state.clear()
        await state.set_state(SearchStates.card)
    today = date.today().strftime("%Y-%m-%d")
    defer_summary = get_defer_summary(config.db_path, client[0], today)
    card = _format_client_card(
        client_id=client[0],
        full_name=client[1],
        phone=client[2],
        tg_username=client[3],
        birth_date=client[4],
        comment=client[5],
        defer_summary=defer_summary,
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


@router.message(F.text == MAIN_MENU_BUTTONS[3])
async def handle_attendance_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    groups = list_active_groups(config.db_path)
    if not groups:
        await state.clear()
        await message.answer("Групп пока нет", reply_markup=_main_menu_reply_markup(message, config))
        return
    labels = [_format_group_label(group[0], group[1]) for group in groups]
    mapping = {label: group[0] for label, group in zip(labels, groups)}
    await state.clear()
    await state.set_state(AttendanceStates.select_group)
    await state.update_data(group_map=mapping, group_names={group[0]: group[1] for group in groups})
    await message.answer("Выберите группу", reply_markup=groups_keyboard(labels))


@router.message(AttendanceStates.select_group)
async def handle_attendance_select_group(message: Message, config: Config, state: FSMContext) -> None:
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
    await state.set_state(AttendanceStates.select_date)
    await message.answer("Выберите дату", reply_markup=attendance_date_keyboard())


@router.message(AttendanceStates.select_date)
async def handle_attendance_select_date(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == ATTENDANCE_DATE_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == ATTENDANCE_DATE_BUTTONS[0]:
        selected_date = date.today().strftime("%Y-%m-%d")
    elif message.text == ATTENDANCE_DATE_BUTTONS[1]:
        selected_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif message.text == ATTENDANCE_DATE_BUTTONS[2]:
        await message.answer("Введите дату в формате YYYY-MM-DD")
        return
    else:
        parsed = _parse_iso_date(message.text or "")
        if not parsed:
            await message.answer("Неверный формат даты, используйте YYYY-MM-DD")
            return
        selected_date = parsed

    data = await state.get_data()
    group_id = int(data.get("group_id"))
    clients = list_clients_for_attendance(config.db_path, group_id, selected_date)
    if not clients:
        await state.clear()
        await message.answer("Нет клиентов для отметки", reply_markup=_main_menu_reply_markup(message, config))
        return
    labels = [_format_attendance_client_label(row[1], row[2]) for row in clients]
    mapping = {label: row[0] for label, row in zip(labels, clients)}
    await state.update_data(attendance_date=selected_date, client_map=mapping)
    await state.set_state(AttendanceStates.select_client)
    await message.answer("Выберите клиента", reply_markup=search_results_keyboard(labels))


@router.message(AttendanceStates.select_client)
async def handle_attendance_select_client(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    data = await state.get_data()
    mapping = data.get("client_map", {})
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
    await state.set_state(AttendanceStates.select_status)
    await message.answer("Отметить посещение", reply_markup=attendance_status_keyboard())


@router.message(AttendanceStates.select_status)
async def handle_attendance_select_status(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == ATTENDANCE_STATUS_BUTTONS[4]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == ATTENDANCE_STATUS_BUTTONS[3]:
        data = await state.get_data()
        mapping = data.get("client_map", {})
        labels = list(mapping.keys())
        await state.set_state(AttendanceStates.select_client)
        await message.answer("Выберите клиента", reply_markup=search_results_keyboard(labels))
        return

    status_map = {
        ATTENDANCE_STATUS_BUTTONS[0]: "attended",
        ATTENDANCE_STATUS_BUTTONS[1]: "noshow",
        ATTENDANCE_STATUS_BUTTONS[2]: "cancelled",
    }
    if message.text not in status_map:
        await message.answer("Выберите статус", reply_markup=attendance_status_keyboard())
        return

    data = await state.get_data()
    visit_date = data.get("attendance_date")
    group_id = int(data.get("group_id"))
    client_id = int(data.get("client_id"))
    created_by = message.from_user.id if message.from_user else None
    upsert_visit_status(
        config.db_path,
        visit_date=visit_date,
        group_id=group_id,
        client_id=client_id,
        status=status_map[message.text],
        created_by=created_by,
    )
    await state.clear()
    await message.answer("Готово ✅", reply_markup=_main_menu_reply_markup(message, config))


@router.message(F.text == MAIN_MENU_BUTTONS[4], StateFilter(None))
async def handle_payment_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(PaymentStates.menu)
    await message.answer("Оплаты", reply_markup=payment_menu_keyboard())


@router.message(PaymentStates.menu)
async def handle_payment_menu_choice(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PAYMENT_MENU_BUTTONS[2]:
        await state.clear()
        await message.answer("Главное меню", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == PAYMENT_MENU_BUTTONS[0]:
        await state.set_state(PaymentStates.create_type)
        await message.answer("Выберите тип оплаты", reply_markup=payment_type_keyboard())
        return
    if message.text == PAYMENT_MENU_BUTTONS[1]:
        await state.set_state(PaymentStates.close_client_method)
        await message.answer("Выберите способ поиска клиента", reply_markup=booking_client_search_keyboard())
        return
    await message.answer("Выберите действие", reply_markup=payment_menu_keyboard())


@router.message(PaymentStates.create_type)
async def handle_payment_create_type(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PAYMENT_TYPE_BUTTONS[2]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == PAYMENT_TYPE_BUTTONS[0]:
        await state.update_data(payment_type="single")
    elif message.text == PAYMENT_TYPE_BUTTONS[1]:
        await state.update_data(payment_type="pass")
    else:
        await message.answer("Выберите тип оплаты", reply_markup=payment_type_keyboard())
        return
    await state.set_state(PaymentStates.create_client_method)
    await message.answer("Выберите способ поиска клиента", reply_markup=booking_client_search_keyboard())


@router.message(PaymentStates.create_client_method)
async def handle_payment_create_client_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[0]:
        await state.set_state(PaymentStates.create_client_phone)
        await message.answer("Введите телефон клиента", reply_markup=new_client_phone_keyboard())
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[1]:
        await state.set_state(PaymentStates.create_client_name)
        await message.answer("Введите имя или часть имени", reply_markup=cancel_keyboard())
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[2]:
        await state.set_state(PaymentStates.create_client_tg)
        await message.answer("Введите username (с @ или без)", reply_markup=cancel_keyboard())
        return
    await message.answer("Выберите способ поиска клиента", reply_markup=booking_client_search_keyboard())


@router.message(PaymentStates.create_client_phone)
async def handle_payment_create_client_phone(message: Message, config: Config, state: FSMContext) -> None:
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
    await _prepare_payment_group_selection(message, config, state)


@router.message(PaymentStates.create_client_name)
async def handle_payment_create_client_name(message: Message, config: Config, state: FSMContext) -> None:
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
        await _prepare_payment_group_selection(message, config, state)
        return
    if len(results) > 10:
        await message.answer("Слишком много результатов, уточните запрос")
        return

    labels = [f"{row[1]} ({row[2]})" for row in results]
    mapping = {label: row[0] for label, row in zip(labels, results)}
    await state.update_data(search_results=mapping)
    await state.set_state(PaymentStates.create_client_select)
    await message.answer("Выберите клиента", reply_markup=search_results_keyboard(labels))


@router.message(PaymentStates.create_client_tg)
async def handle_payment_create_client_tg(message: Message, config: Config, state: FSMContext) -> None:
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
    await _prepare_payment_group_selection(message, config, state)


@router.message(PaymentStates.create_client_select)
async def handle_payment_create_client_select(message: Message, config: Config, state: FSMContext) -> None:
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
    await _prepare_payment_group_selection(message, config, state)


@router.message(PaymentStates.create_group)
async def handle_payment_create_group(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    data = await state.get_data()
    mapping = data.get("group_map")
    group_names = data.get("group_names")
    if not mapping or not group_names:
        groups = list_active_groups(config.db_path)
        if not groups:
            await state.clear()
            await message.answer("Групп пока нет", reply_markup=_main_menu_reply_markup(message, config))
            return
        labels = [_format_group_label(group[0], group[1]) for group in groups]
        mapping = {label: group[0] for label, group in zip(labels, groups)}
        group_names = {group[0]: group[1] for group in groups}
    if message.text not in mapping:
        await message.answer("Выберите группу из списка")
        return
    group_id = int(mapping[message.text])
    group_name = group_names.get(group_id, message.text)
    await state.update_data(group_id=group_id, group_name=group_name)

    data = await state.get_data()
    if data.get("payment_type") == "single":
        await state.set_state(PaymentStates.create_date)
        await message.answer("Выберите дату", reply_markup=payment_date_keyboard())
        return

    passes = list_active_passes(config.db_path, client_id=int(data.get("client_id")), group_id=group_id)
    if not passes:
        await state.clear()
        await message.answer("Нет активного абонемента — сначала 🎫 Абонемент", reply_markup=_main_menu_reply_markup(message, config))
        return
    if len(passes) == 1:
        await state.update_data(pass_id=passes[0][0])
        await state.set_state(PaymentStates.create_amount)
        await message.answer("Введите сумму", reply_markup=cancel_keyboard())
        return
    labels = [f"ID {row[0]}: {row[1]}–{row[2]}" for row in passes]
    mapping = {label: row[0] for label, row in zip(labels, passes)}
    await state.update_data(pass_map=mapping)
    await state.set_state(PaymentStates.create_pass_select)
    await message.answer("Выберите абонемент", reply_markup=search_results_keyboard(labels))


@router.message(PaymentStates.create_pass_select)
async def handle_payment_create_pass_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    data = await state.get_data()
    mapping = data.get("pass_map", {})
    if message.text not in mapping:
        await message.answer("Выберите абонемент из списка")
        return
    await state.update_data(pass_id=int(mapping[message.text]))
    await state.set_state(PaymentStates.create_amount)
    await message.answer("Введите сумму", reply_markup=cancel_keyboard())


@router.message(PaymentStates.create_date)
async def handle_payment_create_date(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PAYMENT_DATE_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == PAYMENT_DATE_BUTTONS[0]:
        selected_date = date.today().strftime("%Y-%m-%d")
    elif message.text == PAYMENT_DATE_BUTTONS[1]:
        selected_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif message.text == PAYMENT_DATE_BUTTONS[2]:
        await message.answer("Введите дату в формате YYYY-MM-DD")
        return
    else:
        parsed = _parse_iso_date(message.text or "")
        if not parsed:
            await message.answer("Неверный формат даты, используйте YYYY-MM-DD")
            return
        selected_date = parsed

    data = await state.get_data()
    visit_id = get_or_create_single_visit(
        config.db_path,
        client_id=int(data.get("client_id")),
        group_id=int(data.get("group_id")),
        visit_date=selected_date,
        created_by=message.from_user.id if message.from_user else None,
    )
    await state.update_data(visit_date=selected_date, visit_id=visit_id)
    await state.set_state(PaymentStates.create_amount)
    await message.answer("Введите сумму", reply_markup=cancel_keyboard())


@router.message(PaymentStates.create_amount)
async def handle_payment_create_amount(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer("Введите сумму числом")
        return
    await state.update_data(amount=amount)
    await state.set_state(PaymentStates.create_method)
    await message.answer("Выберите способ оплаты", reply_markup=payment_method_keyboard())


@router.message(PaymentStates.create_method)
async def handle_payment_create_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PAYMENT_METHOD_BUTTONS[4]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    method_map = {
        PAYMENT_METHOD_BUTTONS[0]: "cash",
        PAYMENT_METHOD_BUTTONS[1]: "transfer",
        PAYMENT_METHOD_BUTTONS[2]: "qr",
        PAYMENT_METHOD_BUTTONS[3]: "defer",
    }
    if message.text not in method_map:
        await message.answer("Выберите способ оплаты", reply_markup=payment_method_keyboard())
        return
    method = method_map[message.text]
    await state.update_data(method=method)
    if method == "defer":
        await state.set_state(PaymentStates.create_due_date)
        await message.answer("Когда оплатят?", reply_markup=defer_due_date_keyboard())
        return
    await state.update_data(due_date=None)
    await state.set_state(PaymentStates.create_confirm)
    data = await state.get_data()
    summary = _format_payment_summary(
        client_name=data.get("client_name"),
        group_name=data.get("group_name"),
        payment_type=data.get("payment_type"),
        amount=data.get("amount"),
        method=data.get("method"),
        visit_date=data.get("visit_date"),
        due_date=None,
        pass_id=data.get("pass_id"),
    )
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(PaymentStates.create_due_date)
async def handle_payment_create_due_date(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == DEFER_DUE_DATE_BUTTONS[4]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == DEFER_DUE_DATE_BUTTONS[3]:
        due_date = None
    elif message.text == DEFER_DUE_DATE_BUTTONS[0]:
        due_date = date.today().strftime("%Y-%m-%d")
    elif message.text == DEFER_DUE_DATE_BUTTONS[1]:
        due_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    elif message.text == DEFER_DUE_DATE_BUTTONS[2]:
        await message.answer("Введите дату в формате YYYY-MM-DD")
        return
    else:
        parsed = _parse_iso_date(message.text or "")
        if not parsed:
            await message.answer("Неверный формат даты, используйте YYYY-MM-DD")
            return
        due_date = parsed

    await state.update_data(due_date=due_date)
    await state.set_state(PaymentStates.create_confirm)
    data = await state.get_data()
    summary = _format_payment_summary(
        client_name=data.get("client_name"),
        group_name=data.get("group_name"),
        payment_type=data.get("payment_type"),
        amount=data.get("amount"),
        method=data.get("method"),
        visit_date=data.get("visit_date"),
        due_date=due_date,
        pass_id=data.get("pass_id"),
    )
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(PaymentStates.create_confirm)
async def handle_payment_create_confirm(message: Message, config: Config, state: FSMContext) -> None:
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
    method = data.get("method")
    status = "deferred" if method == "defer" else "paid"
    amount = int(data.get("amount"))
    accepted_by = message.from_user.id if message.from_user else None
    if data.get("payment_type") == "single":
        create_payment_single(
            config.db_path,
            client_id=int(data.get("client_id")),
            group_id=int(data.get("group_id")),
            visit_id=int(data.get("visit_id")),
            amount=amount,
            method=method,
            status=status,
            due_date=data.get("due_date"),
            accepted_by=accepted_by,
        )
    else:
        create_payment_pass(
            config.db_path,
            client_id=int(data.get("client_id")),
            group_id=int(data.get("group_id")),
            pass_id=int(data.get("pass_id")),
            amount=amount,
            method=method,
            status=status,
            due_date=data.get("due_date"),
            accepted_by=accepted_by,
        )
    await state.clear()
    if data.get("return_to") == "pass_menu":
        await message.answer("✅ Оплата сохранена", reply_markup=pass_menu_keyboard())
        return
    await message.answer("Готово ✅", reply_markup=_main_menu_reply_markup(message, config))


@router.message(PaymentStates.close_client_method)
async def handle_payment_close_client_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[0]:
        await state.set_state(PaymentStates.close_client_phone)
        await message.answer("Введите телефон клиента", reply_markup=new_client_phone_keyboard())
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[1]:
        await state.set_state(PaymentStates.close_client_name)
        await message.answer("Введите имя или часть имени", reply_markup=cancel_keyboard())
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[2]:
        await state.set_state(PaymentStates.close_client_tg)
        await message.answer("Введите username (с @ или без)", reply_markup=cancel_keyboard())
        return
    await message.answer("Выберите способ поиска клиента", reply_markup=booking_client_search_keyboard())


@router.message(PaymentStates.close_client_phone)
async def handle_payment_close_client_phone(message: Message, config: Config, state: FSMContext) -> None:
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
    await _show_close_deferred_list(message, config, state)


@router.message(PaymentStates.close_client_name)
async def handle_payment_close_client_name(message: Message, config: Config, state: FSMContext) -> None:
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
        await _show_close_deferred_list(message, config, state)
        return
    if len(results) > 10:
        await message.answer("Слишком много результатов, уточните запрос")
        return

    labels = [f"{row[1]} ({row[2]})" for row in results]
    mapping = {label: row[0] for label, row in zip(labels, results)}
    await state.update_data(search_results=mapping)
    await state.set_state(PaymentStates.close_client_select)
    await message.answer("Выберите клиента", reply_markup=search_results_keyboard(labels))


@router.message(PaymentStates.close_client_tg)
async def handle_payment_close_client_tg(message: Message, config: Config, state: FSMContext) -> None:
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
    await _show_close_deferred_list(message, config, state)


@router.message(PaymentStates.close_client_select)
async def handle_payment_close_client_select(message: Message, config: Config, state: FSMContext) -> None:
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
    await _show_close_deferred_list(message, config, state)


async def _show_close_deferred_list(message: Message, config: Config, state: FSMContext) -> None:
    data = await state.get_data()
    client_id = int(data.get("client_id"))
    deferred = list_deferred_payments_by_client(config.db_path, client_id)
    if not deferred:
        await state.clear()
        await message.answer("Нет отсрочек", reply_markup=_main_menu_reply_markup(message, config))
        return
    labels = [
        _format_deferred_payment_label(row[0], row[1], row[2], row[4], row[5], row[6])
        for row in deferred
    ]
    mapping = {label: row[0] for label, row in zip(labels, deferred)}
    details = {
        row[0]: {
            "amount": row[1],
            "purpose": row[2],
            "group_name": row[4],
            "due_date": row[5],
        }
        for row in deferred
    }
    await state.update_data(deferred_map=mapping, deferred_details=details)
    await state.set_state(PaymentStates.close_payment_select)
    await message.answer("Выберите отсрочку", reply_markup=search_results_keyboard(labels))


@router.message(PaymentStates.close_payment_select)
async def handle_payment_close_payment_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    data = await state.get_data()
    mapping = data.get("deferred_map", {})
    if message.text not in mapping:
        await message.answer("Выберите отсрочку из списка")
        return
    pay_id = int(mapping[message.text])
    await state.update_data(pay_id=pay_id)
    await state.set_state(PaymentStates.close_method)
    await message.answer("Выберите метод оплаты", reply_markup=payment_close_method_keyboard())


@router.message(PaymentStates.close_method)
async def handle_payment_close_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PAYMENT_CLOSE_METHOD_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    method_map = {
        PAYMENT_CLOSE_METHOD_BUTTONS[0]: "cash",
        PAYMENT_CLOSE_METHOD_BUTTONS[1]: "transfer",
        PAYMENT_CLOSE_METHOD_BUTTONS[2]: "qr",
    }
    if message.text not in method_map:
        await message.answer("Выберите метод оплаты", reply_markup=payment_close_method_keyboard())
        return
    await state.update_data(close_method=method_map[message.text])
    await state.set_state(PaymentStates.close_date)
    await message.answer("Выберите дату оплаты", reply_markup=payment_close_date_keyboard())


@router.message(PaymentStates.close_date)
async def handle_payment_close_date(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PAYMENT_CLOSE_DATE_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == PAYMENT_CLOSE_DATE_BUTTONS[0]:
        pay_date = date.today().strftime("%Y-%m-%d")
    elif message.text == PAYMENT_CLOSE_DATE_BUTTONS[1]:
        pay_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif message.text == PAYMENT_CLOSE_DATE_BUTTONS[2]:
        await message.answer("Введите дату в формате YYYY-MM-DD")
        return
    else:
        parsed = _parse_iso_date(message.text or "")
        if not parsed:
            await message.answer("Неверный формат даты, используйте YYYY-MM-DD")
            return
        pay_date = parsed
    await state.update_data(pay_date=pay_date)
    data = await state.get_data()
    details = data.get("deferred_details", {}).get(int(data.get("pay_id")), {})
    summary = _format_close_payment_summary(
        amount=details.get("amount"),
        purpose=details.get("purpose"),
        group_name=details.get("group_name"),
        due_date=details.get("due_date"),
        method=data.get("close_method"),
        pay_date=pay_date,
    )
    await state.set_state(PaymentStates.close_confirm)
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(PaymentStates.close_confirm)
async def handle_payment_close_confirm(message: Message, config: Config, state: FSMContext) -> None:
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
    close_deferred_payment(
        config.db_path,
        pay_id=int(data.get("pay_id")),
        new_method=data.get("close_method"),
        pay_date=data.get("pay_date"),
        accepted_by=message.from_user.id if message.from_user else None,
    )
    await state.clear()
    await message.answer("Готово ✅", reply_markup=_main_menu_reply_markup(message, config))


@router.message(F.text == MAIN_MENU_BUTTONS[5])
async def handle_pass_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(PassStates.menu)
    await message.answer("Абонемент", reply_markup=pass_menu_keyboard())


@router.message(PassStates.menu)
async def handle_pass_menu_choice(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PASS_MENU_BUTTONS[2]:
        await state.clear()
        await message.answer("Главное меню", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == PASS_MENU_BUTTONS[0]:
        await state.update_data(pass_action="issue")
    elif message.text == PASS_MENU_BUTTONS[1]:
        await state.update_data(pass_action="extend")
    else:
        await message.answer("Выберите действие", reply_markup=pass_menu_keyboard())
        return
    await state.set_state(PassStates.client_method)
    await message.answer("Выберите способ поиска клиента", reply_markup=booking_client_search_keyboard())


@router.message(PassStates.client_method)
async def handle_pass_client_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[3]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[0]:
        await state.set_state(PassStates.client_phone)
        await message.answer("Введите телефон клиента", reply_markup=new_client_phone_keyboard())
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[1]:
        await state.set_state(PassStates.client_name)
        await message.answer("Введите имя или часть имени", reply_markup=cancel_keyboard())
        return
    if message.text == BOOKING_CLIENT_SEARCH_BUTTONS[2]:
        await state.set_state(PassStates.client_tg)
        await message.answer("Введите username (с @ или без)", reply_markup=cancel_keyboard())
        return
    await message.answer("Выберите способ поиска клиента", reply_markup=booking_client_search_keyboard())


@router.message(PassStates.client_phone)
async def handle_pass_client_phone(message: Message, config: Config, state: FSMContext) -> None:
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
    await state.set_state(PassStates.group_select)
    await message.answer(
        "Выберите группу",
        reply_markup=groups_keyboard([_format_group_label(g[0], g[1]) for g in list_active_groups(config.db_path)]),
    )


@router.message(PassStates.client_name)
async def handle_pass_client_name(message: Message, config: Config, state: FSMContext) -> None:
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
        await state.set_state(PassStates.group_select)
        await message.answer(
            "Выберите группу",
            reply_markup=groups_keyboard([_format_group_label(g[0], g[1]) for g in list_active_groups(config.db_path)]),
        )
        return
    if len(results) > 10:
        await message.answer("Слишком много результатов, уточните запрос")
        return

    labels = [f"{row[1]} ({row[2]})" for row in results]
    mapping = {label: row[0] for label, row in zip(labels, results)}
    await state.update_data(search_results=mapping)
    await state.set_state(PassStates.client_select)
    await message.answer("Выберите клиента", reply_markup=search_results_keyboard(labels))


@router.message(PassStates.client_tg)
async def handle_pass_client_tg(message: Message, config: Config, state: FSMContext) -> None:
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
    await state.set_state(PassStates.group_select)
    await message.answer(
        "Выберите группу",
        reply_markup=groups_keyboard([_format_group_label(g[0], g[1]) for g in list_active_groups(config.db_path)]),
    )


@router.message(PassStates.client_select)
async def handle_pass_client_select(message: Message, config: Config, state: FSMContext) -> None:
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
    await state.set_state(PassStates.group_select)
    await message.answer(
        "Выберите группу",
        reply_markup=groups_keyboard([_format_group_label(g[0], g[1]) for g in list_active_groups(config.db_path)]),
    )


@router.message(PassStates.group_select)
async def handle_pass_group_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    groups = list_active_groups(config.db_path)
    if not groups:
        await state.clear()
        await message.answer("Групп пока нет", reply_markup=_main_menu_reply_markup(message, config))
        return
    mapping = { _format_group_label(g[0], g[1]): g[0] for g in groups }
    names = { g[0]: g[1] for g in groups }
    if message.text not in mapping:
        await message.answer("Выберите группу из списка")
        return
    group_id = int(mapping[message.text])
    group_name = names.get(group_id, message.text)
    data = await state.get_data()
    client_id = int(data.get("client_id"))
    today_str = date.today().strftime("%Y-%m-%d")
    active_pass = get_active_pass(config.db_path, client_id, group_id, today_str)
    action = data.get("pass_action")
    if action == "issue":
        if active_pass:
            await state.clear()
            await message.answer(
                f"У клиента уже есть активный абонемент до {active_pass[2]}",
                reply_markup=_main_menu_reply_markup(message, config),
            )
            return
        start_date = today_str
        end_date = _last_day_of_month(date.today()).strftime("%Y-%m-%d")
        await state.update_data(
            group_id=group_id,
            group_name=group_name,
            pass_start=start_date,
            pass_end=end_date,
            pass_active=1,
        )
        summary = _format_pass_summary(
            client_name=data.get("client_name"),
            group_name=group_name,
            start_date=start_date,
            end_date=end_date,
            is_active=1,
        )
        await state.set_state(PassStates.confirm)
        await message.answer(summary, reply_markup=confirm_keyboard())
        return

    if not active_pass:
        await state.clear()
        await message.answer(
            "Нет активного абонемента — сначала 🎫 Выдать",
            reply_markup=_main_menu_reply_markup(message, config),
        )
        return

    next_start, next_end = _next_month_range(date.today())
    await state.update_data(
        group_id=group_id,
        group_name=group_name,
        pass_start=next_start.strftime("%Y-%m-%d"),
        pass_end=next_end.strftime("%Y-%m-%d"),
        pass_active=0,
    )
    summary = _format_pass_summary(
        client_name=data.get("client_name"),
        group_name=group_name,
        start_date=next_start.strftime("%Y-%m-%d"),
        end_date=next_end.strftime("%Y-%m-%d"),
        is_active=0,
    )
    await state.set_state(PassStates.confirm)
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(PassStates.confirm)
async def handle_pass_confirm(message: Message, config: Config, state: FSMContext) -> None:
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
    try:
        pass_id = create_pass(
            config.db_path,
            client_id=int(data.get("client_id")),
            group_id=int(data.get("group_id")),
            start_date=data.get("pass_start"),
            end_date=data.get("pass_end"),
            is_active=int(data.get("pass_active")),
        )
    except sqlite3.IntegrityError:
        await state.clear()
        await message.answer(
            "У клиента уже есть активный абонемент",
            reply_markup=_main_menu_reply_markup(message, config),
        )
        return
    upsert_client_group_active(
        config.db_path,
        client_id=int(data.get("client_id")),
        group_id=int(data.get("group_id")),
    )
    action = data.get("pass_action")
    status_label = "активный" if int(data.get("pass_active")) == 1 else "неактивный (будущий)"
    header = "✅ Абонемент выдан" if action == "issue" else "✅ Абонемент продлён (создан на следующий месяц)"
    text = (
        f"{header}\n"
        f"Клиент: {data.get('client_name')}\n"
        f"Группа: {data.get('group_name')}\n"
        f"Даты: {data.get('pass_start')} – {data.get('pass_end')}\n"
        f"Статус: {status_label}"
    )
    await state.set_state(PassAfterSave.wait_action)
    await state.update_data(
        client_id=int(data.get("client_id")),
        client_name=data.get("client_name"),
        group_id=int(data.get("group_id")),
        group_name=data.get("group_name"),
        pass_id=pass_id,
        purpose="pass",
    )
    await message.answer(text, reply_markup=passes_after_save_menu_kb())


@router.message(PassAfterSave.wait_action)
async def handle_pass_after_save_action(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PASS_AFTER_SAVE_BUTTONS[0]:
        await state.set_state(PassPayStates.choose_method)
        await message.answer("Выберите способ оплаты:", reply_markup=pass_pay_method_keyboard())
        return
    if message.text == PASS_AFTER_SAVE_BUTTONS[1]:
        await state.clear()
        await state.set_state(PassStates.menu)
        await message.answer("Абонемент", reply_markup=pass_menu_keyboard())
        return
    await message.answer("Выберите действие кнопками меню ниже", reply_markup=passes_after_save_menu_kb())


@router.message(PassPayStates.choose_method)
async def handle_pass_pay_choose_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == PASS_PAY_METHOD_BUTTONS[4]:
        await state.clear()
        await state.set_state(PassStates.menu)
        await message.answer("Абонемент", reply_markup=pass_menu_keyboard())
        return
    method_map = {
        PASS_PAY_METHOD_BUTTONS[0]: "cash",
        PASS_PAY_METHOD_BUTTONS[1]: "transfer",
        PASS_PAY_METHOD_BUTTONS[2]: "qr",
        PASS_PAY_METHOD_BUTTONS[3]: "defer",
    }
    if message.text not in method_map:
        await message.answer("Выберите способ оплаты:", reply_markup=pass_pay_method_keyboard())
        return
    await state.update_data(method=method_map[message.text])
    await state.set_state(PassPayStates.enter_amount)
    await message.answer("Введите сумму (числом):")


@router.message(PassPayStates.enter_amount)
async def handle_pass_pay_amount(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer("Введите сумму (числом):")
        return
    data = await state.get_data()
    method = data.get("method")
    status = "deferred" if method == "defer" else "paid"
    create_payment_pass(
        config.db_path,
        client_id=int(data.get("client_id")),
        group_id=int(data.get("group_id")),
        pass_id=int(data.get("pass_id")),
        amount=amount,
        method=method,
        status=status,
        due_date=None,
        accepted_by=message.from_user.id if message.from_user else None,
    )
    await state.clear()
    await message.answer(
        f"✅ Оплата сохранена: {amount} ({_format_payment_method_label(method)})",
        reply_markup=pass_menu_keyboard(),
    )


@router.message(F.text == MAIN_MENU_BUTTONS[6], StateFilter(None))
async def handle_expense_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(ExpenseStates.menu)
    await message.answer("Расходы", reply_markup=expense_menu_keyboard())


@router.message(ExpenseStates.menu)
async def handle_expense_menu_choice(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_MENU_BUTTONS[3]:
        await state.clear()
        await message.answer("Главное меню", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == EXPENSE_MENU_BUTTONS[0]:
        await state.set_state(ExpenseStates.add_date)
        await message.answer("Выберите дату", reply_markup=expense_date_keyboard())
        return
    if message.text == EXPENSE_MENU_BUTTONS[1]:
        await state.set_state(ExpenseStates.list_period)
        await message.answer("Выберите период", reply_markup=expense_list_period_keyboard())
        return
    if message.text == EXPENSE_MENU_BUTTONS[2]:
        await state.set_state(ExpenseStates.category_menu)
        categories = list_expense_categories(config.db_path, include_inactive=False)
        await message.answer(
            _active_expense_categories_text(categories),
            reply_markup=expense_category_menu_keyboard(),
        )
        return
    await message.answer("Выберите действие", reply_markup=expense_menu_keyboard())


@router.message(ExpenseStates.add_date)
async def handle_expense_add_date(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_DATE_BUTTONS[4]:
        await state.set_state(ExpenseStates.menu)
        await message.answer("Расходы", reply_markup=expense_menu_keyboard())
        return
    if message.text == EXPENSE_DATE_BUTTONS[3]:
        created_by = message.from_user.id if message.from_user else 0
        last_expense = get_last_expense(config.db_path, created_by)
        if not last_expense:
            await message.answer("Нет предыдущих расходов")
            return
        exp_date, category_id, amount, method, comment = (
            last_expense[1],
            last_expense[2],
            last_expense[3],
            last_expense[4],
            last_expense[5],
        )
        categories = list_expense_categories(config.db_path, include_inactive=True)
        category_name = next((c[1] for c in categories if c[0] == category_id), "—")
        await state.update_data(
            exp_date=exp_date,
            category_id=category_id,
            category_name=category_name,
            amount=amount,
            method=method,
            comment=comment,
        )
        await state.set_state(ExpenseStates.add_confirm)
        summary = _format_expense_summary(exp_date, category_name, amount, method, comment)
        await message.answer(summary, reply_markup=expense_confirm_keyboard())
        return
    if message.text == EXPENSE_DATE_BUTTONS[0]:
        exp_date = date.today().strftime("%Y-%m-%d")
    elif message.text == EXPENSE_DATE_BUTTONS[1]:
        exp_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    elif message.text == EXPENSE_DATE_BUTTONS[2]:
        await message.answer("Введите дату в формате YYYY-MM-DD")
        return
    else:
        parsed = _parse_iso_date(message.text or "")
        if not parsed:
            await message.answer("Неверный формат даты, используйте YYYY-MM-DD")
            return
        exp_date = parsed
    await state.update_data(exp_date=exp_date)
    await state.set_state(ExpenseStates.add_category)
    await _show_expense_category_selection(message, config, state)


@router.message(ExpenseStates.add_category)
async def handle_expense_add_category(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_CATEGORY_SELECT_BACK:
        await state.set_state(ExpenseStates.add_date)
        await message.answer("Выберите дату", reply_markup=expense_date_keyboard())
        return
    if message.text == EXPENSE_CATEGORY_SELECT_ADD:
        await state.set_state(ExpenseStates.add_category_create)
        await message.answer("Введите название категории")
        return
    if message.text == EXPENSE_CATEGORY_SELECT_NEXT or message.text == EXPENSE_CATEGORY_SELECT_PREV:
        data = await state.get_data()
        current_page = int(data.get("category_page", 0))
        new_page = current_page + (1 if message.text == EXPENSE_CATEGORY_SELECT_NEXT else -1)
        await state.update_data(category_page=new_page)
        await _show_expense_category_selection(message, config, state)
        return
    match = re.match(r"^(\d+)\)", message.text or "")
    if not match:
        await message.answer("Выберите категорию кнопками ниже")
        await _show_expense_category_selection(message, config, state)
        return
    category_id = int(match.group(1))
    data = await state.get_data()
    categories = data.get("categories", [])
    category_name = next((row[1] for row in categories if row[0] == category_id), None)
    if not category_name:
        await message.answer("Выберите категорию кнопками ниже")
        await _show_expense_category_selection(message, config, state)
        return
    await state.update_data(category_id=category_id, category_name=category_name)
    await state.set_state(ExpenseStates.add_amount)
    await message.answer("Введите сумму")


@router.message(ExpenseStates.add_category_create)
async def handle_expense_add_category_create(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_CATEGORY_SELECT_BACK:
        await state.set_state(ExpenseStates.add_category)
        await _show_expense_category_selection(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите название категории")
        return
    create_expense_category(config.db_path, message.text.strip())
    await state.set_state(ExpenseStates.add_category)
    await _show_expense_category_selection(message, config, state)


@router.message(ExpenseStates.add_amount)
async def handle_expense_add_amount(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer("Введите сумму числом")
        return
    await state.update_data(amount=amount)
    await state.set_state(ExpenseStates.add_method)
    await message.answer("Выберите способ", reply_markup=expense_method_keyboard())


@router.message(ExpenseStates.add_method)
async def handle_expense_add_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_METHOD_BUTTONS[3]:
        await state.set_state(ExpenseStates.add_amount)
        await message.answer("Введите сумму")
        return
    method_map = {
        EXPENSE_METHOD_BUTTONS[0]: "cash",
        EXPENSE_METHOD_BUTTONS[1]: "transfer",
        EXPENSE_METHOD_BUTTONS[2]: "qr",
    }
    if message.text not in method_map:
        await message.answer("Выберите способ", reply_markup=expense_method_keyboard())
        return
    await state.update_data(method=method_map[message.text])
    await state.set_state(ExpenseStates.add_comment)
    await message.answer("Комментарий (опционально)", reply_markup=expense_comment_keyboard())


@router.message(ExpenseStates.add_comment)
async def handle_expense_add_comment(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_COMMENT_BUTTONS[1]:
        await state.set_state(ExpenseStates.add_method)
        await message.answer("Выберите способ", reply_markup=expense_method_keyboard())
        return
    comment = None
    if message.text and message.text not in (EXPENSE_COMMENT_BUTTONS[0],):
        comment = message.text.strip()
    await state.update_data(comment=comment)
    data = await state.get_data()
    summary = _format_expense_summary(
        data.get("exp_date"),
        data.get("category_name"),
        int(data.get("amount")),
        data.get("method"),
        comment,
    )
    await state.set_state(ExpenseStates.add_confirm)
    await message.answer(summary, reply_markup=expense_confirm_keyboard())


@router.message(ExpenseStates.add_confirm)
async def handle_expense_add_confirm(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_CONFIRM_BUTTONS[2]:
        await state.clear()
        await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))
        return
    if message.text == EXPENSE_CONFIRM_BUTTONS[1]:
        await state.set_state(ExpenseStates.add_edit)
        await message.answer("Что изменить?", reply_markup=expense_edit_keyboard())
        return
    if message.text != EXPENSE_CONFIRM_BUTTONS[0]:
        await message.answer("Выберите действие", reply_markup=expense_confirm_keyboard())
        return
    data = await state.get_data()
    create_expense(
        config.db_path,
        exp_date=data.get("exp_date"),
        category_id=int(data.get("category_id")),
        amount=int(data.get("amount")),
        method=data.get("method"),
        comment=data.get("comment"),
        created_by=message.from_user.id if message.from_user else None,
    )
    await state.clear()
    await message.answer("Готово ✅", reply_markup=expense_menu_keyboard())


@router.message(ExpenseStates.add_edit)
async def handle_expense_add_edit_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_EDIT_BUTTONS[4]:
        data = await state.get_data()
        summary = _format_expense_summary(
            data.get("exp_date"),
            data.get("category_name"),
            int(data.get("amount")),
            data.get("method"),
            data.get("comment"),
        )
        await state.set_state(ExpenseStates.add_confirm)
        await message.answer(summary, reply_markup=expense_confirm_keyboard())
        return
    if message.text == EXPENSE_EDIT_BUTTONS[0]:
        categories = list_expense_categories(config.db_path, include_inactive=False)
        labels = [f"{c[1]} (id:{c[0]})" for c in categories]
        mapping = {label: c[0] for label, c in zip(labels, categories)}
        await state.update_data(category_map=mapping, category_names={c[0]: c[1] for c in categories})
        await state.set_state(ExpenseStates.add_category)
        await message.answer("Выберите категорию", reply_markup=categories_selection_keyboard(labels))
        return
    if message.text == EXPENSE_EDIT_BUTTONS[1]:
        await state.set_state(ExpenseStates.add_amount)
        await message.answer("Введите сумму")
        return
    if message.text == EXPENSE_EDIT_BUTTONS[2]:
        await state.set_state(ExpenseStates.add_method)
        await message.answer("Выберите способ", reply_markup=expense_method_keyboard())
        return
    if message.text == EXPENSE_EDIT_BUTTONS[3]:
        await state.set_state(ExpenseStates.add_comment)
        await message.answer("Комментарий (опционально)", reply_markup=expense_comment_keyboard())
        return
    await message.answer("Выберите поле", reply_markup=expense_edit_keyboard())


@router.message(ExpenseStates.list_period)
async def handle_expense_list_period(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_LIST_PERIOD_BUTTONS[4]:
        await state.set_state(ExpenseStates.menu)
        await message.answer("Расходы", reply_markup=expense_menu_keyboard())
        return
    today_date = date.today()
    if message.text == EXPENSE_LIST_PERIOD_BUTTONS[0]:
        date_from = today_date.strftime("%Y-%m-%d")
        date_to = date_from
    elif message.text == EXPENSE_LIST_PERIOD_BUTTONS[1]:
        date_from, date_to = _current_week_range(today_date)
    elif message.text == EXPENSE_LIST_PERIOD_BUTTONS[2]:
        date_from, date_to = _current_month_range(today_date)
    elif message.text == EXPENSE_LIST_PERIOD_BUTTONS[3]:
        await state.set_state(ExpenseStates.list_custom_from)
        await message.answer("Введите дату начала (YYYY-MM-DD)")
        return
    else:
        await message.answer("Выберите период", reply_markup=expense_list_period_keyboard())
        return
    await _show_expense_list(message, config, state, date_from, date_to)


@router.message(ExpenseStates.list_custom_from)
async def handle_expense_list_custom_from(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    parsed = _parse_iso_date(message.text or "")
    if not parsed:
        await message.answer("Неверный формат даты, используйте YYYY-MM-DD")
        return
    await state.update_data(list_from=parsed)
    await state.set_state(ExpenseStates.list_custom_to)
    await message.answer("Введите дату конца (YYYY-MM-DD)")


@router.message(ExpenseStates.list_custom_to)
async def handle_expense_list_custom_to(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    parsed = _parse_iso_date(message.text or "")
    if not parsed:
        await message.answer("Неверный формат даты, используйте YYYY-MM-DD")
        return
    data = await state.get_data()
    await _show_expense_list(message, config, state, data.get("list_from"), parsed)


async def _show_expense_list(
    message: Message, config: Config, state: FSMContext, date_from: str, date_to: str
) -> None:
    expenses = list_expenses(config.db_path, date_from, date_to, limit=30)
    if not expenses:
        await state.set_state(ExpenseStates.menu)
        await message.answer("Расходов нет", reply_markup=expense_menu_keyboard())
        return
    lines = []
    labels = []
    mapping = {}
    for idx, row in enumerate(expenses, start=1):
        label = f"{idx}) {row[1]} • {row[3]} • {row[4]} • {_format_expense_method_label(row[5])}"
        lines.append(label)
        labels.append(label)
        mapping[label] = row[0]
    await state.update_data(expense_map=mapping)
    await state.set_state(ExpenseStates.list_select)
    await message.answer("\n".join(lines), reply_markup=expenses_selection_keyboard(labels))


@router.message(ExpenseStates.list_select)
async def handle_expense_list_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ExpenseStates.list_period)
        await message.answer("Выберите период", reply_markup=expense_list_period_keyboard())
        return
    data = await state.get_data()
    mapping = data.get("expense_map", {})
    if message.text not in mapping:
        await message.answer("Выберите расход из списка")
        return
    expense = get_expense_by_id(config.db_path, int(mapping[message.text]))
    if not expense:
        await message.answer("Расход не найден")
        return
    await state.update_data(expense_id=expense[0])
    await state.set_state(ExpenseStates.card)
    card = _format_expense_card(expense[1], expense[3], expense[4], expense[5], expense[6])
    await message.answer(card, reply_markup=expense_card_keyboard())


@router.message(ExpenseStates.card)
async def handle_expense_card_actions(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_CARD_BUTTONS[2]:
        await state.set_state(ExpenseStates.list_period)
        await message.answer("Выберите период", reply_markup=expense_list_period_keyboard())
        return
    if message.text == EXPENSE_CARD_BUTTONS[1]:
        data = await state.get_data()
        delete_expense(config.db_path, int(data.get("expense_id")))
        await state.set_state(ExpenseStates.menu)
        await message.answer("Удалено ✅", reply_markup=expense_menu_keyboard())
        return
    if message.text == EXPENSE_CARD_BUTTONS[0]:
        await state.set_state(ExpenseStates.edit_menu)
        await message.answer("Что изменить?", reply_markup=expense_edit_keyboard())
        return
    await message.answer("Выберите действие", reply_markup=expense_card_keyboard())


@router.message(ExpenseStates.edit_menu)
async def handle_expense_edit_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_EDIT_BUTTONS[4]:
        data = await state.get_data()
        expense = get_expense_by_id(config.db_path, int(data.get("expense_id")))
        if not expense:
            await message.answer("Расход не найден")
            return
        await state.set_state(ExpenseStates.card)
        card = _format_expense_card(expense[1], expense[3], expense[4], expense[5], expense[6])
        await message.answer(card, reply_markup=expense_card_keyboard())
        return
    if message.text == EXPENSE_EDIT_BUTTONS[0]:
        categories = list_expense_categories(config.db_path, include_inactive=False)
        labels = [f"{c[1]} (id:{c[0]})" for c in categories]
        mapping = {label: c[0] for label, c in zip(labels, categories)}
        await state.update_data(category_map=mapping, category_names={c[0]: c[1] for c in categories})
        await state.set_state(ExpenseStates.edit_category)
        await message.answer("Выберите категорию", reply_markup=categories_selection_keyboard(labels))
        return
    if message.text == EXPENSE_EDIT_BUTTONS[1]:
        await state.set_state(ExpenseStates.edit_amount)
        await message.answer("Введите сумму")
        return
    if message.text == EXPENSE_EDIT_BUTTONS[2]:
        await state.set_state(ExpenseStates.edit_method)
        await message.answer("Выберите способ", reply_markup=expense_method_keyboard())
        return
    if message.text == EXPENSE_EDIT_BUTTONS[3]:
        await state.set_state(ExpenseStates.edit_comment)
        await message.answer("Комментарий (опционально)", reply_markup=expense_comment_keyboard())
        return
    await message.answer("Выберите поле", reply_markup=expense_edit_keyboard())


@router.message(ExpenseStates.edit_category)
async def handle_expense_edit_category(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ExpenseStates.edit_menu)
        await message.answer("Что изменить?", reply_markup=expense_edit_keyboard())
        return
    data = await state.get_data()
    mapping = data.get("category_map", {})
    if message.text not in mapping:
        await message.answer("Выберите категорию из списка")
        return
    update_expense(config.db_path, int(data.get("expense_id")), category_id=int(mapping[message.text]))
    await state.set_state(ExpenseStates.card)
    expense = get_expense_by_id(config.db_path, int(data.get("expense_id")))
    card = _format_expense_card(expense[1], expense[3], expense[4], expense[5], expense[6])
    await message.answer(card, reply_markup=expense_card_keyboard())


@router.message(ExpenseStates.edit_amount)
async def handle_expense_edit_amount(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    amount = _parse_amount(message.text or "")
    if amount is None:
        await message.answer("Введите сумму числом")
        return
    data = await state.get_data()
    update_expense(config.db_path, int(data.get("expense_id")), amount=amount)
    await state.set_state(ExpenseStates.card)
    expense = get_expense_by_id(config.db_path, int(data.get("expense_id")))
    card = _format_expense_card(expense[1], expense[3], expense[4], expense[5], expense[6])
    await message.answer(card, reply_markup=expense_card_keyboard())


@router.message(ExpenseStates.edit_method)
async def handle_expense_edit_method(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_METHOD_BUTTONS[3]:
        await state.set_state(ExpenseStates.edit_menu)
        await message.answer("Что изменить?", reply_markup=expense_edit_keyboard())
        return
    method_map = {
        EXPENSE_METHOD_BUTTONS[0]: "cash",
        EXPENSE_METHOD_BUTTONS[1]: "transfer",
        EXPENSE_METHOD_BUTTONS[2]: "qr",
    }
    if message.text not in method_map:
        await message.answer("Выберите способ", reply_markup=expense_method_keyboard())
        return
    data = await state.get_data()
    update_expense(config.db_path, int(data.get("expense_id")), method=method_map[message.text])
    await state.set_state(ExpenseStates.card)
    expense = get_expense_by_id(config.db_path, int(data.get("expense_id")))
    card = _format_expense_card(expense[1], expense[3], expense[4], expense[5], expense[6])
    await message.answer(card, reply_markup=expense_card_keyboard())


@router.message(ExpenseStates.edit_comment)
async def handle_expense_edit_comment(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_COMMENT_BUTTONS[1]:
        await state.set_state(ExpenseStates.edit_menu)
        await message.answer("Что изменить?", reply_markup=expense_edit_keyboard())
        return
    comment = None
    if message.text and message.text not in (EXPENSE_COMMENT_BUTTONS[0],):
        comment = message.text.strip()
    data = await state.get_data()
    update_expense(config.db_path, int(data.get("expense_id")), comment=comment)
    await state.set_state(ExpenseStates.card)
    expense = get_expense_by_id(config.db_path, int(data.get("expense_id")))
    card = _format_expense_card(expense[1], expense[3], expense[4], expense[5], expense[6])
    await message.answer(card, reply_markup=expense_card_keyboard())


@router.message(ExpenseStates.category_menu)
async def handle_expense_category_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == EXPENSE_CATEGORY_MENU_BUTTONS[4]:
        await state.set_state(ExpenseStates.menu)
        await message.answer("Расходы", reply_markup=expense_menu_keyboard())
        return
    if message.text == "Категории":
        categories = list_expense_categories(config.db_path, include_inactive=False)
        await message.answer(
            _active_expense_categories_text(categories),
            reply_markup=expense_category_menu_keyboard(),
        )
        return
    if message.text == EXPENSE_CATEGORY_MENU_BUTTONS[0]:
        await state.set_state(ExpenseStates.category_add)
        await message.answer("Введите название категории")
        return
    if message.text == EXPENSE_CATEGORY_MENU_BUTTONS[1]:
        categories = list_expense_categories(config.db_path, include_inactive=True)
        if not categories:
            await message.answer("Категорий нет")
            return
        labels = [f"{c[1]} (id:{c[0]})" for c in categories]
        mapping = {label: c[0] for label, c in zip(labels, categories)}
        await state.update_data(category_map=mapping)
        await state.set_state(ExpenseStates.category_rename_select)
        await message.answer("Выберите категорию", reply_markup=categories_selection_keyboard(labels))
        return
    if message.text == EXPENSE_CATEGORY_MENU_BUTTONS[2]:
        categories = list_expense_categories(config.db_path, include_inactive=False)
        if not categories:
            await message.answer("Активных категорий нет")
            return
        labels = [f"{c[1]} (id:{c[0]})" for c in categories]
        mapping = {label: c[0] for label, c in zip(labels, categories)}
        await state.update_data(category_map=mapping)
        await state.set_state(ExpenseStates.category_hide_select)
        await message.answer("Выберите категорию", reply_markup=categories_selection_keyboard(labels))
        return
    if message.text == EXPENSE_CATEGORY_MENU_BUTTONS[3]:
        categories = list_expense_categories(config.db_path, include_inactive=True)
        hidden = [c for c in categories if c[2] == 0]
        if not hidden:
            await message.answer("Скрытых категорий нет")
            return
        labels = [f"{c[1]} (id:{c[0]})" for c in hidden]
        mapping = {label: c[0] for label, c in zip(labels, hidden)}
        await state.update_data(category_map=mapping)
        await state.set_state(ExpenseStates.category_show_hidden_select)
        lines = [f"{row[0]}) {row[1]}" for row in hidden]
        await message.answer("Скрытые категории:\n" + "\n".join(lines))
        await message.answer("Выберите категорию для активации", reply_markup=categories_selection_keyboard(labels))
        return
    await message.answer("Выберите действие", reply_markup=expense_category_menu_keyboard())


@router.message(ExpenseStates.category_add)
async def handle_expense_category_add(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите название категории")
        return
    create_expense_category(config.db_path, message.text.strip())
    await state.set_state(ExpenseStates.category_menu)
    categories = list_expense_categories(config.db_path, include_inactive=False)
    await message.answer("Категория добавлена ✅")
    await message.answer(
        _active_expense_categories_text(categories),
        reply_markup=expense_category_menu_keyboard(),
    )


@router.message(ExpenseStates.category_rename_select)
async def handle_expense_category_rename_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ExpenseStates.category_menu)
        categories = list_expense_categories(config.db_path, include_inactive=False)
        await message.answer(
            _active_expense_categories_text(categories),
            reply_markup=expense_category_menu_keyboard(),
        )
        return
    data = await state.get_data()
    mapping = data.get("category_map", {})
    if message.text not in mapping:
        await message.answer("Выберите категорию из списка")
        return
    await state.update_data(category_id=int(mapping[message.text]))
    await state.set_state(ExpenseStates.category_rename_name)
    await message.answer("Введите новое название")


@router.message(ExpenseStates.category_rename_name)
async def handle_expense_category_rename_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите новое название")
        return
    data = await state.get_data()
    rename_expense_category(config.db_path, int(data.get("category_id")), message.text.strip())
    await state.set_state(ExpenseStates.category_menu)
    categories = list_expense_categories(config.db_path, include_inactive=False)
    await message.answer("Категория переименована ✅")
    await message.answer(
        _active_expense_categories_text(categories),
        reply_markup=expense_category_menu_keyboard(),
    )


@router.message(ExpenseStates.category_hide_select)
async def handle_expense_category_hide_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ExpenseStates.category_menu)
        categories = list_expense_categories(config.db_path, include_inactive=False)
        await message.answer(
            _active_expense_categories_text(categories),
            reply_markup=expense_category_menu_keyboard(),
        )
        return
    data = await state.get_data()
    mapping = data.get("category_map", {})
    if message.text not in mapping:
        await message.answer("Выберите категорию из списка")
        return
    set_expense_category_active(config.db_path, int(mapping[message.text]), False)
    await state.set_state(ExpenseStates.category_menu)
    categories = list_expense_categories(config.db_path, include_inactive=False)
    await message.answer("Категория скрыта ✅")
    await message.answer(
        _active_expense_categories_text(categories),
        reply_markup=expense_category_menu_keyboard(),
    )


@router.message(ExpenseStates.category_show_hidden_select)
async def handle_expense_category_show_hidden_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ExpenseStates.category_menu)
        categories = list_expense_categories(config.db_path, include_inactive=False)
        await message.answer(
            _active_expense_categories_text(categories),
            reply_markup=expense_category_menu_keyboard(),
        )
        return
    data = await state.get_data()
    mapping = data.get("category_map", {})
    if message.text not in mapping:
        await message.answer("Выберите категорию из списка")
        return
    set_expense_category_active(config.db_path, int(mapping[message.text]), True)
    await state.set_state(ExpenseStates.category_menu)
    categories = list_expense_categories(config.db_path, include_inactive=False)
    await message.answer("Категория активирована ✅")
    await message.answer(
        _active_expense_categories_text(categories),
        reply_markup=expense_category_menu_keyboard(),
    )


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
    & (F.text != MAIN_MENU_BUTTONS[3])
    & (F.text != MAIN_MENU_BUTTONS[4])
    & (F.text != MAIN_MENU_BUTTONS[5])
    & (F.text != MAIN_MENU_BUTTONS[6])
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
