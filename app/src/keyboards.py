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
