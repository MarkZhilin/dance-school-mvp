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


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=MAIN_MENU_BUTTONS[0]), KeyboardButton(text=MAIN_MENU_BUTTONS[1])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[2]), KeyboardButton(text=MAIN_MENU_BUTTONS[3])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[4]), KeyboardButton(text=MAIN_MENU_BUTTONS[5])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[6]), KeyboardButton(text=MAIN_MENU_BUTTONS[7])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
