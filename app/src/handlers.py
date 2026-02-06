from __future__ import annotations

from datetime import datetime, date, timedelta
import re
import sqlite3
from typing import Optional

from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, Message

from config import Config
from db import (
    create_client,
    create_group,
    create_payment_pass,
    create_payment_single,
    create_single_visit_booked,
    create_trainer,
    create_pass,
    create_expense,
    create_expense_category,
    deactivate_admin,
    get_admin_by_tg_user_id,
    clear_group_trainer,
    get_client_by_id,
    get_client_by_phone,
    get_client_by_tg_username,
    get_active_pass,
    get_expense_by_id,
    get_last_expense,
    get_or_create_single_visit,
    get_group_by_id,
    get_schedule_by_id,
    get_trainer_by_id,
    is_admin_active,
    list_groups,
    list_groups_by_trainer,
    list_clients_for_attendance,
    list_active_groups,
    list_active_passes,
    list_admins,
    set_admin_active,
    list_active_trainers,
    list_deferred_payments_by_client,
    list_expense_categories,
    list_expenses,
    rename_group,
    list_schedule_for_group,
    search_clients_by_name,
    add_schedule_slot,
    update_schedule_slot,
    delete_schedule_slot,
    toggle_schedule_slot,
    set_group_active,
    set_group_trainer,
    set_trainer_active,
    close_deferred_payment,
    get_payment_by_id,
    get_defer_summary,
    rename_expense_category,
    update_trainer_name,
    set_expense_category_active,
    update_expense,
    delete_expense,
    upsert_client_group_active,
    upsert_visit_status,
    upsert_admin,
)
from reporting import (
    build_excel_report,
    count_single_visits,
    count_single_visits_without_payment,
    get_attendance_summary,
    get_deferred_summary,
    get_expense_summary,
    get_revenue_summary,
    list_active_passes_today,
    list_attended_today_by_group,
    list_clients_without_active_pass,
    list_passes_expiring,
    list_single_visits_without_payment,
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
    REPORT_ACTION_BUTTONS,
    REPORT_ATTENDANCE_TODAY_BUTTON,
    REPORT_MENU_BUTTONS,
    REPORT_PERIOD_BUTTONS,
    TRAINERS_MENU_BUTTONS,
    TRAINER_ACTION_BUTTONS,
    GROUPS_MENU_BUTTONS,
    GROUP_ACTION_BUTTONS,
    GROUP_CREATE_ASSIGN_BUTTONS,
    TRAINER_ATTACH_GROUP_NEW,
    TRAINER_ATTACH_GROUP_BACK,
    TRAINER_DETACH_GROUP_BACK,
    GROUP_ASSIGN_TRAINER_NEW,
    GROUP_ASSIGN_TRAINER_BACK,
    ADMIN_MANAGE_BUTTONS,
    SCHEDULE_MENU_BUTTONS,
    SCHEDULE_WEEKDAY_BUTTONS,
    SCHEDULE_EDIT_BUTTONS,
    SCHEDULE_DELETE_BUTTONS,
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
    admin_select_keyboard,
    admin_manage_keyboard,
    report_actions_keyboard,
    report_date_input_keyboard,
    report_menu_keyboard,
    report_period_keyboard,
    trainers_menu_keyboard,
    trainers_list_keyboard,
    trainer_actions_keyboard,
    trainer_attach_group_keyboard,
    trainer_detach_group_keyboard,
    groups_menu_keyboard,
    groups_list_keyboard,
    group_actions_keyboard,
    group_assign_trainer_keyboard,
    group_create_assign_keyboard,
    schedule_menu_keyboard,
    schedule_weekday_keyboard,
    schedule_time_keyboard,
    schedule_duration_keyboard,
    schedule_room_keyboard,
    schedule_slots_keyboard,
    schedule_edit_keyboard,
    schedule_delete_confirm_keyboard,
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

DEFER_OVERDUE_DAYS = 7
REPORT_UNPAID_SINGLE_LIMIT = 20


class AdminStates(StatesGroup):
    menu = State()
    add_tg_id = State()
    add_name = State()
    disable_tg_id = State()
    manage_select = State()
    manage_action = State()


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


class ReportStates(StatesGroup):
    menu = State()
    view = State()
    period_menu = State()
    period_custom_from = State()
    period_custom_to = State()
    attendance_today_group = State()


class TrainerStates(StatesGroup):
    menu = State()
    add_name = State()
    add_phone = State()
    add_tg = State()
    add_confirm = State()
    list_select = State()
    card = State()
    attach_group_select = State()
    create_group_name = State()
    create_group_capacity = State()
    create_group_room = State()
    detach_group_select = State()
    rename = State()


class GroupStates(StatesGroup):
    menu = State()
    create_name = State()
    create_capacity = State()
    create_room = State()
    create_assign = State()
    create_assign_select = State()
    create_trainer_name = State()
    create_confirm = State()
    list_select = State()
    card = State()
    assign_trainer_select = State()
    assign_trainer_name = State()
    rename = State()


class ScheduleStates(StatesGroup):
    menu = State()
    add_weekday = State()
    add_time = State()
    add_duration = State()
    add_room = State()
    add_confirm = State()
    edit_select = State()
    edit_menu = State()
    edit_time = State()
    edit_duration = State()
    edit_room = State()
    delete_select = State()
    delete_confirm = State()


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


def _format_choice_label(item_id: int, name: str) -> str:
    return f"{item_id}) {name}"


def _parse_choice_id(text: str) -> Optional[int]:
    if not text:
        return None
    if ")" not in text:
        return None
    prefix = text.split(")", 1)[0].strip()
    if not prefix.isdigit():
        return None
    return int(prefix)


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


def _previous_month_range(today_date: date) -> tuple[str, str]:
    first_this = today_date.replace(day=1)
    last_prev = first_this - timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    return first_prev.strftime("%Y-%m-%d"), last_prev.strftime("%Y-%m-%d")


async def _ensure_report_period(state: FSMContext, today_date: date) -> tuple[str, str, str]:
    data = await state.get_data()
    date_from = data.get("report_date_from")
    date_to = data.get("report_date_to")
    label = data.get("report_period_label")
    if not date_from or not date_to:
        date_from, date_to = _current_month_range(today_date)
        label = "Этот месяц"
        await state.update_data(
            report_date_from=date_from,
            report_date_to=date_to,
            report_period_label=label,
        )
    return str(date_from), str(date_to), str(label or "")


def _period_label(date_from: str, date_to: str, label: Optional[str]) -> str:
    base = label or f"{date_from} — {date_to}"
    return f"Период: {base} ({date_from} — {date_to})"


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


def _format_revenue_report(period_line: str, summary) -> str:
    return (
        f"{period_line}\n"
        f"Выручка за период: {summary.total} ₽\n"
        f"Наличные: {summary.cash} ₽\n"
        f"Перевод: {summary.transfer} ₽\n"
        f"QR: {summary.qr} ₽\n"
        f"Платежей: {summary.count}"
    )


def _format_expense_report(period_line: str, summary) -> str:
    lines = [
        f"{period_line}",
        f"Расходы за период: {summary.total} ₽",
        f"Наличные: {summary.cash} ₽ / Перевод: {summary.transfer} ₽ / QR: {summary.qr} ₽",
    ]
    if summary.categories:
        lines.append("Категории:")
        for name, amount in summary.categories:
            lines.append(f"- {name}: {amount} ₽")
        if summary.other_amount:
            lines.append(f"- Прочие: {summary.other_amount} ₽")
    return "\n".join(lines)


def _format_profit_report(period_line: str, revenue_total: int, expense_total: int) -> str:
    profit = revenue_total - expense_total
    return (
        f"{period_line}\n"
        f"Выручка: {revenue_total} ₽\n"
        f"Расходы: {expense_total} ₽\n"
        f"Прибыль: {profit} ₽"
    )


def _format_attendance_report(period_line: str, summary) -> str:
    return (
        f"{period_line}\n"
        "Посещаемость:\n"
        f"attended: {summary.attended}\n"
        f"noshow: {summary.noshow}\n"
        f"cancelled: {summary.cancelled}\n"
        f"booked: {summary.booked}"
    )


def _format_passes_report(
    today_label: str,
    active_passes: list[tuple[str, str, str, str]],
    expiring: list[tuple[str, str, str]],
    missing: list[tuple[str, str]],
) -> str:
    lines = [
        f"Дата: {today_label}",
        f"Активные абонементы: {len(active_passes)}",
        f"Заканчиваются в ближайшие 7 дней: {len(expiring)}",
        f"Постоянные без активного абонемента: {len(missing)}",
    ]
    if expiring:
        lines.append("Заканчиваются:")
        for full_name, group_name, end_date in expiring:
            lines.append(f"- {full_name} / {group_name} до {end_date}")
    if missing:
        lines.append("Без активного абонемента:")
        for full_name, group_name in missing:
            lines.append(f"- {full_name} / {group_name}")
    return "\n".join(lines)


def _format_single_visits_report(
    period_line: str,
    total_single: int,
    total_unpaid: int,
    unpaid: list[tuple[str, str, str, str]],
    unpaid_limit: int,
) -> str:
    lines = [
        f"{period_line}",
        f"Разовые визиты (booked/attended): {total_single}",
        f"Разовые без оплаты: {total_unpaid}",
    ]
    if unpaid:
        lines.append("Без оплаты:")
        for visit_date, full_name, group_name, status in unpaid:
            lines.append(f"- {visit_date} / {full_name} / {group_name} / {status}")
        if total_unpaid > len(unpaid):
            lines.append(f"Показаны первые {unpaid_limit}")
    return "\n".join(lines)


def _format_deferred_report(
    period_line: str,
    total_count: int,
    total_amount: int,
    latest: list[tuple[int, str, str, int, str, Optional[str]]],
    overdue: list[tuple[int, str, str, int, str]],
    overdue_days: int,
) -> str:
    lines = [
        f"{period_line}",
        f"Отсрочек за период: {total_count} / {total_amount} ₽",
    ]
    if latest:
        lines.append("Последние 10 отсрочек:")
        for pay_id, client_name, group_name, amount, created_date, due_date in latest:
            due_label = due_date or "—"
            lines.append(
                f"- #{pay_id} {client_name} / {group_name} / {amount} ₽ / {created_date} / до {due_label}"
            )
    if overdue:
        lines.append(f"Просроченные (старше {overdue_days} дней):")
        for pay_id, client_name, group_name, amount, created_date in overdue:
            lines.append(f"- #{pay_id} {client_name} / {group_name} / {amount} ₽ / {created_date}")
    return "\n".join(lines)




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


def _format_trainer_card(trainer: tuple, groups: list[tuple]) -> str:
    trainer_id, full_name, phone, tg_user_id, tg_username, is_active = trainer
    phone_line = phone or "—"
    tg_value = tg_username or "—"
    if tg_value != "—" and not tg_value.startswith("@"):
        tg_value = f"@{tg_value}"
    status_label = "active" if int(is_active) == 1 else "inactive"
    if groups:
        group_lines = [f"- {_format_choice_label(g[0], g[1])}" for g in groups]
        groups_text = "\n".join(group_lines)
    else:
        groups_text = "нет групп"
    return (
        f"Тренер: {full_name}\n"
        f"Телефон: {phone_line}\n"
        f"TG: {tg_value}\n"
        f"Статус: {status_label}\n"
        f"Группы:\n{groups_text}"
    )


def _format_group_card(group: tuple) -> str:
    group_id, name, trainer_id, trainer_name, capacity, room_name, is_active = group
    trainer_label = trainer_name or "не назначен"
    capacity_label = capacity if capacity is not None else 0
    room_label = room_name or "—"
    status_label = "active" if int(is_active) == 1 else "inactive"
    return (
        f"Группа: {name}\n"
        f"Тренер: {trainer_label}\n"
        f"Вместимость: {capacity_label}\n"
        f"Зал: {room_label}\n"
        f"Статус: {status_label}"
    )


_WEEKDAY_LABELS = {
    1: "Пн",
    2: "Вт",
    3: "Ср",
    4: "Чт",
    5: "Пт",
    6: "Сб",
    7: "Вс",
}
_WEEKDAY_TEXT_TO_NUM = {value: key for key, value in _WEEKDAY_LABELS.items()}


def _weekday_label(weekday: int) -> str:
    return _WEEKDAY_LABELS.get(weekday, str(weekday))


def _parse_hhmm(value: str) -> Optional[str]:
    value = value.strip()
    try:
        parsed = datetime.strptime(value, "%H:%M")
    except ValueError:
        return None
    return parsed.strftime("%H:%M")


def _format_schedule_slot(day_of_week: int, time_hhmm: str, duration_min: int, room_name: Optional[str]) -> str:
    base = f"{_weekday_label(day_of_week)} {time_hhmm} ({duration_min}м)"
    if room_name:
        return f"{base}, зал: {room_name}"
    return base


def _format_schedule_list(group_name: str, slots: list[tuple]) -> str:
    if not slots:
        return f"Расписание группы {group_name}:\nнет занятий"
    lines = [f"Расписание группы {group_name}:"]
    for slot in slots:
        _, day_of_week, time_hhmm, duration_min, room_name, is_active = slot
        line = _format_schedule_slot(day_of_week, time_hhmm, duration_min, room_name)
        if int(is_active) == 0:
            line = f"{line} ⛔"
        lines.append(line)
    return "\n".join(lines)


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
        await state.update_data(client_id=client[0], client_name=client[1], client_phone=client[2])
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

    today_str = date.today().strftime("%Y-%m-%d")
    end_date = _last_day_of_month(date.today()).strftime("%Y-%m-%d")
    try:
        pass_id = create_pass(
            config.db_path,
            client_id=client_id,
            group_id=group_id,
            start_date=today_str,
            end_date=end_date,
            is_active=1,
        )
    except sqlite3.IntegrityError:
        await state.clear()
        await message.answer(
            "У клиента уже есть активный абонемент",
            reply_markup=_main_menu_reply_markup(message, config),
        )
        return
    upsert_client_group_active(config.db_path, client_id=client_id, group_id=group_id)
    await state.set_state(PassPayStates.choose_method)
    await state.update_data(
        client_id=client_id,
        client_name=data.get("client_name"),
        group_id=group_id,
        group_name=data.get("group_name"),
        pass_id=pass_id,
        method=None,
    )
    await message.answer(
        f"✅ Абонемент выдан ({today_str} – {end_date}). Выберите способ оплаты:",
        reply_markup=pass_pay_method_keyboard(),
    )


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
    prefill_id = data.get("prefill_client_id")
    if prefill_id:
        matched = next((row for row in clients if row[0] == int(prefill_id)), None)
        if matched:
            await state.update_data(
                attendance_date=selected_date,
                client_map=mapping,
                client_id=int(prefill_id),
                client_name=matched[1],
            )
            await state.set_state(AttendanceStates.select_status)
            await message.answer("Отметить посещение", reply_markup=attendance_status_keyboard())
            return
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
    data = await state.get_data()
    prefill_id = data.get("prefill_client_id")
    if prefill_id:
        await state.update_data(client_id=prefill_id, client_name=data.get("prefill_client_name"))
        await _prepare_payment_group_selection(message, config, state)
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
async def handle_client_actions(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text:
        return
    data = await state.get_data()
    client_id = data.get("client_id")
    client_name = data.get("client_name")
    if not client_id:
        await message.answer("Клиент не выбран")
        return
    if message.text == CLIENT_ACTION_BUTTONS[0]:
        await state.clear()
        await state.set_state(BookingStates.select_type)
        await state.update_data(client_id=client_id, client_name=client_name)
        await message.answer("Выберите тип записи", reply_markup=booking_type_keyboard())
        return
    if message.text == CLIENT_ACTION_BUTTONS[1]:
        groups = list_active_groups(config.db_path)
        if not groups:
            await state.clear()
            await message.answer("Групп пока нет", reply_markup=_main_menu_reply_markup(message, config))
            return
        labels = [_format_group_label(group[0], group[1]) for group in groups]
        mapping = {label: group[0] for label, group in zip(labels, groups)}
        await state.clear()
        await state.set_state(AttendanceStates.select_group)
        await state.update_data(
            group_map=mapping,
            group_names={group[0]: group[1] for group in groups},
            prefill_client_id=client_id,
            prefill_client_name=client_name,
        )
        await message.answer("Выберите группу", reply_markup=groups_keyboard(labels))
        return
    if message.text == CLIENT_ACTION_BUTTONS[2]:
        await state.clear()
        await state.set_state(PaymentStates.create_type)
        await state.update_data(prefill_client_id=client_id, prefill_client_name=client_name)
        await message.answer("Выберите тип оплаты", reply_markup=payment_type_keyboard())
        return
    if message.text == CLIENT_ACTION_BUTTONS[3]:
        await state.clear()
        await state.set_state(PassStates.menu)
        await state.update_data(prefill_client_id=client_id, prefill_client_name=client_name)
        await message.answer("Абонемент", reply_markup=pass_menu_keyboard())
        return


@router.message(SearchStates.card, F.text == CLIENT_ACTION_BUTTONS[5])
async def handle_client_actions_cancel(message: Message, config: Config, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))


@router.message(F.text == "❌ Отмена", StateFilter(None))
async def handle_cancel_any(message: Message, config: Config, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отмена", reply_markup=_main_menu_reply_markup(message, config))


@router.message(F.text == MAIN_MENU_BUTTONS[7])
async def handle_reports_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(ReportStates.menu)
    await _ensure_report_period(state, date.today())
    await message.answer("Отчеты", reply_markup=report_menu_keyboard())


@router.message(F.text == MAIN_MENU_BUTTONS[8])
async def handle_trainers_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(TrainerStates.menu)
    await message.answer("Тренеры", reply_markup=trainers_menu_keyboard())


@router.message(F.text == MAIN_MENU_BUTTONS[9])
async def handle_groups_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.clear()
    await state.set_state(GroupStates.menu)
    await message.answer("Группы", reply_markup=groups_menu_keyboard())


@router.message(
    F.text.in_(MAIN_MENU_BUTTONS)
    & (F.text != MAIN_MENU_BUTTONS[0])
    & (F.text != MAIN_MENU_BUTTONS[1])
    & (F.text != MAIN_MENU_BUTTONS[2])
    & (F.text != MAIN_MENU_BUTTONS[3])
    & (F.text != MAIN_MENU_BUTTONS[4])
    & (F.text != MAIN_MENU_BUTTONS[5])
    & (F.text != MAIN_MENU_BUTTONS[6])
    & (F.text != MAIN_MENU_BUTTONS[7])
    & (F.text != MAIN_MENU_BUTTONS[8])
    & (F.text != MAIN_MENU_BUTTONS[9])
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
    await state.set_state(AdminStates.menu)
    await message.answer("Меню админов", reply_markup=admin_menu_keyboard())


@router.message(AdminStates.menu, F.text == ADMIN_MENU_BUTTONS[0])
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
    if message.text == ADMIN_MENU_BUTTONS[3]:
        await state.clear()
        await message.answer("Меню админов", reply_markup=admin_menu_keyboard())
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
    if message.text == ADMIN_MENU_BUTTONS[3]:
        await state.clear()
        await message.answer("Меню админов", reply_markup=admin_menu_keyboard())
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Имя не может быть пустым")
        return
    data = await state.get_data()
    tg_user_id = int(data["tg_user_id"])
    upsert_admin(config.db_path, tg_user_id=tg_user_id, name=message.text.strip())
    await state.clear()
    await message.answer("Админ сохранен и активирован ✅", reply_markup=admin_menu_keyboard())


@router.message(AdminStates.menu, F.text == ADMIN_MENU_BUTTONS[1])
async def handle_admin_disable_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    active, inactive = list_admins(config.db_path)
    combined = active + inactive
    if not combined:
        await message.answer("Админов пока нет", reply_markup=admin_menu_keyboard())
        return
    labels = [
        _format_choice_label(rec.tg_user_id, f"{rec.name} ({'active' if rec.is_active else 'inactive'})")
        for rec in combined
    ]
    await state.set_state(AdminStates.manage_select)
    await message.answer("Выберите админа", reply_markup=admin_select_keyboard(labels))


@router.message(AdminStates.disable_tg_id)
async def handle_admin_disable_tg_id(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    if message.text == ADMIN_MENU_BUTTONS[3]:
        await state.clear()
        await message.answer("Меню админов", reply_markup=admin_menu_keyboard())
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


@router.message(AdminStates.manage_select)
async def handle_admin_manage_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    if message.text == ADMIN_MENU_BUTTONS[3]:
        await state.clear()
        await message.answer("Меню админов", reply_markup=admin_menu_keyboard())
        return
    admin_id = _parse_choice_id(message.text or "")
    if admin_id is None:
        await message.answer("Выберите админа из списка")
        return
    admin = get_admin_by_tg_user_id(config.db_path, admin_id)
    if not admin:
        await message.answer("Админ не найден", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    await state.update_data(manage_admin_id=admin.tg_user_id, manage_admin_active=admin.is_active)
    await state.set_state(AdminStates.manage_action)
    await message.answer(
        f"Админ: {admin.name} ({admin.tg_user_id})",
        reply_markup=admin_manage_keyboard(is_active=bool(admin.is_active)),
    )


@router.message(AdminStates.manage_action)
async def handle_admin_manage_action(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    if message.text == ADMIN_MANAGE_BUTTONS[2]:
        await handle_admin_disable_start(message, config, state)
        return
    data = await state.get_data()
    admin_id = data.get("manage_admin_id")
    if not admin_id:
        await handle_admin_disable_start(message, config, state)
        return
    if message.text == ADMIN_MANAGE_BUTTONS[0]:
        set_admin_active(config.db_path, int(admin_id), False)
        await message.answer("Админ отключен ✅", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    if message.text == ADMIN_MANAGE_BUTTONS[1]:
        set_admin_active(config.db_path, int(admin_id), True)
        await message.answer("Админ активирован ✅", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    await message.answer("Выберите действие", reply_markup=admin_manage_keyboard(is_active=bool(data.get("manage_admin_active", 1))))


@router.message(AdminStates.menu, F.text == ADMIN_MENU_BUTTONS[2])
async def handle_admin_list(message: Message, config: Config, state: FSMContext) -> None:
    if not _is_owner(message, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    active, inactive = list_admins(config.db_path)
    combined = active + inactive
    if not combined:
        await message.answer("Админов пока нет", reply_markup=admin_menu_keyboard())
        return
    labels = [
        _format_choice_label(rec.tg_user_id, f"{rec.name} ({'active' if rec.is_active else 'inactive'})")
        for rec in combined
    ]
    await state.set_state(AdminStates.manage_select)
    await message.answer("Выберите админа", reply_markup=admin_select_keyboard(labels))


@router.message(AdminStates.menu, F.text == ADMIN_MENU_BUTTONS[3])
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


async def _show_report_menu(message: Message, config: Config, state: FSMContext) -> None:
    await state.set_state(ReportStates.menu)
    await _ensure_report_period(state, date.today())
    await message.answer("Отчеты", reply_markup=report_menu_keyboard())


async def _show_report(message: Message, config: Config, state: FSMContext, report_key: str) -> None:
    await state.set_state(ReportStates.view)
    await state.update_data(report_last=report_key)
    today_date = date.today()
    date_from, date_to, label = await _ensure_report_period(state, today_date)
    period_line = _period_label(date_from, date_to, label)

    if report_key == "revenue":
        summary = get_revenue_summary(config.db_path, date_from, date_to)
        text = _format_revenue_report(period_line, summary)
    elif report_key == "expenses":
        summary = get_expense_summary(config.db_path, date_from, date_to)
        text = _format_expense_report(period_line, summary)
    elif report_key == "profit":
        revenue = get_revenue_summary(config.db_path, date_from, date_to)
        expenses = get_expense_summary(config.db_path, date_from, date_to)
        text = _format_profit_report(period_line, revenue.total, expenses.total)
    elif report_key == "attendance":
        summary = get_attendance_summary(config.db_path, date_from, date_to)
        text = _format_attendance_report(period_line, summary)
    elif report_key == "passes":
        today_str = today_date.strftime("%Y-%m-%d")
        expiring_from = today_str
        expiring_to = (today_date + timedelta(days=7)).strftime("%Y-%m-%d")
        active_passes = list_active_passes_today(config.db_path, today_str)
        expiring = list_passes_expiring(config.db_path, expiring_from, expiring_to)
        missing = list_clients_without_active_pass(config.db_path, today_str)
        text = _format_passes_report(today_str, active_passes, expiring, missing)
    elif report_key == "singles":
        total_single = count_single_visits(config.db_path, date_from, date_to)
        total_unpaid = count_single_visits_without_payment(config.db_path, date_from, date_to)
        unpaid = list_single_visits_without_payment(
            config.db_path, date_from, date_to, limit=REPORT_UNPAID_SINGLE_LIMIT
        )
        text = _format_single_visits_report(
            period_line, total_single, total_unpaid, unpaid, REPORT_UNPAID_SINGLE_LIMIT
        )
    elif report_key == "defers":
        today_str = today_date.strftime("%Y-%m-%d")
        total_count, total_amount, latest, overdue = get_deferred_summary(
            config.db_path, date_from, date_to, today_str, DEFER_OVERDUE_DAYS
        )
        text = _format_deferred_report(period_line, total_count, total_amount, latest, overdue, DEFER_OVERDUE_DAYS)
    else:
        text = "Отчет в разработке"

    include_attendance = report_key == "attendance"
    await message.answer(text, reply_markup=report_actions_keyboard(include_attendance_today=include_attendance))


async def _show_last_report_or_menu(message: Message, config: Config, state: FSMContext) -> None:
    data = await state.get_data()
    report_last = data.get("report_last")
    if report_last:
        await _show_report(message, config, state, report_last)
    else:
        await _show_report_menu(message, config, state)


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[0])
async def handle_report_revenue(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_report(message, config, state, "revenue")


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[1])
async def handle_report_expenses(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_report(message, config, state, "expenses")


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[2])
async def handle_report_profit(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_report(message, config, state, "profit")


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[3])
async def handle_report_attendance(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_report(message, config, state, "attendance")


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[4])
async def handle_report_passes(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_report(message, config, state, "passes")


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[5])
async def handle_report_singles(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_report(message, config, state, "singles")


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[6])
async def handle_report_defers(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_report(message, config, state, "defers")


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[7])
async def handle_report_excel(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    today_date = date.today()
    date_from, date_to, _ = await _ensure_report_period(state, today_date)
    today_str = today_date.strftime("%Y-%m-%d")
    data = build_excel_report(config.db_path, date_from, date_to, today_str, DEFER_OVERDUE_DAYS)
    filename = f"report_{date_from}__{date_to}.xlsx"

    owner_file = BufferedInputFile(data, filename=filename)
    requester_file = BufferedInputFile(data, filename=filename)

    if message.from_user and message.from_user.id != config.owner_tg_user_id:
        await message.bot.send_document(
            config.owner_tg_user_id,
            owner_file,
            caption=f"Отчет {date_from} — {date_to}",
        )
    await message.answer_document(
        requester_file,
        caption=f"Отчет {date_from} — {date_to}",
        reply_markup=report_menu_keyboard(),
    )


@router.message(ReportStates.menu, F.text == REPORT_MENU_BUTTONS[8])
async def handle_report_back_to_main(message: Message, config: Config, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню", reply_markup=_main_menu_reply_markup(message, config))


@router.message(ReportStates.view, F.text == REPORT_ACTION_BUTTONS[0])
async def handle_report_period_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.set_state(ReportStates.period_menu)
    await message.answer("Выберите период", reply_markup=report_period_keyboard())


@router.message(ReportStates.view, F.text == REPORT_ACTION_BUTTONS[1])
async def handle_report_view_back(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_report_menu(message, config, state)


@router.message(ReportStates.view, F.text == REPORT_ATTENDANCE_TODAY_BUTTON)
async def handle_report_attendance_today_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    if data.get("report_last") != "attendance":
        await message.answer("Сначала откройте отчет по посещаемости")
        return
    groups = list_active_groups(config.db_path)
    if not groups:
        await message.answer("Групп пока нет", reply_markup=report_actions_keyboard(include_attendance_today=True))
        return
    labels = [_format_group_label(group[0], group[1]) for group in groups]
    mapping = {label: group[0] for label, group in zip(labels, groups)}
    await state.update_data(report_group_map=mapping, report_group_names={group[0]: group[1] for group in groups})
    await state.set_state(ReportStates.attendance_today_group)
    await message.answer("Выберите группу", reply_markup=groups_keyboard(labels))


@router.message(ReportStates.period_menu)
async def handle_report_period_choice(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text:
        await message.answer("Выберите период", reply_markup=report_period_keyboard())
        return
    today_date = date.today()
    if message.text == REPORT_PERIOD_BUTTONS[0]:
        date_from, date_to = _current_month_range(today_date)
        label = "Этот месяц"
        await state.update_data(
            report_date_from=date_from, report_date_to=date_to, report_period_label=label
        )
        await _show_last_report_or_menu(message, config, state)
        return
    if message.text == REPORT_PERIOD_BUTTONS[1]:
        date_from, date_to = _previous_month_range(today_date)
        label = "Прошлый месяц"
        await state.update_data(
            report_date_from=date_from, report_date_to=date_to, report_period_label=label
        )
        await _show_last_report_or_menu(message, config, state)
        return
    if message.text == REPORT_PERIOD_BUTTONS[2]:
        date_from, date_to = _current_week_range(today_date)
        label = "Эта неделя"
        await state.update_data(
            report_date_from=date_from, report_date_to=date_to, report_period_label=label
        )
        await _show_last_report_or_menu(message, config, state)
        return
    if message.text == REPORT_PERIOD_BUTTONS[3]:
        today_str = today_date.strftime("%Y-%m-%d")
        await state.update_data(
            report_date_from=today_str, report_date_to=today_str, report_period_label="Сегодня"
        )
        await _show_last_report_or_menu(message, config, state)
        return
    if message.text == REPORT_PERIOD_BUTTONS[4]:
        await state.set_state(ReportStates.period_custom_from)
        await message.answer("Введите дату начала (YYYY-MM-DD)", reply_markup=report_date_input_keyboard())
        return
    if message.text == REPORT_PERIOD_BUTTONS[5]:
        await state.set_state(ReportStates.view)
        await _show_last_report_or_menu(message, config, state)
        return
    await message.answer("Выберите период", reply_markup=report_period_keyboard())


@router.message(ReportStates.period_custom_from)
async def handle_report_period_custom_from(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text:
        await message.answer("Введите дату начала (YYYY-MM-DD)", reply_markup=report_date_input_keyboard())
        return
    if message.text == "↩️ Назад":
        await state.set_state(ReportStates.period_menu)
        await message.answer("Выберите период", reply_markup=report_period_keyboard())
        return
    parsed = _parse_iso_date(message.text)
    if not parsed:
        await message.answer("Неверный формат даты, пример: 2026-02-04")
        return
    await state.update_data(report_custom_from=parsed)
    await state.set_state(ReportStates.period_custom_to)
    await message.answer("Введите дату окончания (YYYY-MM-DD)", reply_markup=report_date_input_keyboard())


@router.message(ReportStates.period_custom_to)
async def handle_report_period_custom_to(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text:
        await message.answer("Введите дату окончания (YYYY-MM-DD)", reply_markup=report_date_input_keyboard())
        return
    if message.text == "↩️ Назад":
        await state.set_state(ReportStates.period_menu)
        await message.answer("Выберите период", reply_markup=report_period_keyboard())
        return
    parsed = _parse_iso_date(message.text)
    if not parsed:
        await message.answer("Неверный формат даты, пример: 2026-02-04")
        return
    data = await state.get_data()
    date_from = data.get("report_custom_from")
    if not date_from:
        await state.set_state(ReportStates.period_custom_from)
        await message.answer("Введите дату начала (YYYY-MM-DD)", reply_markup=report_date_input_keyboard())
        return
    if parsed < date_from:
        await message.answer("Дата окончания не может быть раньше даты начала")
        return
    await state.update_data(
        report_date_from=date_from,
        report_date_to=parsed,
        report_period_label="Выбранный период",
    )
    await _show_last_report_or_menu(message, config, state)


@router.message(ReportStates.attendance_today_group)
async def handle_report_attendance_today_group(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "❌ Отмена":
        await state.set_state(ReportStates.view)
        await _show_last_report_or_menu(message, config, state)
        return
    data = await state.get_data()
    mapping = data.get("report_group_map", {})
    if not message.text or message.text not in mapping:
        await message.answer("Выберите группу из списка")
        return
    group_id = int(mapping[message.text])
    group_name = data.get("report_group_names", {}).get(group_id, "Группа")
    today_str = date.today().strftime("%Y-%m-%d")
    attendees = list_attended_today_by_group(config.db_path, group_id, today_str)
    if attendees:
        lines = [f"- {full_name} ({phone})" for full_name, phone in attendees]
        text = f"Кто был сегодня ({group_name}, {today_str}):\n" + "\n".join(lines)
    else:
        text = f"Сегодня в группе {group_name} никто не отмечен"
    await state.set_state(ReportStates.view)
    await message.answer(text, reply_markup=report_actions_keyboard(include_attendance_today=True))


async def _show_trainers_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(TrainerStates.menu)
    await message.answer("Тренеры", reply_markup=trainers_menu_keyboard())


async def _show_groups_menu(message: Message, state: FSMContext) -> None:
    await state.set_state(GroupStates.menu)
    await message.answer("Группы", reply_markup=groups_menu_keyboard())


async def _show_trainer_card(message: Message, config: Config, state: FSMContext, trainer_id: int) -> None:
    trainer = get_trainer_by_id(config.db_path, trainer_id)
    if not trainer:
        await message.answer("Тренер не найден", reply_markup=trainers_menu_keyboard())
        await state.set_state(TrainerStates.menu)
        return
    groups = list_groups_by_trainer(config.db_path, trainer_id)
    await state.update_data(trainer_id=trainer_id)
    await state.set_state(TrainerStates.card)
    await message.answer(
        _format_trainer_card(trainer, groups),
        reply_markup=trainer_actions_keyboard(is_active=int(trainer[5]) == 1),
    )


async def _show_group_card(message: Message, config: Config, state: FSMContext, group_id: int) -> None:
    group = get_group_by_id(config.db_path, group_id)
    if not group:
        await message.answer("Группа не найдена", reply_markup=groups_menu_keyboard())
        await state.set_state(GroupStates.menu)
        return
    await state.update_data(group_id=group_id)
    await state.set_state(GroupStates.card)
    await message.answer(
        _format_group_card(group),
        reply_markup=group_actions_keyboard(is_active=int(group[6]) == 1),
    )


async def _show_schedule_menu(message: Message, config: Config, state: FSMContext, group_id: int) -> None:
    group = get_group_by_id(config.db_path, group_id)
    if not group:
        await message.answer("Группа не найдена", reply_markup=groups_menu_keyboard())
        await state.set_state(GroupStates.menu)
        return
    slots = list_schedule_for_group(config.db_path, group_id, include_inactive=True)
    await state.update_data(schedule_group_id=group_id)
    await state.set_state(ScheduleStates.menu)
    await message.answer(_format_schedule_list(group[1], slots), reply_markup=schedule_menu_keyboard())


@router.message(TrainerStates.menu)
async def handle_trainers_menu_choice(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == TRAINERS_MENU_BUTTONS[0]:
        await state.set_state(TrainerStates.add_name)
        await message.answer("Введите ФИО тренера")
        return
    if message.text == TRAINERS_MENU_BUTTONS[1]:
        trainers = list_active_trainers(config.db_path)
        if not trainers:
            await message.answer("Активных тренеров нет", reply_markup=trainers_menu_keyboard())
            return
        labels = [_format_choice_label(t[0], t[1]) for t in trainers]
        await state.set_state(TrainerStates.list_select)
        await message.answer("Выберите тренера", reply_markup=trainers_list_keyboard(labels))
        return
    if message.text == TRAINERS_MENU_BUTTONS[2]:
        await state.clear()
        await message.answer("Главное меню", reply_markup=_main_menu_reply_markup(message, config))
        return
    await message.answer("Выберите действие", reply_markup=trainers_menu_keyboard())


@router.message(TrainerStates.add_name)
async def handle_trainer_add_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите ФИО тренера")
        return
    await state.update_data(trainer_full_name=message.text.strip())
    await state.set_state(TrainerStates.add_phone)
    await message.answer("Телефон (можно пропустить)", reply_markup=skip_keyboard())


@router.message(TrainerStates.add_phone)
async def handle_trainer_add_phone(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[1]:
        await state.clear()
        await _show_trainers_menu(message, state)
        return
    if message.text == SKIP_BUTTONS[0]:
        await state.update_data(trainer_phone=None)
        await state.set_state(TrainerStates.add_tg)
        await message.answer("Telegram username (можно пропустить)", reply_markup=skip_keyboard())
        return

    raw_phone = None
    if message.contact and message.contact.phone_number:
        raw_phone = message.contact.phone_number
    elif message.text:
        raw_phone = message.text.strip()

    if not raw_phone:
        await message.answer("Введите телефон или нажмите Пропустить")
        return

    normalized = _normalize_phone(raw_phone)
    if not normalized:
        await message.answer("Не удалось распознать телефон, попробуйте еще раз или пропустите")
        return
    await state.update_data(trainer_phone=normalized)
    await state.set_state(TrainerStates.add_tg)
    await message.answer("Telegram username (можно пропустить)", reply_markup=skip_keyboard())


@router.message(TrainerStates.add_tg)
async def handle_trainer_add_tg(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[1]:
        await state.clear()
        await _show_trainers_menu(message, state)
        return
    if message.text == SKIP_BUTTONS[0]:
        await state.update_data(trainer_tg=None)
        await state.set_state(TrainerStates.add_confirm)
        await message.answer("Сохранить тренера?", reply_markup=confirm_keyboard())
        return
    if not message.text:
        await message.answer("Введите username или нажмите Пропустить")
        return
    normalized = _normalize_username(message.text)
    if not normalized:
        await message.answer("Введите username или нажмите Пропустить")
        return
    await state.update_data(trainer_tg=normalized)
    await state.set_state(TrainerStates.add_confirm)
    await message.answer("Сохранить тренера?", reply_markup=confirm_keyboard())


@router.message(TrainerStates.add_confirm)
async def handle_trainer_add_confirm(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == CONFIRM_BUTTONS[1]:
        await state.clear()
        await _show_trainers_menu(message, state)
        return
    if message.text != CONFIRM_BUTTONS[0]:
        await message.answer("Выберите действие", reply_markup=confirm_keyboard())
        return
    data = await state.get_data()
    trainer_id = create_trainer(
        config.db_path,
        full_name=str(data.get("trainer_full_name", "")).strip(),
        phone=data.get("trainer_phone"),
        tg_username=data.get("trainer_tg"),
    )
    await _show_trainer_card(message, config, state, trainer_id)


@router.message(TrainerStates.list_select)
async def handle_trainer_list_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == TRAINERS_MENU_BUTTONS[0]:
        await state.set_state(TrainerStates.add_name)
        await message.answer("Введите ФИО тренера")
        return
    if message.text == TRAINERS_MENU_BUTTONS[2]:
        await _show_trainers_menu(message, state)
        return
    trainer_id = _parse_choice_id(message.text or "")
    if trainer_id is None:
        await message.answer("Выберите тренера из списка")
        return
    await _show_trainer_card(message, config, state, trainer_id)


@router.message(TrainerStates.card, F.text == TRAINER_ACTION_BUTTONS[0])
async def handle_trainer_attach_group_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    groups = list_active_groups(config.db_path)
    labels = [_format_choice_label(g[0], g[1]) for g in groups]
    await state.set_state(TrainerStates.attach_group_select)
    await message.answer("Выберите группу", reply_markup=trainer_attach_group_keyboard(labels))


@router.message(TrainerStates.card, F.text == TRAINER_ACTION_BUTTONS[1])
async def handle_trainer_create_group_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.set_state(TrainerStates.create_group_name)
    await message.answer("Название группы")


@router.message(TrainerStates.card, F.text == TRAINER_ACTION_BUTTONS[2])
async def handle_trainer_detach_group_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    trainer_id = data.get("trainer_id")
    if not trainer_id:
        await message.answer("Тренер не выбран")
        return
    groups = list_groups_by_trainer(config.db_path, int(trainer_id))
    if not groups:
        await message.answer("У тренера нет групп")
        await _show_trainer_card(message, config, state, int(trainer_id))
        return
    labels = [_format_choice_label(g[0], g[1]) for g in groups]
    await state.set_state(TrainerStates.detach_group_select)
    await message.answer("Выберите группу", reply_markup=trainer_detach_group_keyboard(labels))


@router.message(TrainerStates.card, F.text == TRAINER_ACTION_BUTTONS[3])
async def handle_trainer_rename_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.set_state(TrainerStates.rename)
    await message.answer("Введите новое имя тренера")


@router.message(TrainerStates.card, F.text == TRAINER_ACTION_BUTTONS[4])
async def handle_trainer_hide(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    trainer_id = data.get("trainer_id")
    if trainer_id:
        set_trainer_active(config.db_path, int(trainer_id), False)
        await _show_trainer_card(message, config, state, int(trainer_id))


@router.message(TrainerStates.card, F.text == TRAINER_ACTION_BUTTONS[5])
async def handle_trainer_activate(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    trainer_id = data.get("trainer_id")
    if trainer_id:
        set_trainer_active(config.db_path, int(trainer_id), True)
        await _show_trainer_card(message, config, state, int(trainer_id))


@router.message(TrainerStates.card, F.text == TRAINER_ACTION_BUTTONS[6])
async def handle_trainer_card_back(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_trainers_menu(message, state)


@router.message(TrainerStates.attach_group_select)
async def handle_trainer_attach_group_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == TRAINER_ATTACH_GROUP_BACK:
        data = await state.get_data()
        trainer_id = data.get("trainer_id")
        if trainer_id:
            await _show_trainer_card(message, config, state, int(trainer_id))
        else:
            await _show_trainers_menu(message, state)
        return
    if message.text == TRAINER_ATTACH_GROUP_NEW:
        await state.set_state(TrainerStates.create_group_name)
        await message.answer("Название группы")
        return
    group_id = _parse_choice_id(message.text or "")
    if group_id is None:
        await message.answer("Выберите группу из списка")
        return
    data = await state.get_data()
    trainer_id = data.get("trainer_id")
    if not trainer_id:
        await message.answer("Тренер не выбран")
        return
    success = set_group_trainer(config.db_path, group_id, int(trainer_id))
    if not success:
        await message.answer("Не удалось назначить тренера")
    await _show_trainer_card(message, config, state, int(trainer_id))


@router.message(TrainerStates.create_group_name)
async def handle_trainer_create_group_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите название группы")
        return
    await state.update_data(group_name=message.text.strip())
    await state.set_state(TrainerStates.create_group_capacity)
    await message.answer("Вместимость (можно пропустить)", reply_markup=skip_keyboard())


@router.message(TrainerStates.create_group_capacity)
async def handle_trainer_create_group_capacity(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[0]:
        await state.update_data(group_capacity=0)
        await state.set_state(TrainerStates.create_group_room)
        await message.answer("Зал (можно пропустить)", reply_markup=skip_keyboard())
        return
    if message.text == SKIP_BUTTONS[1]:
        data = await state.get_data()
        trainer_id = data.get("trainer_id")
        if trainer_id:
            await _show_trainer_card(message, config, state, int(trainer_id))
        else:
            await _show_trainers_menu(message, state)
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Введите число или нажмите Пропустить")
        return
    await state.update_data(group_capacity=int(message.text))
    await state.set_state(TrainerStates.create_group_room)
    await message.answer("Зал (можно пропустить)", reply_markup=skip_keyboard())


@router.message(TrainerStates.create_group_room)
async def handle_trainer_create_group_room(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[1]:
        data = await state.get_data()
        trainer_id = data.get("trainer_id")
        if trainer_id:
            await _show_trainer_card(message, config, state, int(trainer_id))
        else:
            await _show_trainers_menu(message, state)
        return
    room_name = None if message.text == SKIP_BUTTONS[0] else (message.text or "").strip()
    data = await state.get_data()
    trainer_id = data.get("trainer_id")
    if not trainer_id:
        await _show_trainers_menu(message, state)
        return
    try:
        create_group(
            config.db_path,
            name=str(data.get("group_name", "")).strip(),
            capacity=int(data.get("group_capacity", 0) or 0),
            room_name=room_name if room_name else None,
            trainer_id=int(trainer_id),
        )
    except ValueError:
        await message.answer("Не удалось создать группу: тренер не найден или неактивен")
    await _show_trainer_card(message, config, state, int(trainer_id))


@router.message(TrainerStates.detach_group_select)
async def handle_trainer_detach_group_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == TRAINER_DETACH_GROUP_BACK:
        data = await state.get_data()
        trainer_id = data.get("trainer_id")
        if trainer_id:
            await _show_trainer_card(message, config, state, int(trainer_id))
        else:
            await _show_trainers_menu(message, state)
        return
    group_id = _parse_choice_id(message.text or "")
    if group_id is None:
        await message.answer("Выберите группу из списка")
        return
    clear_group_trainer(config.db_path, group_id)
    data = await state.get_data()
    trainer_id = data.get("trainer_id")
    if trainer_id:
        await _show_trainer_card(message, config, state, int(trainer_id))
        return
    await _show_trainers_menu(message, state)


@router.message(TrainerStates.rename)
async def handle_trainer_rename(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите новое имя тренера")
        return
    data = await state.get_data()
    trainer_id = data.get("trainer_id")
    if not trainer_id:
        await _show_trainers_menu(message, state)
        return
    update_trainer_name(config.db_path, int(trainer_id), message.text.strip())
    await _show_trainer_card(message, config, state, int(trainer_id))


@router.message(GroupStates.menu)
async def handle_groups_menu_choice(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == GROUPS_MENU_BUTTONS[0]:
        await state.set_state(GroupStates.create_name)
        await message.answer("Введите название группы")
        return
    if message.text == GROUPS_MENU_BUTTONS[1]:
        groups = list_groups(config.db_path, include_inactive=False)
        if not groups:
            await message.answer("Активных групп нет", reply_markup=groups_menu_keyboard())
            return
        labels = [_format_choice_label(g[0], g[1]) for g in groups]
        await state.set_state(GroupStates.list_select)
        await message.answer("Выберите группу", reply_markup=groups_list_keyboard(labels))
        return
    if message.text == GROUPS_MENU_BUTTONS[2]:
        await state.clear()
        await message.answer("Главное меню", reply_markup=_main_menu_reply_markup(message, config))
        return
    await message.answer("Выберите действие", reply_markup=groups_menu_keyboard())


@router.message(GroupStates.create_name)
async def handle_group_create_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите название группы")
        return
    await state.update_data(group_name=message.text.strip())
    await state.set_state(GroupStates.create_capacity)
    await message.answer("Вместимость (можно пропустить)", reply_markup=skip_keyboard())


@router.message(GroupStates.create_capacity)
async def handle_group_create_capacity(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[0]:
        await state.update_data(group_capacity=0)
        await state.set_state(GroupStates.create_room)
        await message.answer("Зал (можно пропустить)", reply_markup=skip_keyboard())
        return
    if message.text == SKIP_BUTTONS[1]:
        await _show_groups_menu(message, state)
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Введите число или нажмите Пропустить")
        return
    await state.update_data(group_capacity=int(message.text))
    await state.set_state(GroupStates.create_room)
    await message.answer("Зал (можно пропустить)", reply_markup=skip_keyboard())


@router.message(GroupStates.create_room)
async def handle_group_create_room(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SKIP_BUTTONS[1]:
        await _show_groups_menu(message, state)
        return
    room_name = None if message.text == SKIP_BUTTONS[0] else (message.text or "").strip()
    await state.update_data(group_room=room_name if room_name else None)
    await state.set_state(GroupStates.create_assign)
    await message.answer("Назначить тренера?", reply_markup=group_create_assign_keyboard())


@router.message(GroupStates.create_assign)
async def handle_group_create_assign(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == GROUP_CREATE_ASSIGN_BUTTONS[0]:
        trainers = list_active_trainers(config.db_path)
        if not trainers:
            await message.answer("Активных тренеров нет", reply_markup=group_create_assign_keyboard())
            return
        labels = [_format_choice_label(t[0], t[1]) for t in trainers]
        await state.set_state(GroupStates.create_assign_select)
        await message.answer("Выберите тренера", reply_markup=group_assign_trainer_keyboard(labels))
        return
    if message.text == GROUP_CREATE_ASSIGN_BUTTONS[1]:
        await state.set_state(GroupStates.create_trainer_name)
        await message.answer("Введите имя тренера")
        return
    if message.text == GROUP_CREATE_ASSIGN_BUTTONS[2]:
        await state.update_data(group_trainer_id=None, group_trainer_name=None)
        await state.set_state(GroupStates.create_confirm)
        data = await state.get_data()
        trainer_label = data.get("group_trainer_name") or "не назначен"
        await message.answer(
            f"Проверьте данные:\n"
            f"Группа: {data.get('group_name')}\n"
            f"Вместимость: {data.get('group_capacity', 0)}\n"
            f"Зал: {data.get('group_room') or '—'}\n"
            f"Тренер: {trainer_label}",
            reply_markup=confirm_keyboard(),
        )
        return
    await message.answer("Выберите действие", reply_markup=group_create_assign_keyboard())


@router.message(GroupStates.create_assign_select)
async def handle_group_create_assign_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == GROUP_ASSIGN_TRAINER_BACK:
        await state.set_state(GroupStates.create_assign)
        await message.answer("Назначить тренера?", reply_markup=group_create_assign_keyboard())
        return
    if message.text == GROUP_ASSIGN_TRAINER_NEW:
        await state.set_state(GroupStates.create_trainer_name)
        await message.answer("Введите имя тренера")
        return
    trainer_id = _parse_choice_id(message.text or "")
    if trainer_id is None:
        await message.answer("Выберите тренера из списка")
        return
    trainer = get_trainer_by_id(config.db_path, trainer_id)
    if not trainer:
        await message.answer("Тренер не найден")
        return
    await state.update_data(group_trainer_id=trainer_id, group_trainer_name=trainer[1])
    await state.set_state(GroupStates.create_confirm)
    data = await state.get_data()
    await message.answer(
        f"Проверьте данные:\n"
        f"Группа: {data.get('group_name')}\n"
        f"Вместимость: {data.get('group_capacity', 0)}\n"
        f"Зал: {data.get('group_room') or '—'}\n"
        f"Тренер: {trainer[1]}",
        reply_markup=confirm_keyboard(),
    )


@router.message(GroupStates.create_trainer_name)
async def handle_group_create_trainer_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите имя тренера")
        return
    trainer_id = create_trainer(config.db_path, message.text.strip())
    await state.update_data(group_trainer_id=trainer_id, group_trainer_name=message.text.strip())
    await state.set_state(GroupStates.create_confirm)
    data = await state.get_data()
    await message.answer(
        f"Проверьте данные:\n"
        f"Группа: {data.get('group_name')}\n"
        f"Вместимость: {data.get('group_capacity', 0)}\n"
        f"Зал: {data.get('group_room') or '—'}\n"
        f"Тренер: {message.text.strip()}",
        reply_markup=confirm_keyboard(),
    )


@router.message(GroupStates.create_confirm)
async def handle_group_create_confirm(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == CONFIRM_BUTTONS[1]:
        await _show_groups_menu(message, state)
        return
    if message.text != CONFIRM_BUTTONS[0]:
        await message.answer("Выберите действие", reply_markup=confirm_keyboard())
        return
    data = await state.get_data()
    try:
        create_group(
            config.db_path,
            name=str(data.get("group_name", "")).strip(),
            capacity=int(data.get("group_capacity", 0) or 0),
            room_name=data.get("group_room"),
            trainer_id=data.get("group_trainer_id"),
            trainer_name=data.get("group_trainer_name"),
        )
    except ValueError:
        await message.answer("Не удалось создать группу: тренер не найден или неактивен")
        await _show_groups_menu(message, state)
        return
    await message.answer("Группа создана ✅")
    await _show_groups_menu(message, state)


@router.message(GroupStates.list_select)
async def handle_group_list_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == GROUPS_MENU_BUTTONS[0]:
        await state.set_state(GroupStates.create_name)
        await message.answer("Введите название группы")
        return
    if message.text == GROUPS_MENU_BUTTONS[2]:
        await _show_groups_menu(message, state)
        return
    group_id = _parse_choice_id(message.text or "")
    if group_id is None:
        await message.answer("Выберите группу из списка")
        return
    await _show_group_card(message, config, state, group_id)


@router.message(GroupStates.card, F.text == GROUP_ACTION_BUTTONS[0])
async def handle_group_assign_trainer_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    trainers = list_active_trainers(config.db_path)
    if not trainers:
        await message.answer("Активных тренеров нет")
        data = await state.get_data()
        group_id = data.get("group_id")
        if group_id:
            await _show_group_card(message, config, state, int(group_id))
        return
    labels = [_format_choice_label(t[0], t[1]) for t in trainers]
    await state.set_state(GroupStates.assign_trainer_select)
    await message.answer("Выберите тренера", reply_markup=group_assign_trainer_keyboard(labels))


@router.message(GroupStates.card, F.text == GROUP_ACTION_BUTTONS[1])
async def handle_group_create_trainer_assign(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.set_state(GroupStates.assign_trainer_name)
    await message.answer("Введите имя тренера")


@router.message(GroupStates.card, F.text == GROUP_ACTION_BUTTONS[2])
async def handle_group_clear_trainer(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    group_id = data.get("group_id")
    if group_id:
        clear_group_trainer(config.db_path, int(group_id))
        await _show_group_card(message, config, state, int(group_id))


@router.message(GroupStates.card, F.text == GROUP_ACTION_BUTTONS[3])
async def handle_group_rename_start(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await state.set_state(GroupStates.rename)
    await message.answer("Введите новое название группы")


@router.message(GroupStates.card, F.text == GROUP_ACTION_BUTTONS[4])
async def handle_group_schedule(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    group_id = data.get("group_id")
    if not group_id:
        await _show_groups_menu(message, state)
        return
    await _show_schedule_menu(message, config, state, int(group_id))


@router.message(GroupStates.card, F.text == GROUP_ACTION_BUTTONS[5])
async def handle_group_hide(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    group_id = data.get("group_id")
    if group_id:
        set_group_active(config.db_path, int(group_id), False)
        await _show_group_card(message, config, state, int(group_id))


@router.message(GroupStates.card, F.text == GROUP_ACTION_BUTTONS[6])
async def handle_group_activate(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    group_id = data.get("group_id")
    if group_id:
        set_group_active(config.db_path, int(group_id), True)
        await _show_group_card(message, config, state, int(group_id))


@router.message(GroupStates.card, F.text == GROUP_ACTION_BUTTONS[7])
async def handle_group_card_back(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    await _show_groups_menu(message, state)


@router.message(GroupStates.assign_trainer_select)
async def handle_group_assign_trainer_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == GROUP_ASSIGN_TRAINER_BACK:
        data = await state.get_data()
        group_id = data.get("group_id")
        if group_id:
            await _show_group_card(message, config, state, int(group_id))
        else:
            await _show_groups_menu(message, state)
        return
    if message.text == GROUP_ASSIGN_TRAINER_NEW:
        await state.set_state(GroupStates.assign_trainer_name)
        await message.answer("Введите имя тренера")
        return
    trainer_id = _parse_choice_id(message.text or "")
    if trainer_id is None:
        await message.answer("Выберите тренера из списка")
        return
    data = await state.get_data()
    group_id = data.get("group_id")
    if not group_id:
        await _show_groups_menu(message, state)
        return
    success = set_group_trainer(config.db_path, int(group_id), trainer_id)
    if not success:
        await message.answer("Не удалось назначить тренера")
    await _show_group_card(message, config, state, int(group_id))


@router.message(GroupStates.assign_trainer_name)
async def handle_group_assign_trainer_name(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите имя тренера")
        return
    data = await state.get_data()
    group_id = data.get("group_id")
    if not group_id:
        await _show_groups_menu(message, state)
        return
    trainer_id = create_trainer(config.db_path, message.text.strip())
    set_group_trainer(config.db_path, int(group_id), trainer_id)
    await _show_group_card(message, config, state, int(group_id))


@router.message(GroupStates.rename)
async def handle_group_rename(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if not message.text or message.text.strip() == "":
        await message.answer("Введите новое название группы")
        return
    data = await state.get_data()
    group_id = data.get("group_id")
    if not group_id:
        await _show_groups_menu(message, state)
        return
    rename_group(config.db_path, int(group_id), message.text.strip())
    await _show_group_card(message, config, state, int(group_id))


def _schedule_choice_label(slot: tuple) -> str:
    schedule_id, day_of_week, time_hhmm, duration_min, room_name, is_active = slot
    label = _format_schedule_slot(day_of_week, time_hhmm, duration_min, room_name)
    if int(is_active) == 0:
        label = f"{label} ⛔"
    return f"{schedule_id}) {label}"


@router.message(ScheduleStates.menu)
async def handle_schedule_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    group_id = data.get("schedule_group_id")
    if not group_id:
        await _show_groups_menu(message, state)
        return
    if message.text == SCHEDULE_MENU_BUTTONS[0]:
        await state.set_state(ScheduleStates.add_weekday)
        await message.answer("Выберите день", reply_markup=schedule_weekday_keyboard())
        return
    if message.text == SCHEDULE_MENU_BUTTONS[1]:
        slots = list_schedule_for_group(config.db_path, int(group_id), include_inactive=True)
        if not slots:
            await message.answer("Расписание пустое", reply_markup=schedule_menu_keyboard())
            return
        labels = [_schedule_choice_label(slot) for slot in slots]
        await state.set_state(ScheduleStates.edit_select)
        await message.answer("Выберите слот", reply_markup=schedule_slots_keyboard(labels))
        return
    if message.text == SCHEDULE_MENU_BUTTONS[2]:
        slots = list_schedule_for_group(config.db_path, int(group_id), include_inactive=True)
        if not slots:
            await message.answer("Расписание пустое", reply_markup=schedule_menu_keyboard())
            return
        labels = [_schedule_choice_label(slot) for slot in slots]
        await state.set_state(ScheduleStates.delete_select)
        await message.answer("Выберите слот для удаления", reply_markup=schedule_slots_keyboard(labels))
        return
    if message.text == SCHEDULE_MENU_BUTTONS[3]:
        await _show_group_card(message, config, state, int(group_id))
        return
    await message.answer("Выберите действие", reply_markup=schedule_menu_keyboard())


@router.message(ScheduleStates.add_weekday)
async def handle_schedule_add_weekday(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == SCHEDULE_WEEKDAY_BUTTONS[7]:
        data = await state.get_data()
        group_id = data.get("schedule_group_id")
        if group_id:
            await _show_schedule_menu(message, config, state, int(group_id))
        return
    if not message.text or message.text not in _WEEKDAY_TEXT_TO_NUM:
        await message.answer("Выберите день недели", reply_markup=schedule_weekday_keyboard())
        return
    await state.update_data(schedule_weekday=_WEEKDAY_TEXT_TO_NUM[message.text])
    await state.set_state(ScheduleStates.add_time)
    await message.answer("Введите время начала (HH:MM)", reply_markup=schedule_time_keyboard())


@router.message(ScheduleStates.add_time)
async def handle_schedule_add_time(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ScheduleStates.add_weekday)
        await message.answer("Выберите день", reply_markup=schedule_weekday_keyboard())
        return
    if not message.text:
        await message.answer("Введите время начала (HH:MM)")
        return
    parsed = _parse_hhmm(message.text)
    if not parsed:
        await message.answer("Неверный формат времени, пример: 18:00")
        return
    await state.update_data(schedule_time=parsed)
    await state.set_state(ScheduleStates.add_duration)
    await message.answer("Длительность, мин (по умолчанию 60)", reply_markup=schedule_duration_keyboard())


@router.message(ScheduleStates.add_duration)
async def handle_schedule_add_duration(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ScheduleStates.add_time)
        await message.answer("Введите время начала (HH:MM)", reply_markup=schedule_time_keyboard())
        return
    if message.text == "Пропустить":
        await state.update_data(schedule_duration=60)
        await state.set_state(ScheduleStates.add_room)
        await message.answer("Зал/комната (можно пропустить)", reply_markup=schedule_room_keyboard())
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Введите число минут или нажмите Пропустить")
        return
    duration = int(message.text)
    if duration <= 0:
        await message.answer("Длительность должна быть больше 0")
        return
    await state.update_data(schedule_duration=duration)
    await state.set_state(ScheduleStates.add_room)
    await message.answer("Зал/комната (можно пропустить)", reply_markup=schedule_room_keyboard())


@router.message(ScheduleStates.add_room)
async def handle_schedule_add_room(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ScheduleStates.add_duration)
        await message.answer("Длительность, мин (по умолчанию 60)", reply_markup=schedule_duration_keyboard())
        return
    room_name = None if message.text == "Пропустить" else (message.text or "").strip()
    await state.update_data(schedule_room=room_name if room_name else None)
    data = await state.get_data()
    weekday = data.get("schedule_weekday")
    time_hhmm = data.get("schedule_time")
    duration = data.get("schedule_duration", 60)
    summary = _format_schedule_slot(int(weekday), str(time_hhmm), int(duration), room_name)
    await state.set_state(ScheduleStates.add_confirm)
    await message.answer(f"Добавить слот?\n{summary}", reply_markup=confirm_keyboard())


@router.message(ScheduleStates.add_confirm)
async def handle_schedule_add_confirm(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    group_id = data.get("schedule_group_id")
    if not group_id:
        await _show_groups_menu(message, state)
        return
    if message.text == CONFIRM_BUTTONS[1]:
        await _show_schedule_menu(message, config, state, int(group_id))
        return
    if message.text != CONFIRM_BUTTONS[0]:
        await message.answer("Выберите действие", reply_markup=confirm_keyboard())
        return
    try:
        add_schedule_slot(
            config.db_path,
            int(group_id),
            int(data.get("schedule_weekday")),
            str(data.get("schedule_time")),
            int(data.get("schedule_duration", 60)),
            data.get("schedule_room"),
        )
    except sqlite3.IntegrityError:
        await message.answer("Такой день/время уже добавлены")
        await _show_schedule_menu(message, config, state, int(group_id))
        return
    await message.answer("Слот добавлен ✅")
    await _show_schedule_menu(message, config, state, int(group_id))


@router.message(ScheduleStates.edit_select)
async def handle_schedule_edit_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        data = await state.get_data()
        group_id = data.get("schedule_group_id")
        if group_id:
            await _show_schedule_menu(message, config, state, int(group_id))
        return
    schedule_id = _parse_choice_id(message.text or "")
    if schedule_id is None:
        await message.answer("Выберите слот из списка")
        return
    slot = get_schedule_by_id(config.db_path, schedule_id)
    if not slot:
        await message.answer("Слот не найден")
        return
    data = await state.get_data()
    group_id = data.get("schedule_group_id")
    if group_id and int(slot[1]) != int(group_id):
        await message.answer("Слот не найден")
        return
    await state.update_data(schedule_id=schedule_id, schedule_active=int(slot[6]))
    label = _format_schedule_slot(int(slot[2]), str(slot[3]), int(slot[4]), slot[5])
    await state.set_state(ScheduleStates.edit_menu)
    await message.answer(f"Изменить слот:\n{label}", reply_markup=schedule_edit_keyboard(is_active=int(slot[6]) == 1))


@router.message(ScheduleStates.edit_menu)
async def handle_schedule_edit_menu(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    group_id = data.get("schedule_group_id")
    if message.text == SCHEDULE_EDIT_BUTTONS[0]:
        await state.set_state(ScheduleStates.edit_time)
        await message.answer("Введите новое время (HH:MM)", reply_markup=schedule_time_keyboard())
        return
    if message.text == SCHEDULE_EDIT_BUTTONS[1]:
        await state.set_state(ScheduleStates.edit_duration)
        await message.answer("Введите длительность, мин", reply_markup=schedule_duration_keyboard())
        return
    if message.text == SCHEDULE_EDIT_BUTTONS[2]:
        await state.set_state(ScheduleStates.edit_room)
        await message.answer("Введите зал/комнату (или Пропустить чтобы очистить)", reply_markup=schedule_room_keyboard())
        return
    if message.text == SCHEDULE_EDIT_BUTTONS[3] or message.text == SCHEDULE_EDIT_BUTTONS[4]:
        schedule_id = data.get("schedule_id")
        if schedule_id:
            new_active = message.text == SCHEDULE_EDIT_BUTTONS[4]
            toggle_schedule_slot(config.db_path, int(schedule_id), new_active)
        if group_id:
            await _show_schedule_menu(message, config, state, int(group_id))
        return
    if message.text == SCHEDULE_EDIT_BUTTONS[5]:
        if group_id:
            await _show_schedule_menu(message, config, state, int(group_id))
        return
    active = bool(data.get("schedule_active", 1))
    await message.answer("Выберите действие", reply_markup=schedule_edit_keyboard(is_active=active))


@router.message(ScheduleStates.edit_time)
async def handle_schedule_edit_time(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ScheduleStates.edit_menu)
        data = await state.get_data()
        active = bool(data.get("schedule_active", 1))
        await message.answer("Выберите действие", reply_markup=schedule_edit_keyboard(is_active=active))
        return
    parsed = _parse_hhmm(message.text or "")
    if not parsed:
        await message.answer("Неверный формат времени, пример: 18:00")
        return
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    if schedule_id:
        try:
            update_schedule_slot(config.db_path, int(schedule_id), start_time=parsed)
        except sqlite3.IntegrityError:
            await message.answer("Такой день/время уже добавлены")
    group_id = data.get("schedule_group_id")
    if group_id:
        await _show_schedule_menu(message, config, state, int(group_id))


@router.message(ScheduleStates.edit_duration)
async def handle_schedule_edit_duration(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ScheduleStates.edit_menu)
        data = await state.get_data()
        active = bool(data.get("schedule_active", 1))
        await message.answer("Выберите действие", reply_markup=schedule_edit_keyboard(is_active=active))
        return
    if message.text == "Пропустить":
        data = await state.get_data()
        group_id = data.get("schedule_group_id")
        if group_id:
            await _show_schedule_menu(message, config, state, int(group_id))
        return
    if not message.text or not message.text.isdigit():
        await message.answer("Введите число минут")
        return
    duration = int(message.text)
    if duration <= 0:
        await message.answer("Длительность должна быть больше 0")
        return
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    if schedule_id:
        update_schedule_slot(config.db_path, int(schedule_id), duration_min=duration)
    group_id = data.get("schedule_group_id")
    if group_id:
        await _show_schedule_menu(message, config, state, int(group_id))


@router.message(ScheduleStates.edit_room)
async def handle_schedule_edit_room(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        await state.set_state(ScheduleStates.edit_menu)
        data = await state.get_data()
        active = bool(data.get("schedule_active", 1))
        await message.answer("Выберите действие", reply_markup=schedule_edit_keyboard(is_active=active))
        return
    room_name = None if message.text == "Пропустить" else (message.text or "").strip()
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    if schedule_id:
        update_schedule_slot(config.db_path, int(schedule_id), room_name=room_name if room_name else None)
    group_id = data.get("schedule_group_id")
    if group_id:
        await _show_schedule_menu(message, config, state, int(group_id))


@router.message(ScheduleStates.delete_select)
async def handle_schedule_delete_select(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    if message.text == "↩️ Назад":
        data = await state.get_data()
        group_id = data.get("schedule_group_id")
        if group_id:
            await _show_schedule_menu(message, config, state, int(group_id))
        return
    schedule_id = _parse_choice_id(message.text or "")
    if schedule_id is None:
        await message.answer("Выберите слот из списка")
        return
    await state.update_data(schedule_id=schedule_id)
    await state.set_state(ScheduleStates.delete_confirm)
    await message.answer("Удалить слот?", reply_markup=schedule_delete_confirm_keyboard())


@router.message(ScheduleStates.delete_confirm)
async def handle_schedule_delete_confirm(message: Message, config: Config, state: FSMContext) -> None:
    if not _has_access(message, config):
        await _deny_and_menu(message, config, state)
        return
    data = await state.get_data()
    group_id = data.get("schedule_group_id")
    if message.text == SCHEDULE_DELETE_BUTTONS[1]:
        if group_id:
            await _show_schedule_menu(message, config, state, int(group_id))
        return
    if message.text != SCHEDULE_DELETE_BUTTONS[0]:
        await message.answer("Выберите действие", reply_markup=schedule_delete_confirm_keyboard())
        return
    schedule_id = data.get("schedule_id")
    if schedule_id:
        delete_schedule_slot(config.db_path, int(schedule_id))
        await message.answer("Слот удалён ✅")
    if group_id:
        await _show_schedule_menu(message, config, state, int(group_id))
