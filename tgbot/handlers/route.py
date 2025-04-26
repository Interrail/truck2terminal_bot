import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    user,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram3_calendar import SimpleCalendar, simple_cal_callback

from infrastructure.some_api.api import MyApi
from tgbot.keyboards.inline import (
    send_route_details_keyboard,
)
from tgbot.services.route_service import TERMINALS, RouteService

route_router = Router()
logger = logging.getLogger(__name__)


class RouteStates(StatesGroup):
    waiting_for_truck_front_number = State()
    waiting_for_truck_back_number = State()
    waiting_for_terminal = State()
    waiting_for_eta_date = State()
    waiting_for_eta_time = State()
    waiting_for_container_name = State()
    waiting_for_container_size = State()
    waiting_for_container_type = State()
    finish_route = State()
    live_location = State()


# Translations for route messages
ROUTE_TRANSLATIONS = {
    "uz": {
        "enter_truck_front_number": "🚚 Iltimos, yuk mashinasining old raqamini kiriting:",
        "enter_truck_back_number": "🚚 Endi orqa raqamini kiriting:",
        "select_terminal": "🏢 Terminalni tanlang:",
        "invalid_terminal": "⚠️ Iltimos, to'g'ri terminalni tanlang.",
        "enter_eta_date": "📅 Taxminiy kelish sanasini kiriting (YYYY-MM-DD formatida):",
        "enter_eta_time": "🕒 Taxminiy kelish vaqtini kiriting (HH:MM formatida):",
        "invalid_eta_format": "⚠️ Noto'g'ri format. Iltimos, ko'rsatilgan formatda qayta kiriting.",
        "enter_container_name": "📦 Konteyner nomini kiriting:",
        "select_container_size": "📏 Konteyner o'lchamini tanlang:",
        "invalid_container_size": "⚠️ Iltimos, to'g'ri konteyner o'lchamini tanlang.",
        "select_container_type": "🔍 Konteyner turini tanlang:",
        "invalid_container_type": "⚠️ Iltimos, to'g'ri konteyner turini tanlang.",
        "route_details": "📋 <b>Yo'nalish tafsilotlari:</b>\n\n🚚 Yuk mashinasi: <b>{}</b>\n🏢 Terminal: <b>{}</b>\n⏱ Taxminiy kelish vaqti: <b>{}</b>\n📦 Konteyner: <b>{}</b> (<b>{}</b>ft)\n🔍 Turi: <b>{}</b>",
        "creating_route": "⏳ <b>Yo'nalish yaratilmoqda...</b>",
        "route_created": "✅ <b>Yo'nalish muvaffaqiyatli yaratildi!</b>\n\n🚚 Yuk mashinasi: <b>{}</b>\n🏢 Terminal: <b>{}</b>\n⏱ Taxminiy kelish vaqti: <b>{}</b>\n📦 Konteyner: <b>{}</b> (<b>{}</b>ft)\n🔍 Turi: <b>{}</b>",
        "route_failed": "❌ <b>Yo'nalish yaratishda xatolik yuz berdi:</b> {}",
        "laden": "Yuklangan",
        "empty": "Bo'sh",
        "truck_number_received": "🚚 Yuk mashinasi raqami: <b>{}</b>",
        "terminal_selected": "🚚 Yuk mashinasi: <b>{}</b>\n🏢 Terminal: <b>{}</b>",
        "eta_selected": "🚚 Yuk mashinasi: <b>{}</b>\n🏢 Terminal: <b>{}</b>\n⏱ Taxminiy kelish vaqti: <b>{}</b>",
        "container_name_received": "🚚 Yuk mashinasi: <b>{}</b>\n🏢 Terminal: <b>{}</b>\n⏱ Taxminiy kelish vaqti: <b>{}</b>\n📦 Konteyner: <b>{}</b>",
        "container_size_selected": "🚚 Yuk mashinasi: <b>{}</b>\n🏢 Terminal: <b>{}</b>\n⏱ Taxminiy kelish vaqti: <b>{}</b>\n📦 Konteyner: <b>{}</b> (<b>{}</b>ft)",
        "location_tracking": "📍 Joylashuvni real vaqtda ulashing va qaytadan urinib ko'ring",
        "location_received_confirmation": "✅ Joylashuvingiz qabul qilindi.",
    },
    "ru": {
        "enter_truck_front_number": "🚚 Пожалуйста, введите передний номер грузовика:",
        "enter_truck_back_number": "🚚 Теперь введите задний номер:",
        "select_terminal": "🏢 Выберите терминал:",
        "invalid_terminal": "⚠️ Пожалуйста, выберите правильный терминал.",
        "enter_eta_date": "📅 Введите дату ожидаемого прибытия (в формате ГГГГ-ММ-ДД):",
        "enter_eta_time": "🕒 Введите время ожидаемого прибытия (в формате ЧЧ:ММ):",
        "invalid_eta_format": "⚠️ Неверный формат. Пожалуйста, введите в указанном формате.",
        "enter_container_name": "📦 Введите название контейнера:",
        "select_container_size": "📏 Выберите размер контейнера:",
        "invalid_container_size": "⚠️ Пожалуйста, выберите правильный размер контейнера.",
        "select_container_type": "🔍 Выберите тип контейнера:",
        "invalid_container_type": "⚠️ Пожалуйста, выберите правильный тип контейнера.",
        "route_details": "📋 <b>Детали маршрута:</b>\n\n🚚 Грузовик: <b>{}</b>\n🏢 Терминал: <b>{}</b>\n⏱ Ожидаемое время прибытия: <b>{}</b>\n📦 Контейнер: <b>{}</b> (<b>{}</b>фт)\n🔍 Тип: <b>{}</b>",
        "creating_route": "⏳ <b>Создание маршрута...</b>",
        "route_created": "✅ <b>Маршрут успешно создан!</b>\n\n🚚 Грузовик: <b>{}</b>\n🏢 Терминал: <b>{}</b>\n⏱ Ожидаемое время прибытия: <b>{}</b>\n📦 Контейнер: <b>{}</b> (<b>{}</b>фт)\n🔍 Тип: <b>{}</b>",
        "route_failed": "❌ <b>Не удалось создать маршрут:</b> {}",
        "laden": "Загруженный",
        "empty": "Пустой",
        "truck_number_received": "🚚 Номер грузовика: <b>{}</b>",
        "terminal_selected": "🚚 Грузовик: <b>{}</b>\n🏢 Терминал: <b>{}</b>",
        "eta_selected": "🚚 Грузовик: <b>{}</b>\n🏢 Терминал: <b>{}</b>\n⏱ Ожидаемое время прибытия: <b>{}</b>",
        "container_name_received": "🚚 Грузовик: <b>{}</b>\n🏢 Терминал: <b>{}</b>\n⏱ Ожидаемое время прибытия: <b>{}</b>\n📦 Контейнер: <b>{}</b>",
        "container_size_selected": "🚚 Грузовик: <b>{}</b>\n🏢 Терминал: <b>{}</b>\n⏱ Ожидаемое время прибытия: <b>{}</b>\n📦 Контейнер: <b>{}</b> (<b>{}</b>фт)",
        "location_tracking": "📍 Укажите местоположение в реальном времени и Попробуйте снова.",
        "location_received_confirmation": "✅ Ваше местоположение получено.",
    },
}

# Container size choices
CONTAINER_SIZES = ["20", "40", "45"]

# Container type choices
CONTAINER_TYPES = ["laden", "empty"]


@route_router.message(F.text.in_({"Yo'nalish qo'shish", "Добавить маршрут"}))
async def start_route_creation(
    message: Message, state: FSMContext, api_client, language, truck_number
):
    """Start the route creation process with truck number input (front and back)"""

    await state.set_state(RouteStates.waiting_for_truck_front_number)
    # Always save truck number in FSM state

    if truck_number:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=truck_number, callback_data=truck_number)
        await message.reply(
            ROUTE_TRANSLATIONS[language]["enter_truck_front_number"],
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML",
        )
    else:
        await message.reply(ROUTE_TRANSLATIONS[language]["enter_truck_front_number"])


@route_router.message(RouteStates.waiting_for_truck_front_number)
async def process_truck_front_number(
    message: Message, state: FSMContext, api_client, language
):
    """
    Process truck front number and move to back number input.
    """
    front_number = message.text
    await state.update_data(truck_front_number=front_number)
    await state.set_state(RouteStates.waiting_for_truck_back_number)
    await message.reply(ROUTE_TRANSLATIONS[language]["enter_truck_back_number"])


@route_router.message(RouteStates.waiting_for_truck_back_number)
async def process_truck_back_number(
    message: Message, state: FSMContext, api_client, language
):
    """
    Process truck back number, combine, and move to terminal selection.
    """
    back_number = message.text
    data = await state.get_data()
    front_number = data.get("`truck_front_number`", "")
    truck_number = f"{front_number}/{back_number}"
    await state.update_data(truck_back_number=back_number, truck_number=truck_number)

    # Fetch terminals (from API or fallback)
    route_service = RouteService(api_client=api_client)
    try:
        terminals = await route_service.get_terminals(message.from_user.id)
        await state.update_data(terminals=terminals)
    except Exception as e:
        print(f"Error fetching terminals: {e}")

    # Create terminal selection keyboard
    keyboard = InlineKeyboardBuilder()
    for terminal_name, terminal_id in terminals.items():
        keyboard.button(text=terminal_name, callback_data=terminal_name)
    keyboard.adjust(2)  # 2 buttons per row

    response_text = (
        f"{ROUTE_TRANSLATIONS[language]['truck_number_received'].format(truck_number)}\n\n"
        f"<b>{ROUTE_TRANSLATIONS[language]['select_terminal']}</b>"
    )
    await message.reply(
        response_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )
    await state.set_state(RouteStates.waiting_for_terminal)


@route_router.callback_query(RouteStates.waiting_for_terminal, F.data)
async def process_terminal_selection(
    callback: CallbackQuery, state: FSMContext, language
):
    """
    Process terminal selection and move to ETA date input.
    """
    await callback.answer()

    # Get the selected terminal
    terminal_name = callback.data

    # Get user data including terminals
    user_data = await state.get_data()
    terminals = user_data.get("terminals", TERMINALS)

    # Validate terminal selection
    if terminal_name not in terminals:
        # Invalid terminal selection
        await callback.message.edit_text(
            ROUTE_TRANSLATIONS[language]["invalid_terminal"],
            parse_mode="HTML",
        )
        return

    # Save to state
    await state.update_data(terminal=terminal_name)

    # Get user language
    truck_number = user_data.get("truck_number", "")

    # Set next state
    await state.set_state(RouteStates.waiting_for_eta_date)

    # Show accumulated information with calendar
    response_text = (
        f"{ROUTE_TRANSLATIONS[language]['terminal_selected'].format(truck_number, terminal_name)}\n\n"
        f"<b>{ROUTE_TRANSLATIONS[language]['enter_eta_date']}</b>"
    )

    # Create a calendar for date selection
    calendar = SimpleCalendar()

    await callback.message.edit_text(
        response_text,
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML",
    )


# Handle calendar selection
@route_router.callback_query(
    RouteStates.waiting_for_eta_date, simple_cal_callback.filter()
)
async def process_calendar_selection(
    callback: CallbackQuery, callback_data: dict, state: FSMContext, language
):
    """
    Process the calendar selection for ETA date.
    """
    # Get user data
    user_data = await state.get_data()

    # Initialize the calendar
    calendar = SimpleCalendar()

    # Process the calendar selection
    selected, date = await calendar.process_selection(callback, callback_data)

    if selected:
        # Date is selected, format it as YYYY-MM-DD
        date_str = date.strftime("%Y-%m-%d")

        # Save the date to state
        await state.update_data(eta_date=date_str)

        # Get other data
        truck_number = user_data.get("truck_number", "")
        terminal_name = user_data.get("terminal", "")

        # Set next state for time input
        await state.set_state(RouteStates.waiting_for_eta_time)

        # Show time selection keyboard
        await show_time_picker(callback.message, truck_number, terminal_name, language)


async def show_time_picker(message, truck_number, terminal_name, language):
    """
    Show time picker with inline keyboard.
    """
    # Create hours keyboard (0-23)
    keyboard = InlineKeyboardBuilder()

    # Add hour buttons (4 per row)
    for hour in range(24):
        keyboard.button(text=f"{hour:02d}:00", callback_data=f"time_hour_{hour:02d}")
    keyboard.adjust(4)  # 4 buttons per row

    # Show accumulated information with time picker
    response_text = (
        f"{ROUTE_TRANSLATIONS[language]['terminal_selected'].format(truck_number, terminal_name)}\n\n"
        f"<b>{ROUTE_TRANSLATIONS[language]['enter_eta_time']}</b>"
    )

    await message.edit_text(
        response_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )


@route_router.callback_query(
    RouteStates.waiting_for_eta_time, F.data.startswith("time_hour_")
)
async def process_hour_selection(callback: CallbackQuery, state: FSMContext, language):
    """
    Process hour selection and show minutes selection.
    """
    await callback.answer()

    # Extract selected hour
    selected_hour = callback.data.split("_")[2]

    # Save to state temporarily
    await state.update_data(selected_hour=selected_hour)

    # Get user data
    user_data = await state.get_data()
    truck_number = user_data.get("truck_number", "")
    terminal_name = user_data.get("terminal", "")

    # Show minutes keyboard (00, 15, 30, 45)
    keyboard = InlineKeyboardBuilder()
    for minute in ["00", "15", "30", "45"]:
        keyboard.button(
            text=f"{selected_hour}:{minute}", callback_data=f"time_minute_{minute}"
        )
    keyboard.adjust(2)  # 2 buttons per row

    # Add back button
    keyboard.button(text="← Back to hours", callback_data="time_back_to_hours")
    keyboard.adjust(2, 1)  # 2 buttons in first rows, 1 in last row

    # Show accumulated information with minutes picker
    response_text = (
        f"{ROUTE_TRANSLATIONS[language]['terminal_selected'].format(truck_number, terminal_name)}\n\n"
        f"<b>{ROUTE_TRANSLATIONS[language]['enter_eta_time']}</b>\n"
        f"Selected hour: {selected_hour}"
    )

    await callback.message.edit_text(
        response_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )


@route_router.callback_query(
    RouteStates.waiting_for_eta_time, F.data.startswith("time_minute_")
)
async def process_minute_selection(
    callback: CallbackQuery, state: FSMContext, language
):
    """
    Process minute selection and complete time selection.
    """
    await callback.answer()

    # Extract selected minute
    selected_minute = callback.data.split("_")[2]

    # Get user data including the previously selected hour
    user_data = await state.get_data()
    selected_hour = user_data.get("selected_hour")

    # Format the full time
    time_str = f"{selected_hour}:{selected_minute}"

    # Save the complete time to state
    await state.update_data(eta_time=time_str)

    # Get other data
    truck_number = user_data.get("truck_number", "")
    terminal_name = user_data.get("terminal", "")
    eta_date = user_data.get("eta_date", "")

    # Combine date and time
    eta = f"{eta_date} {time_str}"
    await state.update_data(eta=eta)

    # Set next state for container name input
    await state.set_state(RouteStates.waiting_for_container_name)

    # Show prompt for container name input
    response_text = (
        f"{ROUTE_TRANSLATIONS[language]['eta_selected'].format(truck_number, terminal_name, eta)}\n\n"
        f"<b>{ROUTE_TRANSLATIONS[language]['enter_container_name']}</b>"
    )

    await callback.message.edit_text(
        response_text,
        parse_mode="HTML",
    )


@route_router.callback_query(
    RouteStates.waiting_for_eta_time, F.data == "time_back_to_hours"
)
async def back_to_hours(callback: CallbackQuery, state: FSMContext, language):
    """
    Go back to hour selection.
    """
    await callback.answer()

    # Get user data
    user_data = await state.get_data()
    truck_number = user_data.get("truck_number", "")
    terminal_name = user_data.get("terminal", "")

    # Show hour selection again
    await show_time_picker(callback.message, truck_number, terminal_name, language)


@route_router.message(RouteStates.waiting_for_eta_date)
async def process_eta_date(message: Message, state: FSMContext):
    """
    Fallback handler for text input in ETA date state.
    Reminds the user to use the calendar.
    """
    # Get user language
    user_data = await state.get_data()
    language = user_data.get("language", "ru")

    # Remind user to use the calendar
    await message.reply(
        f"{ROUTE_TRANSLATIONS[language]['use_calendar']}",
        parse_mode="HTML",
    )

    # Re-send the calendar
    calendar = SimpleCalendar()

    # Get other data for the message
    truck_number = user_data.get("truck_number", "")
    terminal_name = user_data.get("terminal", "")

    # Show accumulated information with calendar
    response_text = (
        f"{ROUTE_TRANSLATIONS[language]['terminal_selected'].format(truck_number, terminal_name)}\n\n"
        f"<b>{ROUTE_TRANSLATIONS[language]['enter_eta_date']}</b>"
    )

    await message.reply(
        response_text,
        reply_markup=await calendar.start_calendar(),
        parse_mode="HTML",
    )


@route_router.message(RouteStates.waiting_for_eta_time)
async def process_eta_time(message: Message, state: FSMContext):
    """
    Fallback handler for text input in ETA time state.
    Reminds the user to use the time picker.
    """
    # Get user data
    user_data = await state.get_data()
    language = user_data.get("language", "ru")
    truck_number = user_data.get("truck_number", "")
    terminal_name = user_data.get("terminal", "")

    # Remind user to use the time picker
    await message.reply(
        "<b>Please use the buttons to select a time.</b>",
        parse_mode="HTML",
    )

    # Show time picker again
    await show_time_picker(
        await message.answer("..."),
        truck_number,
        terminal_name,
        language,
    )


@route_router.message(RouteStates.waiting_for_container_name)
async def process_container_name(message: Message, state: FSMContext, language):
    """
    Process container name and move to container size selection.
    """
    # Save container name to state
    container_name = message.text
    await state.update_data(container_name=container_name)

    # Get user language and other data
    user_data = await state.get_data()
    truck_number = user_data.get("truck_number", "")
    terminal_name = user_data.get("terminal", "")
    eta = user_data.get("eta", "")

    # Set next state
    await state.set_state(RouteStates.waiting_for_container_size)

    # Create container size selection keyboard
    keyboard = InlineKeyboardBuilder()
    for size in CONTAINER_SIZES:
        keyboard.button(text=f"{size}ft", callback_data=size)
    keyboard.adjust(3)  # 3 buttons per row

    # Show accumulated information
    response_text = (
        f"{ROUTE_TRANSLATIONS[language]['container_name_received'].format(truck_number, terminal_name, eta, container_name)}\n\n"
        f"<b>{ROUTE_TRANSLATIONS[language]['select_container_size']}</b>"
    )

    await message.reply(
        response_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )


@route_router.callback_query(
    RouteStates.waiting_for_container_size, F.data.in_(CONTAINER_SIZES)
)
async def process_container_size(callback: CallbackQuery, state: FSMContext, language):
    """
    Process container size selection and move to container type selection.
    """
    await callback.answer()

    # Get the selected container size
    container_size = callback.data

    # Save to state
    await state.update_data(container_size=container_size)

    # Get user language and other data
    user_data = await state.get_data()
    truck_number = user_data.get("truck_number", "")
    terminal_name = user_data.get("terminal", "")
    container_name = user_data.get("container_name", "")
    eta = user_data.get("eta", "")

    # Set next state
    await state.set_state(RouteStates.waiting_for_container_type)

    # Create container type selection keyboard
    keyboard = InlineKeyboardBuilder()
    for container_type in CONTAINER_TYPES:
        keyboard.button(
            text=ROUTE_TRANSLATIONS[language][container_type],
            callback_data=container_type,
        )
    keyboard.adjust(2)  # 2 buttons per row

    # Show accumulated information
    response_text = (
        f"{ROUTE_TRANSLATIONS[language]['container_size_selected'].format(truck_number, terminal_name, eta, container_name, container_size)}\n\n"
        f"<b>{ROUTE_TRANSLATIONS[language]['select_container_type']}</b>"
    )

    await callback.message.edit_text(
        response_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML",
    )


