from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def simple_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Creates a simple menu keyboard with common options.

    Returns:
        ReplyKeyboardMarkup: A keyboard with menu buttons.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Add Route"),
            ],
            [
                KeyboardButton(text="My Profile"),
                KeyboardButton(text="Help"),
            ],
            [
                KeyboardButton(text="Settings"),
                KeyboardButton(text="Support"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard
