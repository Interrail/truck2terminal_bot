from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from infrastructure.some_api.api import MyApi
from tgbot.keyboards.inline import send_route_details_keyboard

route_router = Router()


class RouteStates(StatesGroup):
    waiting_for_truck_number = State()
    waiting_for_start_location = State()
    waiting_for_terminal = State()
    waiting_for_container_name = State()
    waiting_for_container_size = State()
    waiting_for_container_type = State()
    finish_route = State()


LOCATION_CHOICES = [
    ("Tashkent", "Tashkent"),
    ("Navoi", "Navoi"),
    ("Samarkand", "Samarkand"),
    ("Bukhara", "Bukhara"),
    ("Andijan", "Andijan"),
    ("Fergana", "Fergana"),
    ("Namangan", "Namangan"),
    ("Qarshi", "Qarshi"),
    ("Termez", "Termez"),
    ("Urgench", "Urgench"),
    ("Nukus", "Nukus"),
    ("Jizzakh", "Jizzakh"),
]


@route_router.message(F.text == "Add Route")
async def start_route_creation(message: Message, state: FSMContext):
    """Start the route creation process with truck number input"""
    await state.set_state(RouteStates.waiting_for_truck_number)
    await message.reply("Please enter the truck number:", reply_markup=ReplyKeyboardRemove())


@route_router.message(RouteStates.waiting_for_truck_number)
async def process_truck_number(message: Message, state: FSMContext):
    """Process truck number input"""
    await state.update_data(truck_number=message.text)
    await state.set_state(RouteStates.waiting_for_start_location)

    # Create reply keyboard for location choices
    keyboard = ReplyKeyboardBuilder()
    for location, _ in LOCATION_CHOICES:
        keyboard.button(text=location)
    keyboard.adjust(2)  # Adjust to 2 buttons per row

    await message.reply(
        "Please choose the start location:",
        reply_markup=keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True),
    )


@route_router.message(RouteStates.waiting_for_start_location)
async def process_start_location(message: Message, state: FSMContext):
    """Process start location selection from reply keyboard"""
    selected_location = message.text
    # Validate the selected location
    if selected_location not in [loc for loc, _ in LOCATION_CHOICES]:
        await message.reply(
            "Please select a valid location from the keyboard.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=loc)] for loc, _ in LOCATION_CHOICES],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return

    await state.update_data(start_location=selected_location)

    # Show terminals after location selection
    terminals = [("ULS", 1), ("FTT", 2), ("MTT", 3)]
    keyboard = ReplyKeyboardBuilder()
    for name, _ in terminals:
        keyboard.button(text=name)
    keyboard.adjust(2)

    await state.set_state(RouteStates.waiting_for_terminal)
    await message.reply(
        "Please select a terminal:",
        reply_markup=keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True),
    )


@route_router.message(RouteStates.waiting_for_terminal)
async def process_terminal_selection(message: Message, state: FSMContext):
    """Process terminal selection from reply keyboard"""
    terminal_name = message.text
    terminals = [("ULS", 1), ("FTT", 2), ("MTT", 3)]
    terminal_dict = {name: id for name, id in terminals}

    if terminal_name not in terminal_dict:
        await message.reply(
            "Please select a valid terminal from the keyboard.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=name)] for name, _ in terminals],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return

    terminal_id = terminal_dict[terminal_name]
    await state.update_data(terminal_id=terminal_id)
    await state.set_state(RouteStates.waiting_for_container_name)

    await message.reply(
        "Please enter the container name:", reply_markup=ReplyKeyboardRemove()
    )


@route_router.message(RouteStates.waiting_for_container_name)
async def process_container_name(message: Message, state: FSMContext):
    """Process container name input"""
    await state.update_data(container_name=message.text)
    await state.set_state(RouteStates.waiting_for_container_size)

    # Create reply keyboard for container size
    keyboard = ReplyKeyboardBuilder()
    for size in ["20", "40"]:
        keyboard.button(text=size)
    keyboard.adjust(2)

    await message.reply(
        "Please select the container size:",
        reply_markup=keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True),
    )


@route_router.message(RouteStates.waiting_for_container_size)
async def process_container_size(message: Message, state: FSMContext):
    """Process container size selection from reply keyboard"""
    selected_size = message.text
    if selected_size not in ["20", "40"]:
        await message.reply(
            "Please select a valid container size from the keyboard.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=size)] for size in ["20", "40"]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return

    await state.update_data(container_size=selected_size)
    await state.set_state(RouteStates.waiting_for_container_type)

    # Create reply keyboard for container type
    keyboard = ReplyKeyboardBuilder()
    for type_ in ["Laden", "Empty"]:
        keyboard.button(text=type_)
    keyboard.adjust(2)

    await message.reply(
        "Please select the container type:",
        reply_markup=keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True),
    )


@route_router.message(RouteStates.waiting_for_container_type)
async def process_container_type(message: Message, state: FSMContext):
    """Process container type selection from reply keyboard"""
    selected_type = message.text.lower()
    if selected_type not in ["laden", "empty"]:
        await message.reply(
            "Please select a valid container type from the keyboard.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text=type_)] for type_ in ["Laden", "Empty"]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return

    await state.update_data(container_type=selected_type)
    await state.set_state(RouteStates.finish_route)

    user_data = await state.get_data()

    await message.reply(
        f"Route details:\n"
        f"- Truck Number: {user_data.get('truck_number')}\n"
        f"- Start Location: {user_data.get('start_location')}\n"
        f"- Terminal: {user_data.get('terminal_id')}\n"
        f"- Container: {user_data.get('container_name')} ({user_data.get('container_size')}ft)\n"
        f"- Type: {user_data.get('container_type')}",
        reply_markup=send_route_details_keyboard(),
    )


@route_router.callback_query(RouteStates.finish_route, F.data == "send_route_details")
async def process_send_route_details(callback: CallbackQuery, state: FSMContext):
    """Process final route submission"""
    user_data = await state.get_data()

    # Disable button and show loading
    await callback.message.edit_reply_markup(reply_markup=None)
    creating_message = await callback.message.reply("Creating route...")

    api = MyApi(api_key="your_api_key")
    try:
        status, result = await api.create_route(
            driver_id=callback.from_user.id,
            truck_number=user_data.get("truck_number"),
            terminal_id=user_data.get("terminal_id"),
            container_name=user_data.get("container_name"),
            container_size=user_data.get("container_size"),
            container_type=user_data.get("container_type"),
            start_location=user_data.get("start_location"),
            access_token=user_data.get("access_token"),
        )

        if status != 201:
            await creating_message.edit_text(f"❌ Failed to create route: {result}")
            return

        await creating_message.edit_text(
            f"✅ Route created successfully!\n"
            f"Truck: {user_data.get('truck_number')}\n"
            f"Start Location: {user_data.get('start_location')}\n"
            f"Terminal: {user_data.get('terminal_id')}\n"
            f"Container: {user_data.get('container_name')} ({user_data.get('container_size')}ft)\n"
            f"Type: {user_data.get('container_type')}"
        )
    except Exception as e:
        await creating_message.edit_text(f"❌ Failed to create route: {str(e)}")
    finally:
        await state.clear()
