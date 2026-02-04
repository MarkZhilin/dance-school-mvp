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
    "🧑‍🏫 Тренеры",
    "👥 Группы",
]

REPORT_MENU_BUTTONS = [
    "💰 Выручка",
    "💸 Расходы",
    "📈 Прибыль",
    "👥 Посещаемость",
    "🎫 Абонементы",
    "🧾 Разовые",
    "⏳ Отсрочки",
    "📤 Excel директору",
    "↩️ Назад",
]

REPORT_PERIOD_BUTTONS = [
    "Этот месяц",
    "Прошлый месяц",
    "Эта неделя",
    "Сегодня",
    "Выбрать даты",
    "↩️ Назад",
]

REPORT_ACTION_BUTTONS = [
    "📅 Период",
    "↩️ Назад",
]

REPORT_ATTENDANCE_TODAY_BUTTON = "👥 Кто был сегодня"

TRAINERS_MENU_BUTTONS = [
    "➕ Добавить тренера",
    "📋 Список тренеров",
    "↩️ Назад",
]

TRAINER_ACTION_BUTTONS = [
    "➕ Привязать группу",
    "➕ Создать группу",
    "❌ Отвязать группу",
    "✏️ Переименовать тренера",
    "⛔️ Скрыть тренера",
    "✅ Активировать тренера",
    "↩️ Назад",
]

GROUPS_MENU_BUTTONS = [
    "➕ Создать группу",
    "📋 Список групп",
    "↩️ Назад",
]

GROUP_ACTION_BUTTONS = [
    "👤 Назначить тренера",
    "➕ Создать тренера и назначить",
    "❌ Убрать тренера",
    "✏️ Переименовать группу",
    "📅 Расписание",
    "⛔️ Скрыть группу",
    "✅ Активировать группу",
    "↩️ Назад",
]

GROUP_CREATE_ASSIGN_BUTTONS = [
    "👤 Выбрать тренера",
    "➕ Создать тренера",
    "Пропустить",
]

TRAINER_ATTACH_GROUP_NEW = "➕ Новая группа"
TRAINER_ATTACH_GROUP_BACK = "↩️ Назад"

TRAINER_DETACH_GROUP_BACK = "↩️ Назад"

GROUP_ASSIGN_TRAINER_NEW = "➕ Новый тренер"
GROUP_ASSIGN_TRAINER_BACK = "↩️ Назад"

SCHEDULE_MENU_BUTTONS = [
    "➕ Добавить день",
    "✏️ Изменить",
    "🗑 Удалить",
    "↩️ Назад",
]

SCHEDULE_WEEKDAY_BUTTONS = [
    "Пн",
    "Вт",
    "Ср",
    "Чт",
    "Пт",
    "Сб",
    "Вс",
    "↩️ Назад",
]

SCHEDULE_EDIT_BUTTONS = [
    "🕒 Время",
    "⏱ Длительность",
    "🏠 Зал",
    "⛔️ Отключить",
    "✅ Включить",
    "↩️ Назад",
]

