from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def simple_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Creates a simple menu keyboard with common options.

    Returns:
        InlineKeyboardMarkup: A keyboard with menu buttons.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="My Profile", callback_data="profile"),
                InlineKeyboardButton(text="Help", callback_data="help"),
            ],
            [
                InlineKeyboardButton(text="Settings", callback_data="settings"),
                InlineKeyboardButton(text="Support", callback_data="support"),
            ],
        ]
    )
    return keyboard


def send_route_details_keyboard() -> InlineKeyboardMarkup:
    """
    Creates a keyboard for sending route details.

    Returns:
        InlineKeyboardMarkup: A keyboard with a single button to send route details.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Send Route Details", callback_data="send_route_details"
                ),
            ]
        ]
    )
    return keyboard
