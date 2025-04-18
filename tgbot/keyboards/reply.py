from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Translations for reply keyboard buttons
REPLY_TRANSLATIONS = {
    "uz": {
        "add_route": "Yo'nalish qo'shish",
        "my_profile": "Mening profilim",
        "help": "Yordam",
        "settings": "Sozlamalar",
        "support": "Qo'llab-quvvatlash",
        "terminal": "Terminallar",
        "language": "Til",
        "back": "Orqaga",
        "send_location": "📍 Lokatsiyani yuborish",
    },
    "ru": {
        "add_route": "Добавить маршрут",
        "my_profile": "Мой профиль",
        "terminal": "Терминалы",
        "help": "Помощь",
        "settings": "Настройки",
        "support": "Поддержка",
        "language": "Язык",
        "back": "Назад",
        "send_location": "📍 Отправить локацию",
    },
}


def simple_menu_keyboard(language_code: str = "ru") -> ReplyKeyboardMarkup:
    """
    Creates a simple menu keyboard with common options.

    Args:
        language_code: User's selected language code (defaults to Russian)

    Returns:
        ReplyKeyboardMarkup: A keyboard with menu buttons.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=REPLY_TRANSLATIONS[language_code]["add_route"]),
                KeyboardButton(text=REPLY_TRANSLATIONS[language_code]["terminal"]),
            ],
            [
                KeyboardButton(text=REPLY_TRANSLATIONS[language_code]["my_profile"]),
                KeyboardButton(text=REPLY_TRANSLATIONS[language_code]["support"]),
            ],
            [
                KeyboardButton(
                    text=REPLY_TRANSLATIONS[language_code]["send_location"],
                    request_location=True,
                )
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard
