from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    await message.reply("Please enter the truck number:")


@route_router.message(RouteStates.waiting_for_truck_number)
async def process_truck_number(message: Message, state: FSMContext):
    """Process truck number input"""
    await state.update_data(truck_number=message.text)
    await state.set_state(RouteStates.waiting_for_start_location)

    keyboard = InlineKeyboardBuilder()
    for location, callback_data in LOCATION_CHOICES:
        keyboard.button(text=location, callback_data=callback_data)
    keyboard.adjust(2)

    await message.reply(
        "Please choose the start location:", reply_markup=keyboard.as_markup()
    )


@route_router.callback_query(RouteStates.waiting_for_start_location)
async def process_start_location(callback: CallbackQuery, state: FSMContext):
    """Process start location selection from inline keyboard"""
    await state.update_data(start_location=callback.data)

    # Show terminals after location selection
    terminals = [("ULS", 1), ("FTT", 2), ("MTT", 3)]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"terminal_{id}")]
            for name, id in terminals
        ]
    )

    await state.set_state(RouteStates.waiting_for_terminal)
    await callback.message.edit_text(
        f"Start location: {callback.data}\nPlease select a terminal:",
        reply_markup=keyboard,
    )
    await callback.answer()


@route_router.callback_query(F.data.startswith("terminal_"))
async def process_terminal_selection(callback: CallbackQuery, state: FSMContext):
    """Process terminal selection from inline keyboard"""
    terminal_id = int(callback.data.split("_")[1])
    await state.update_data(terminal_id=terminal_id)
    await state.set_state(RouteStates.waiting_for_container_name)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Please enter the container name:")


@route_router.message(RouteStates.waiting_for_container_name)
async def process_container_name(message: Message, state: FSMContext):
    """Process container name input"""
    await state.update_data(container_name=message.text)
    await state.set_state(RouteStates.waiting_for_container_size)
    await message.reply("Please enter the container size (20/40):")


@route_router.message(RouteStates.waiting_for_container_size)
async def process_container_size(message: Message, state: FSMContext):
    """Process container size input"""
    if message.text not in ["20", "40"]:
        await message.reply("Please enter a valid container size (20 or 40):")
        return

    await state.update_data(container_size=message.text)
    await state.set_state(RouteStates.waiting_for_container_type)
    await message.reply("Please enter the container type (laden/empty):")


@route_router.message(RouteStates.waiting_for_container_type)
async def process_container_type(message: Message, state: FSMContext):
    """Process container type input"""
    if message.text.lower() not in ["laden", "empty"]:
        await message.reply("Please enter a valid container type (laden or empty):")
        return

    await state.update_data(container_type=message.text.lower())
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
async def process_start_location_message(callback: CallbackQuery, state: FSMContext):
    """Process start location and create route"""
    user_data = await state.get_data()

    # Disable button and show loading
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply("Creating route...")

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
            await callback.message.reply(f"❌ Failed to create route: {result}")
            return

        await callback.message.reply(
            f"✅ Route created successfully!\n"
            f"Truck: {user_data.get('truck_number')}\n"
            f"Start Location: {user_data.get('start_location')}\n"
            f"Terminal: {user_data.get('terminal_id')}\n"
            f"Container: {user_data.get('container_name')} ({user_data.get('container_size')}ft)\n"
            f"Type: {user_data.get('container_type')}"
        )
    except Exception as e:
        await callback.message.reply(f"❌ Failed to create route: {str(e)}")
    finally:
        await state.clear()
