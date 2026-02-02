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
