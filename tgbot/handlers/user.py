from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup

from infrastructure.some_api.api import MyApi
from tgbot.keyboards.reply import main_menu_keyboard

registration_router = Router()


# Registration FSM
class RegistrationStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_phone = State()
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_truck_number = State()


# Available languages
LANGUAGES = {
    "🇺🇿 O'zbek": "uz",
    "🇷🇺 Русский": "ru",
}


# Helper keyboards
def get_language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang)] for lang in LANGUAGES.keys()],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_phone_keyboard(language):
    text = (
        "📱 Telefon raqamni ulashish" if language == "uz" else "📱 Поделиться номером"
    )
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@registration_router.message(F.text == "/start")
async def cmd_start(
    message: Message,
    state: FSMContext,
    language: str,
    truck_number: str,
    api_client: MyApi = None,
):
    await state.clear()

    if truck_number:  # ✅ Already registered
        await message.answer(
            f"👋 Xush kelibsiz qaytib, <b>{message.from_user.full_name}</b>! 🚛",
            reply_markup=main_menu_keyboard(language),
            parse_mode="HTML",
        )
    else:  # 🚫 Not registered yet
        await state.set_state(RegistrationStates.waiting_for_language)
        await message.answer(
            "🛻 <b>Truck2Terminalga xush kelibsiz!</b>\n\n🌍 Iltimos, tilni tanlang:",
            reply_markup=get_language_keyboard(),
            parse_mode="HTML",
        )


# Language selected
@registration_router.message(RegistrationStates.waiting_for_language)
async def process_language(message: Message, state: FSMContext):
    selected_language = LANGUAGES.get(message.text)
    if not selected_language:
        await message.answer(
            "⚠️ Iltimos, klaviaturadan tilni tanlang.",
            reply_markup=get_language_keyboard(),
        )
        return

    await state.update_data(language=selected_language)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer(
        f"✅ Til tanlandi! (1/5)\n\n📱 Telefon raqamingizni ulashing:",
        reply_markup=get_phone_keyboard(selected_language),
        parse_mode="HTML",
    )


# Phone number received
@registration_router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if not message.contact:
        user_data = await state.get_data()
        language = user_data.get("language", "uz")
        await message.answer(
            "⚠️ Tugmadan foydalanib telefon raqamingizni ulashing!",
            reply_markup=get_phone_keyboard(language),
        )
        return

    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(RegistrationStates.waiting_for_first_name)
    await message.answer(
        "✅ Telefon raqami qabul qilindi! (2/5)\n\n👤 Ismingizni yozing:",
        parse_mode="HTML",
    )


# First name received
@registration_router.message(RegistrationStates.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    if not message.text.strip():
        await message.answer("⚠️ Iltimos, ismingizni yozing!")
        return

    await state.update_data(first_name=message.text.strip())
    await state.set_state(RegistrationStates.waiting_for_last_name)
    await message.answer(
        "✅ Ism qabul qilindi! (3/5)\n\n👥 Endi familiyangizni yozing:",
        parse_mode="HTML",
    )


# Last name received
@registration_router.message(RegistrationStates.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    if not message.text.strip():
        await message.answer("⚠️ Iltimos, familiyangizni yozing!")
        return

    await state.update_data(last_name=message.text.strip())
    await state.set_state(RegistrationStates.waiting_for_truck_number)
    await message.answer(
        "✅ Familiya qabul qilindi! (4/5)\n\n🚛 Yuk mashinangiz raqamini yuboring.\n\n<b>Namuna:</b> 01W540MC/106413BA",
        parse_mode="HTML",
    )


# Truck number received
@registration_router.message(RegistrationStates.waiting_for_truck_number)
async def process_truck_number(
    message: Message, state: FSMContext, api_client: MyApi = None
):
    if "/" not in message.text.strip():
        await message.answer(
            "⚠️ Yuk mashina raqamini to'g'ri formatda kiriting: 01W540MC/106413BA"
        )
        return

    await state.update_data(truck_number=message.text.strip())
    data = await state.get_data()

    registration_data = {
        "telegram_id": message.from_user.id,
        "phone_number": data.get("phone"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "truck_number": data.get("truck_number"),
        "language": data.get("language"),
        "role": "driver",
    }

    try:
        api = api_client or MyApi()
        await api.telegram_auth(**registration_data)

        await message.answer(
            f"✅ Ro'yxatdan o'tish yakunlandi! (5/5)\n\n👋 Xush kelibsiz, {data.get('first_name')}!\n\n📋 Quyidagi menyudan foydalaning:",
            reply_markup=main_menu_keyboard(data.get("language")),
            parse_mode="HTML",
        )
        await state.clear()

    except Exception as e:
        await message.answer(
            f"❌ Ro'yxatdan o'tishda xatolik: {str(e)}",
            parse_mode="HTML",
        )


# Global fallback for unknown text during registration
@registration_router.message()
async def fallback_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state and current_state.startswith("RegistrationStates"):
        await message.answer(
            "⚠️ Iltimos, tugmalardan foydalaning yoki ko'rsatilgan ma'lumotlarni yuboring."
        )