SCHEDULE_DELETE_BUTTONS = [
    "✅ Да удалить",
    "❌ Отмена",
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

PAYMENT_MENU_BUTTONS = [
    "➕ Принять оплату",
    "🕒 Закрыть отсрочку",
    "↩️ Назад",
]

PAYMENT_TYPE_BUTTONS = [
    "Разовое",
    "Абонемент",
    "❌ Отмена",
]

PAYMENT_METHOD_BUTTONS = [
    "Наличные",
    "Перевод",
    "QR",
    "Отсрочка",
    "❌ Отмена",
]

PAYMENT_DATE_BUTTONS = [
    "Сегодня",
    "Вчера",
    "Ввести дату (YYYY-MM-DD)",
    "❌ Отмена",
]

DEFER_DUE_DATE_BUTTONS = [
    "Сегодня",
    "Завтра",
    "Выбрать дату",
    "Пропустить",
    "❌ Отмена",
]

PAYMENT_CLOSE_METHOD_BUTTONS = [
    "Наличные",
    "Перевод",
    "QR",
    "❌ Отмена",
]

PAYMENT_CLOSE_DATE_BUTTONS = [
    "Сегодня",
    "Вчера",
    "Выбрать дату",
    "❌ Отмена",
]

PASS_MENU_BUTTONS = [
    "🎫 Выдать",
    "🔁 Продлить",
    "↩️ Назад",
]

PASS_AFTER_SAVE_BUTTONS = [
    "💳 Принять оплату",
    "↩️ В меню 🎫 Абонемент",
]

PASS_PAY_METHOD_BUTTONS = [
    "💵 Наличные",
    "🔁 Перевод",
    "📷 QR-код",
    "⏳ Отсрочка",
    "↩️ Назад",
]

EXPENSE_MENU_BUTTONS = [
    "➕ Добавить расход",
    "📋 Список расходов",
    "🏷 Категории",
    "↩️ Назад",
]

EXPENSE_CATEGORY_MENU_BUTTONS = [
    "➕ Добавить",
    "✏️ Переименовать",
    "🙈 Скрыть категорию",
    "👁 Показать скрытые",
    "↩️ Назад",
]

EXPENSE_DATE_BUTTONS = [
    "Сегодня",
    "Вчера",
    "Выбрать дату",
    "🔁 Повторить последний расход",
    "↩️ Назад",
]

EXPENSE_METHOD_BUTTONS = [
    "Наличные",
    "Перевод",
    "QR",
    "↩️ Назад",
]

EXPENSE_CONFIRM_BUTTONS = [
    "✅ Сохранить",
    "✏️ Изменить",
    "❌ Отмена",
]

EXPENSE_COMMENT_BUTTONS = [
    "Пропустить",
    "↩️ Назад",
]

EXPENSE_LIST_PERIOD_BUTTONS = [
    "Сегодня",
    "Эта неделя",
    "Этот месяц",
    "Выбрать даты",
    "↩️ Назад",
]

EXPENSE_CARD_BUTTONS = [
    "✏️ Редактировать",
    "🗑 Удалить",
    "↩️ Назад",
]

EXPENSE_EDIT_BUTTONS = [
    "Категория",
    "Сумма",
    "Метод",
    "Комментарий",
    "↩️ Назад",
]

EXPENSE_CATEGORY_SELECT_ADD = "➕ Добавить категорию"
EXPENSE_CATEGORY_SELECT_BACK = "↩️ Назад"
EXPENSE_CATEGORY_SELECT_PREV = "⬅️ Назад"
EXPENSE_CATEGORY_SELECT_NEXT = "➡️ Вперёд"


def main_menu_keyboard(user_id: int, owner_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=MAIN_MENU_BUTTONS[0]), KeyboardButton(text=MAIN_MENU_BUTTONS[1])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[2]), KeyboardButton(text=MAIN_MENU_BUTTONS[3])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[4]), KeyboardButton(text=MAIN_MENU_BUTTONS[5])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[6]), KeyboardButton(text=MAIN_MENU_BUTTONS[7])],
        [KeyboardButton(text=MAIN_MENU_BUTTONS[8]), KeyboardButton(text=MAIN_MENU_BUTTONS[9])],
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


