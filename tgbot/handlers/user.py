from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from infrastructure.some_api.api import MyApi
from tgbot.keyboards.reply import simple_menu_keyboard

user_router = Router()


# Define states for registration process
class RegistrationStates(StatesGroup):
    waiting_for_phone = State()


# Create keyboard with button to request phone number
def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Share Phone Number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


@user_router.message(CommandStart())
async def user_start(message: Message, state: FSMContext):
    """
    Start command handler. Begins the registration process.
    """
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.reply(
        "Welcome to Truck2Terminal! To register, please share your phone number.",
        reply_markup=get_phone_keyboard(),
    )


@user_router.message(Command("register"))
async def register_command(message: Message, state: FSMContext):
    """
    Explicit registration command.
    """
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.reply(
        "To register, please share your phone number.",
        reply_markup=get_phone_keyboard(),
    )


@user_router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone_number(message: Message, state: FSMContext):
    """
    Process the shared phone number and register the user.
    """
    # Clear the state
    await state.clear()

    # Get user info
    contact = message.contact
    phone_number = contact.phone_number
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    # Send registration request
    try:
        api = MyApi(api_key="your_api_key")
        result = await api.telegram_auth(
            telegram_id=telegram_id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
        )

        # Store tokens in state for future use
        await state.update_data(
            access_token=result.get("access"),
            refresh_token=result.get("refresh"),
            user_id=result.get("user_id"),
            username=result.get("username"),
            role=result.get("role"),
        )

        await message.reply(
            f"Registration successful! Welcome to Truck2Terminal, {first_name}!",
            reply_markup=simple_menu_keyboard(),
        )
    except Exception as e:
        await message.reply(
            f"Registration failed. Please try again later.\nError: {str(e)}",
            reply_markup=ReplyKeyboardRemove(),
        )


# Handle text messages during phone number request (invalid input)
@user_router.message(RegistrationStates.waiting_for_phone)
async def invalid_phone_input(message: Message):
    """
    Handle invalid input during phone number request.
    """
    await message.reply(
        "Please share your phone number using the button below.",
        reply_markup=get_phone_keyboard(),
    )
