from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU_BUTTONS = [
    "➕ Новый клиент",
    "🔎 Найти клиента",
    "📅 Записать на занятие",
    "✅ Отметить посещение",
    "💳 Принять оплату",
    "🎫 Абонемент",
    "💸 Расходы",
    "📊 Отчеты",
]

ADMIN_MENU_BUTTONS = [
    "➕ Добавить админа",
    "⛔ Отключить админа",
    "📋 Список админов",
    "↩️ Назад",
]

NEW_CLIENT_PHONE_BUTTONS = [
    "📱 Отправить контакт",
    "✍️ Ввести вручную",
    "❌ Отмена",
]

SKIP_BUTTONS = [
    "Пропустить",
    "❌ Отмена",
]

CONFIRM_BUTTONS = [
    "✅ Сохранить",
    "❌ Отмена",
]

SEARCH_MENU_BUTTONS = [
    "📱 По телефону",
    "🔤 По имени",
    "👤 Telegram",
    "❌ Отмена",
]

CLIENT_ACTION_BUTTONS = [
    "📅 Записать",
    "✅ Отметить",
    "💳 Оплата",
    "🎫 Абонемент",
    "↩️ Назад",
    "❌ Отмена",
]

BOOKING_CLIENT_SEARCH_BUTTONS = [
    "📱 По телефону",
    "🔤 По имени",
    "👤 Telegram",
    "❌ Отмена",
]

BOOKING_TYPE_BUTTONS = [
    "Разовое",
    "По абонементу (закрепить в группе)",
    "❌ Отмена",
]

BOOKING_DATE_BUTTONS = [
    "Сегодня",
    "Завтра",
    "Ввести дату",
    "❌ Отмена",
]

ADD_GROUP_BUTTONS = [
    "➕ Добавить группу",
    "❌ Отмена",
]

ATTENDANCE_DATE_BUTTONS = [
    "Сегодня",
    "Вчера",
    "Ввести дату (YYYY-MM-DD)",
    "Отмена",
]

ATTENDANCE_STATUS_BUTTONS = [
    "✅ Был",
    "❌ Не пришёл",
    "🚫 Отменил",
    "Назад",
    "Отмена",
]


def main_menu_keyboard(user_id: int, owner_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=MAIN_MENU_BUTTONS[0]), KeyboardButton(text=MAIN_MENU_BUTTONS[1])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[2]), KeyboardButton(text=MAIN_MENU_BUTTONS[3])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[4]), KeyboardButton(text=MAIN_MENU_BUTTONS[5])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[6]), KeyboardButton(text=MAIN_MENU_BUTTONS[7])],
    ]
    if user_id == owner_id:
        rows.append([KeyboardButton(text="👑 Админы")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=ADMIN_MENU_BUTTONS[0]), KeyboardButton(text=ADMIN_MENU_BUTTONS[1])],
        [KeyboardButton(text=ADMIN_MENU_BUTTONS[2])],
        [KeyboardButton(text=ADMIN_MENU_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def new_client_phone_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=NEW_CLIENT_PHONE_BUTTONS[0], request_contact=True)],
        [KeyboardButton(text=NEW_CLIENT_PHONE_BUTTONS[1])],
        [KeyboardButton(text=NEW_CLIENT_PHONE_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def skip_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=SKIP_BUTTONS[0])],
        [KeyboardButton(text=SKIP_BUTTONS[1])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def confirm_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=CONFIRM_BUTTONS[0])],
        [KeyboardButton(text=CONFIRM_BUTTONS[1])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def search_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=SEARCH_MENU_BUTTONS[0])],
        [KeyboardButton(text=SEARCH_MENU_BUTTONS[1])],
        [KeyboardButton(text=SEARCH_MENU_BUTTONS[2])],
        [KeyboardButton(text=SEARCH_MENU_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def not_found_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=MAIN_MENU_BUTTONS[0])],
        [KeyboardButton(text="❌ Отмена")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def search_results_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def client_actions_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=CLIENT_ACTION_BUTTONS[0]), KeyboardButton(text=CLIENT_ACTION_BUTTONS[1])],
        [KeyboardButton(text=CLIENT_ACTION_BUTTONS[2]), KeyboardButton(text=CLIENT_ACTION_BUTTONS[3])],
        [KeyboardButton(text=CLIENT_ACTION_BUTTONS[4])],
        [KeyboardButton(text=CLIENT_ACTION_BUTTONS[5])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def booking_client_search_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BOOKING_CLIENT_SEARCH_BUTTONS[0])],
        [KeyboardButton(text=BOOKING_CLIENT_SEARCH_BUTTONS[1])],
        [KeyboardButton(text=BOOKING_CLIENT_SEARCH_BUTTONS[2])],
        [KeyboardButton(text=BOOKING_CLIENT_SEARCH_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def booking_type_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BOOKING_TYPE_BUTTONS[0])],
        [KeyboardButton(text=BOOKING_TYPE_BUTTONS[1])],
        [KeyboardButton(text=BOOKING_TYPE_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def booking_date_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BOOKING_DATE_BUTTONS[0]), KeyboardButton(text=BOOKING_DATE_BUTTONS[1])],
        [KeyboardButton(text=BOOKING_DATE_BUTTONS[2])],
        [KeyboardButton(text=BOOKING_DATE_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def add_group_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=ADD_GROUP_BUTTONS[0])],
        [KeyboardButton(text=ADD_GROUP_BUTTONS[1])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def groups_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def attendance_date_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=ATTENDANCE_DATE_BUTTONS[0]), KeyboardButton(text=ATTENDANCE_DATE_BUTTONS[1])],
        [KeyboardButton(text=ATTENDANCE_DATE_BUTTONS[2])],
        [KeyboardButton(text=ATTENDANCE_DATE_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def attendance_status_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=ATTENDANCE_STATUS_BUTTONS[0]), KeyboardButton(text=ATTENDANCE_STATUS_BUTTONS[1])],
        [KeyboardButton(text=ATTENDANCE_STATUS_BUTTONS[2])],
        [KeyboardButton(text=ATTENDANCE_STATUS_BUTTONS[3])],
        [KeyboardButton(text=ATTENDANCE_STATUS_BUTTONS[4])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)
