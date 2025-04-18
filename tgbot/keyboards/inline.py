from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Translations for inline keyboard buttons
INLINE_TRANSLATIONS = {
    "uz": {
        "my_profile": "Mening profilim",
        "help": "Yordam",
        "settings": "Sozlamalar",
        "support": "Qo'llab-quvvatlash",
        "send_route_details": "Yo'nalish tafsilotlarini yuborish",
        "share_location": "Joylashuvni ulashish",
    },
    "ru": {
        "my_profile": "Мой профиль",
        "help": "Помощь",
        "settings": "Настройки",
        "support": "Поддержка",
        "send_route_details": "Отправить детали маршрута",
        "share_location": "Поделиться местоположением",
    },
}


def simple_menu_keyboard(language_code: str = "ru") -> InlineKeyboardMarkup:
    """
    Creates a simple menu keyboard with common options.

    Args:
        language_code: User's selected language code (defaults to Russian)

    Returns:
        InlineKeyboardMarkup: A keyboard with menu buttons in the selected language.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=INLINE_TRANSLATIONS[language_code]["my_profile"],
                    callback_data="profile",
                ),
                InlineKeyboardButton(
                    text=INLINE_TRANSLATIONS[language_code]["help"],
                    callback_data="help",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=INLINE_TRANSLATIONS[language_code]["settings"],
                    callback_data="settings",
                ),
                InlineKeyboardButton(
                    text=INLINE_TRANSLATIONS[language_code]["support"],
                    callback_data="support",
                ),
            ],
        ]
    )
    return keyboard


def send_route_details_keyboard(language_code: str = "ru") -> InlineKeyboardMarkup:
    """
    Creates a keyboard for sending route details.

    Args:
        language_code: User's selected language code (defaults to Russian)

    Returns:
        InlineKeyboardMarkup: A keyboard with a button to send route details in the selected language.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=INLINE_TRANSLATIONS[language_code]["send_route_details"],
                    callback_data="send_route_details",
                ),
            ]
        ]
    )
    return keyboard


def location_tracking_keyboard(language_code: str = "ru") -> InlineKeyboardMarkup:
    """
    Creates a keyboard for location tracking.

    Args:
        language_code: User's selected language code (defaults to Russian)

    Returns:
        InlineKeyboardMarkup: A keyboard with a button to share location in the selected language.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=INLINE_TRANSLATIONS[language_code]["share_location"],
                    callback_data="share_location",
                ),
            ]
        ]
    )
    return keyboard