@route_router.callback_query(
    RouteStates.waiting_for_container_type, F.data.in_(CONTAINER_TYPES)
)
async def process_container_type(callback: CallbackQuery, state: FSMContext, language):
    """
    Process container type selection and show route details.
    """
    await callback.answer()

    # Get the selected container type
    container_type = callback.data

    # Save to state
    await state.update_data(container_type=container_type)

    # Get user language and other data
    user_data = await state.get_data()
    truck_number = user_data.get("truck_number", "")
    terminal_name = user_data.get("terminal", "")
    container_name = user_data.get("container_name", "")
    container_size = user_data.get("container_size", "")
    eta = user_data.get("eta", "")

    # Set next state
    await state.set_state(RouteStates.finish_route)

    # Format the route details
    formatted_details = ROUTE_TRANSLATIONS[language]["route_details"].format(
        truck_number,
        terminal_name,
        eta,
        container_name,
        container_size,
        ROUTE_TRANSLATIONS[language][container_type],
    )

    await callback.message.edit_text(
        formatted_details,
        reply_markup=send_route_details_keyboard(language),
        parse_mode="HTML",
    )


@route_router.callback_query(RouteStates.finish_route, F.data == "send_route_details")
async def process_send_route_details(
    callback: CallbackQuery, state: FSMContext, api_client, language
):
    """
    Process the final step of route creation.
    """
    await callback.answer()

    data = await state.get_data()
    await callback.message.edit_text(
        ROUTE_TRANSLATIONS[language]["creating_route"],
        parse_mode="HTML",
    )

    try:
        # Create route using RouteService
        # Use the shared API client from middleware instead of creating a new one
        route_service = RouteService(api_client=api_client)
        result = await route_service.create_route(
            telegram_id=callback.from_user.id,
            truck_number=data.get("truck_number", ""),
            terminal=data.get("terminal", ""),
            container_name=data.get("container_name", ""),
            container_size=data.get("container_size", ""),
            container_type=data.get("container_type", ""),
            eta=data.get(
                "eta", ""
            ),  # This is now a datetime string in format "YYYY-MM-DD HH:MM"
        )

        if result.get("success"):
            success_message = ROUTE_TRANSLATIONS[language]["route_created"].format(
                data["truck_number"],
                data["terminal"],
                data["eta"],  # Use the formatted version for display
                data["container_name"],
                data["container_size"],
                ROUTE_TRANSLATIONS[language]["laden"]
                if data["container_type"] == "laden"
                else ROUTE_TRANSLATIONS[language]["empty"],
            )
            await state.update_data(route_id=result["route_id"])

            await callback.message.edit_text(
                success_message,
                parse_mode="HTML",
            )

        else:
            await callback.message.edit_text(
                ROUTE_TRANSLATIONS[language]["route_failed"].format(result),
                parse_mode="HTML",
            )

    except Exception as e:
        await callback.message.edit_text(
            ROUTE_TRANSLATIONS[language]["route_failed"].format(str(e)),
            parse_mode="HTML",
        )
    finally:
        # Get all current user data
        user_data = await state.get_data()

        # Extract only the important user data that should be preserved
        preserved_data = {
            "user_id": user_data.get("user_id"),
            "language": user_data.get("language"),
            "first_name": user_data.get("first_name"),
            "phone_number": user_data.get("phone_number"),
            "username": user_data.get("username"),
            "role": user_data.get("role"),
            "route_id": user_data.get("route_id"),
        }
        preserved_data = {k: v for k, v in preserved_data.items() if v is not None}

        # Restore the preserved data
        if preserved_data:
            await state.update_data(**preserved_data)


@route_router.callback_query(
    lambda c: c.data and "/" in c.data and c.data.replace("/", "").isdigit()
)
async def process_truck_number_button(
    callback: CallbackQuery, state: FSMContext, api_client, language
):
    truck_number = callback.data
    route_service = RouteService(api_client=api_client)

    try:
        terminals = await route_service.get_terminals(callback.from_user.id)
        await state.update_data(terminals=terminals)
    except Exception as e:
        print(f"Error fetching terminals: {e}")

    # Create terminal selection keyboard
    keyboard = InlineKeyboardBuilder()
    for terminal_name, terminal_id in terminals.items():
        keyboard.button(text=terminal_name, callback_data=terminal_name)
    keyboard.adjust(2)  # 2 buttons per row
    await state.update_data(truck_number=truck_number)
    await state.set_state(RouteStates.waiting_for_terminal)
    await callback.message.edit_text(
        ROUTE_TRANSLATIONS[language]["select_terminal"],
        parse_mode="HTML",
        reply_markup=keyboard.as_markup(),
    )
