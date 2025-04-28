from typing import Any, Dict, List

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from infrastructure.some_api.api import MyApi

# Router instance
terminals_router = Router()


# Define states for terminal viewing
class TerminalStates(StatesGroup):
    viewing_terminals = State()
    viewing_terminal_details = State()


# CallbackData factories (aiogram 3.x style)
class TerminalCallbackFactory(CallbackData, prefix="terminal"):
    terminal_id: str


class LocationCallbackFactory(CallbackData, prefix="location"):
    terminal_id: str


class BackToTerminalsCallbackFactory(CallbackData, prefix="back_terminals"):
    pass


def terminals_keyboard(
    terminals: List[Dict[str, Any]], lang: str = "ru"
) -> InlineKeyboardMarkup:
    """
    Creates inline keyboard with terminal names.
    """
    buttons = []
    for term in terminals:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=term["name"],
                    callback_data=TerminalCallbackFactory(
                        terminal_id=str(term["id"])
                    ).pack(),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def terminal_details_message(terminal: Dict[str, Any], lang: str = "ru") -> str:
    """
    Formats terminal details for display.
    """
    fields = [
        f"<b>{terminal.get('name', '')}</b>",
        f"{terminal.get('full_name', '')}",
        f"\n<b>Адрес:</b> {terminal.get('address', '')}",
        f"<b>Локация:</b> {terminal.get('location', '')}",
        f"<b>Вместимость:</b> {terminal.get('capacity', '')}",
        f"<b>Рабочие дни:</b> {terminal.get('working_days', '')}",
        f"<b>Телефон:</b> {terminal.get('phone_numbers', '')}",
        f"<b>Email:</b> {terminal.get('email', '')}",
    ]
    return "\n".join([f for f in fields if f and f.strip()])


def terminal_details_keyboard(
    terminal: Dict[str, Any], lang: str = "ru"
) -> InlineKeyboardMarkup:
    """
    Inline keyboard for terminal details: location (if present) and back button.
    """
    buttons = []
    if terminal.get("longitude") and terminal.get("latitude"):
        buttons.append(
            [
                InlineKeyboardButton(
                    text="📍 Локация" if lang == "ru" else "📍 Joylashuv",
                    callback_data=LocationCallbackFactory(
                        terminal_id=str(terminal["id"])
                    ).pack(),
                )
            ]
        )
    # Back button (always present)
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад" if lang == "ru" else "⬅️ Orqaga",
                callback_data=BackToTerminalsCallbackFactory().pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def terminal_location_keyboard(
    terminal: Dict[str, Any], lang: str = "ru"
) -> InlineKeyboardMarkup:
    """
    Inline keyboard with location button if lat/lng present.
    """
    buttons = []
    if terminal.get("longitude") and terminal.get("latitude"):
        buttons.append(
            [
                InlineKeyboardButton(
                    text="📍 Локация" if lang == "ru" else "📍 Joylashuv",
                    callback_data=LocationCallbackFactory(
                        terminal_id=str(terminal["id"])
                    ).pack(),
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@terminals_router.message(F.text.in_(["🏢 Терминалы", "🏢 Terminallar"]))
async def terminals_menu(message: Message, state: FSMContext, api_client, language):
    # Set state to viewing terminals
    await state.set_state(TerminalStates.viewing_terminals)

    # Initialize API and fetch terminals
    # Use the shared API client from middleware instead of creating a new one
    api = api_client or MyApi()
    terminals = await api.get_terminals(telegram_id=message.from_user.id)

    if not terminals:
        await message.answer(
            "Терминалы не найдены" if language == "ru" else "Terminallar topilmadi"
        )
        return

    # Store terminals in state to avoid re-fetching
    await state.update_data(terminals=terminals)

    await message.answer(
        "Выберите терминал:" if language == "ru" else "Terminalni tanlang:",
        reply_markup=terminals_keyboard(terminals, language),
    )


@terminals_router.callback_query(TerminalCallbackFactory.filter())
async def terminal_selected(
    call: CallbackQuery,
    callback_data: TerminalCallbackFactory,
    state: FSMContext,
    api_client,
    language,
):
    """
    Handler for terminal selection - shows terminal details.
    """
    # Get terminal details directly from API
    terminal_id = int(callback_data.terminal_id)
    # Use the shared API client from middleware instead of creating a new one
    api = api_client or MyApi()

    try:
        # Fetch specific terminal details using the new API endpoint
        terminal = await api.get_terminal(
            terminal_id=terminal_id, telegram_id=call.from_user.id
        )

        if not terminal:
            await call.answer(
                "Терминал не найден" if language == "ru" else "Terminal topilmadi",
                show_alert=True,
            )
            return

        # Set state to viewing terminal details
        await state.set_state(TerminalStates.viewing_terminal_details)
        await state.update_data(current_terminal_id=terminal_id)

        # Show terminal details
        await call.message.edit_text(
            terminal_details_message(terminal, language),
            parse_mode="HTML",
            reply_markup=terminal_details_keyboard(terminal, language),
        )
        await call.answer()

    except Exception as e:
        print(f"Terminal details error: {e}")
        await call.answer(
            "Ошибка при получении данных терминала"
            if language == "ru"
            else "Terminal ma'lumotlarini olishda xatolik",
            show_alert=True,
        )


@terminals_router.callback_query(LocationCallbackFactory.filter())
async def terminal_location(
    call: CallbackQuery,
    callback_data: LocationCallbackFactory,
    state: FSMContext,
    api_client,
    language,
):
    """
    Handler for location button - sends terminal location.
    """
    # Get terminal details directly from API
    terminal_id = int(callback_data.terminal_id)
    # Use the shared API client from middleware instead of creating a new one
    api = api_client or MyApi()

    try:
        # Fetch specific terminal details using the new API endpoint
        terminal = await api.get_terminal(
            terminal_id=terminal_id, telegram_id=call.from_user.id
        )

        if (
            not terminal
            or not terminal.get("latitude")
            or not terminal.get("longitude")
        ):
            await call.answer(
                "Локация недоступна" if language == "ru" else "Joylashuv mavjud emas",
                show_alert=True,
            )
            return

        # Send location
        await call.message.bot.send_location(
            chat_id=call.message.chat.id,
            latitude=terminal["latitude"],
            longitude=terminal["longitude"],
        )
        await call.answer()

    except Exception as e:
        print(f"Terminal location error: {e}")
        await call.answer(
            "Ошибка при получении локации"
            if language == "ru"
            else "Joylashuvni olishda xatolik",
            show_alert=True,
        )


@terminals_router.callback_query(BackToTerminalsCallbackFactory.filter())
async def back_to_terminals(
    call: CallbackQuery, state: FSMContext, api_client, language
):
    """
    Handler for back button - returns to terminal list.
    """
    # Set state back to viewing terminals list
    await state.set_state(TerminalStates.viewing_terminals)

    # Fetch fresh terminal list
    # Use the shared API client from middleware instead of creating a new one
    api = api_client or MyApi()
    try:
        terminals = await api.get_terminals(telegram_id=call.from_user.id)

        await call.message.edit_text(
            "Выберите терминал:" if language == "ru" else "Terminalni tanlang:",
            reply_markup=terminals_keyboard(terminals, language),
        )
        await call.answer()

    except Exception as e:
        print(f"Terminal list error: {e}")
        await call.answer(
            "Ошибка при получении списка терминалов"
            if language == "ru"
            else "Terminallar ro'yxatini olishda xatolik",
            show_alert=True,
        )