def report_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=REPORT_MENU_BUTTONS[0]), KeyboardButton(text=REPORT_MENU_BUTTONS[1])],
        [KeyboardButton(text=REPORT_MENU_BUTTONS[2]), KeyboardButton(text=REPORT_MENU_BUTTONS[3])],
        [KeyboardButton(text=REPORT_MENU_BUTTONS[4]), KeyboardButton(text=REPORT_MENU_BUTTONS[5])],
        [KeyboardButton(text=REPORT_MENU_BUTTONS[6]), KeyboardButton(text=REPORT_MENU_BUTTONS[7])],
        [KeyboardButton(text=REPORT_MENU_BUTTONS[8])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def report_period_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=REPORT_PERIOD_BUTTONS[0])],
        [KeyboardButton(text=REPORT_PERIOD_BUTTONS[1])],
        [KeyboardButton(text=REPORT_PERIOD_BUTTONS[2])],
        [KeyboardButton(text=REPORT_PERIOD_BUTTONS[3])],
        [KeyboardButton(text=REPORT_PERIOD_BUTTONS[4])],
        [KeyboardButton(text=REPORT_PERIOD_BUTTONS[5])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def report_actions_keyboard(include_attendance_today: bool = False) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=REPORT_ACTION_BUTTONS[0])]]
    if include_attendance_today:
        rows.append([KeyboardButton(text=REPORT_ATTENDANCE_TODAY_BUTTON)])
    rows.append([KeyboardButton(text=REPORT_ACTION_BUTTONS[1])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def report_date_input_keyboard() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="↩️ Назад")]]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def trainers_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=TRAINERS_MENU_BUTTONS[0])],
        [KeyboardButton(text=TRAINERS_MENU_BUTTONS[1])],
        [KeyboardButton(text=TRAINERS_MENU_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def trainers_list_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text=TRAINERS_MENU_BUTTONS[0])])
    rows.append([KeyboardButton(text=TRAINERS_MENU_BUTTONS[2])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def trainer_actions_keyboard(is_active: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=TRAINER_ACTION_BUTTONS[0]), KeyboardButton(text=TRAINER_ACTION_BUTTONS[1])],
        [KeyboardButton(text=TRAINER_ACTION_BUTTONS[2])],
        [KeyboardButton(text=TRAINER_ACTION_BUTTONS[3])],
    ]
    if is_active:
        rows.append([KeyboardButton(text=TRAINER_ACTION_BUTTONS[4])])
    else:
        rows.append([KeyboardButton(text=TRAINER_ACTION_BUTTONS[5])])
    rows.append([KeyboardButton(text=TRAINER_ACTION_BUTTONS[6])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def trainer_attach_group_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text=TRAINER_ATTACH_GROUP_NEW)])
    rows.append([KeyboardButton(text=TRAINER_ATTACH_GROUP_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def trainer_detach_group_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text=TRAINER_DETACH_GROUP_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def groups_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=GROUPS_MENU_BUTTONS[0])],
        [KeyboardButton(text=GROUPS_MENU_BUTTONS[1])],
        [KeyboardButton(text=GROUPS_MENU_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def groups_list_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text=GROUPS_MENU_BUTTONS[0])])
    rows.append([KeyboardButton(text=GROUPS_MENU_BUTTONS[2])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def group_actions_keyboard(is_active: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=GROUP_ACTION_BUTTONS[0])],
        [KeyboardButton(text=GROUP_ACTION_BUTTONS[1])],
        [KeyboardButton(text=GROUP_ACTION_BUTTONS[2])],
        [KeyboardButton(text=GROUP_ACTION_BUTTONS[3])],
        [KeyboardButton(text=GROUP_ACTION_BUTTONS[4])],
    ]
    if is_active:
        rows.append([KeyboardButton(text=GROUP_ACTION_BUTTONS[5])])
    else:
        rows.append([KeyboardButton(text=GROUP_ACTION_BUTTONS[6])])
    rows.append([KeyboardButton(text=GROUP_ACTION_BUTTONS[7])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def group_assign_trainer_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text=GROUP_ASSIGN_TRAINER_NEW)])
    rows.append([KeyboardButton(text=GROUP_ASSIGN_TRAINER_BACK)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def group_create_assign_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=GROUP_CREATE_ASSIGN_BUTTONS[0])],
        [KeyboardButton(text=GROUP_CREATE_ASSIGN_BUTTONS[1])],
        [KeyboardButton(text=GROUP_CREATE_ASSIGN_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def schedule_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=SCHEDULE_MENU_BUTTONS[0])],
        [KeyboardButton(text=SCHEDULE_MENU_BUTTONS[1])],
        [KeyboardButton(text=SCHEDULE_MENU_BUTTONS[2])],
        [KeyboardButton(text=SCHEDULE_MENU_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def schedule_weekday_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton(text=SCHEDULE_WEEKDAY_BUTTONS[0]),
            KeyboardButton(text=SCHEDULE_WEEKDAY_BUTTONS[1]),
            KeyboardButton(text=SCHEDULE_WEEKDAY_BUTTONS[2]),
        ],
        [
            KeyboardButton(text=SCHEDULE_WEEKDAY_BUTTONS[3]),
            KeyboardButton(text=SCHEDULE_WEEKDAY_BUTTONS[4]),
            KeyboardButton(text=SCHEDULE_WEEKDAY_BUTTONS[5]),
        ],
        [KeyboardButton(text=SCHEDULE_WEEKDAY_BUTTONS[6])],
        [KeyboardButton(text=SCHEDULE_WEEKDAY_BUTTONS[7])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def schedule_time_keyboard() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="↩️ Назад")]]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def schedule_duration_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Пропустить")],
        [KeyboardButton(text="↩️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def schedule_room_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Пропустить")],
        [KeyboardButton(text="↩️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def schedule_slots_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text="↩️ Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def schedule_edit_keyboard(is_active: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=SCHEDULE_EDIT_BUTTONS[0])],
        [KeyboardButton(text=SCHEDULE_EDIT_BUTTONS[1])],
        [KeyboardButton(text=SCHEDULE_EDIT_BUTTONS[2])],
    ]
    if is_active:
        rows.append([KeyboardButton(text=SCHEDULE_EDIT_BUTTONS[3])])
    else:
        rows.append([KeyboardButton(text=SCHEDULE_EDIT_BUTTONS[4])])
    rows.append([KeyboardButton(text=SCHEDULE_EDIT_BUTTONS[5])])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def schedule_delete_confirm_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=SCHEDULE_DELETE_BUTTONS[0])],
        [KeyboardButton(text=SCHEDULE_DELETE_BUTTONS[1])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


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


def payment_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PAYMENT_MENU_BUTTONS[0])],
        [KeyboardButton(text=PAYMENT_MENU_BUTTONS[1])],
        [KeyboardButton(text=PAYMENT_MENU_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def payment_type_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PAYMENT_TYPE_BUTTONS[0])],
        [KeyboardButton(text=PAYMENT_TYPE_BUTTONS[1])],
        [KeyboardButton(text=PAYMENT_TYPE_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def payment_method_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PAYMENT_METHOD_BUTTONS[0]), KeyboardButton(text=PAYMENT_METHOD_BUTTONS[1])],
        [KeyboardButton(text=PAYMENT_METHOD_BUTTONS[2]), KeyboardButton(text=PAYMENT_METHOD_BUTTONS[3])],
        [KeyboardButton(text=PAYMENT_METHOD_BUTTONS[4])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def payment_date_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PAYMENT_DATE_BUTTONS[0]), KeyboardButton(text=PAYMENT_DATE_BUTTONS[1])],
        [KeyboardButton(text=PAYMENT_DATE_BUTTONS[2])],
        [KeyboardButton(text=PAYMENT_DATE_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def defer_due_date_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=DEFER_DUE_DATE_BUTTONS[0]), KeyboardButton(text=DEFER_DUE_DATE_BUTTONS[1])],
        [KeyboardButton(text=DEFER_DUE_DATE_BUTTONS[2])],
        [KeyboardButton(text=DEFER_DUE_DATE_BUTTONS[3])],
        [KeyboardButton(text=DEFER_DUE_DATE_BUTTONS[4])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def payment_close_method_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PAYMENT_CLOSE_METHOD_BUTTONS[0]), KeyboardButton(text=PAYMENT_CLOSE_METHOD_BUTTONS[1])],
        [KeyboardButton(text=PAYMENT_CLOSE_METHOD_BUTTONS[2])],
        [KeyboardButton(text=PAYMENT_CLOSE_METHOD_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def payment_close_date_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PAYMENT_CLOSE_DATE_BUTTONS[0]), KeyboardButton(text=PAYMENT_CLOSE_DATE_BUTTONS[1])],
        [KeyboardButton(text=PAYMENT_CLOSE_DATE_BUTTONS[2])],
        [KeyboardButton(text=PAYMENT_CLOSE_DATE_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def pass_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PASS_MENU_BUTTONS[0])],
        [KeyboardButton(text=PASS_MENU_BUTTONS[1])],
        [KeyboardButton(text=PASS_MENU_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def passes_after_save_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PASS_AFTER_SAVE_BUTTONS[0])],
        [KeyboardButton(text=PASS_AFTER_SAVE_BUTTONS[1])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def pass_pay_method_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=PASS_PAY_METHOD_BUTTONS[0]), KeyboardButton(text=PASS_PAY_METHOD_BUTTONS[1])],
        [KeyboardButton(text=PASS_PAY_METHOD_BUTTONS[2]), KeyboardButton(text=PASS_PAY_METHOD_BUTTONS[3])],
        [KeyboardButton(text=PASS_PAY_METHOD_BUTTONS[4])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_MENU_BUTTONS[0])],
        [KeyboardButton(text=EXPENSE_MENU_BUTTONS[1])],
        [KeyboardButton(text=EXPENSE_MENU_BUTTONS[2])],
        [KeyboardButton(text=EXPENSE_MENU_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_category_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_CATEGORY_MENU_BUTTONS[0])],
        [KeyboardButton(text=EXPENSE_CATEGORY_MENU_BUTTONS[1])],
        [KeyboardButton(text=EXPENSE_CATEGORY_MENU_BUTTONS[2])],
        [KeyboardButton(text=EXPENSE_CATEGORY_MENU_BUTTONS[3])],
        [KeyboardButton(text=EXPENSE_CATEGORY_MENU_BUTTONS[4])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_date_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_DATE_BUTTONS[0]), KeyboardButton(text=EXPENSE_DATE_BUTTONS[1])],
        [KeyboardButton(text=EXPENSE_DATE_BUTTONS[2])],
        [KeyboardButton(text=EXPENSE_DATE_BUTTONS[3])],
        [KeyboardButton(text=EXPENSE_DATE_BUTTONS[4])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_method_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_METHOD_BUTTONS[0]), KeyboardButton(text=EXPENSE_METHOD_BUTTONS[1])],
        [KeyboardButton(text=EXPENSE_METHOD_BUTTONS[2])],
        [KeyboardButton(text=EXPENSE_METHOD_BUTTONS[3])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_confirm_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_CONFIRM_BUTTONS[0])],
        [KeyboardButton(text=EXPENSE_CONFIRM_BUTTONS[1])],
        [KeyboardButton(text=EXPENSE_CONFIRM_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_comment_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_COMMENT_BUTTONS[0])],
        [KeyboardButton(text=EXPENSE_COMMENT_BUTTONS[1])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_list_period_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_LIST_PERIOD_BUTTONS[0]), KeyboardButton(text=EXPENSE_LIST_PERIOD_BUTTONS[1])],
        [KeyboardButton(text=EXPENSE_LIST_PERIOD_BUTTONS[2])],
        [KeyboardButton(text=EXPENSE_LIST_PERIOD_BUTTONS[3])],
        [KeyboardButton(text=EXPENSE_LIST_PERIOD_BUTTONS[4])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_card_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_CARD_BUTTONS[0]), KeyboardButton(text=EXPENSE_CARD_BUTTONS[1])],
        [KeyboardButton(text=EXPENSE_CARD_BUTTONS[2])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_edit_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=EXPENSE_EDIT_BUTTONS[0]), KeyboardButton(text=EXPENSE_EDIT_BUTTONS[1])],
        [KeyboardButton(text=EXPENSE_EDIT_BUTTONS[2]), KeyboardButton(text=EXPENSE_EDIT_BUTTONS[3])],
        [KeyboardButton(text=EXPENSE_EDIT_BUTTONS[4])],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def categories_selection_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text="↩️ Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expense_category_select_keyboard(
    labels: list[str], show_nav: bool
) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text=EXPENSE_CATEGORY_SELECT_ADD)])
    rows.append([KeyboardButton(text=EXPENSE_CATEGORY_SELECT_BACK)])
    if show_nav:
        rows.append(
            [
                KeyboardButton(text=EXPENSE_CATEGORY_SELECT_PREV),
                KeyboardButton(text=EXPENSE_CATEGORY_SELECT_NEXT),
            ]
        )
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def expenses_selection_keyboard(labels: list[str]) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=label)] for label in labels]
    rows.append([KeyboardButton(text="↩️ Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)
