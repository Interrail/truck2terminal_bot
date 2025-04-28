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
    },
}


def main_menu_keyboard(lang="uz"):
    """
    Generate main menu keyboard with multilanguage support

    Args:
        lang (str): Language code ('uz' or 'ru')

    Returns:
        ReplyKeyboardMarkup: Keyboard with translated buttons
    """
    if lang not in REPLY_TRANSLATIONS:
        lang = "uz"  # Default to Uzbek if language not supported

    translations = REPLY_TRANSLATIONS[lang]

    keyboard = [
        [KeyboardButton(text=f"➕ {translations['add_route']}")],
        [KeyboardButton(text=f"👤 {translations['my_profile']}")],
        [KeyboardButton(text=f"🏢 {translations['terminal']}")],
        [KeyboardButton(text=f"❓ {translations['support']}")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
