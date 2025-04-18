import aiohttp
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Location,
    Message,
    ReplyKeyboardMarkup,
)

from infrastructure.some_api.api import MyApi
from tgbot.keyboards.reply import simple_menu_keyboard

user_router = Router()


# Define states for registration process
class RegistrationStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_phone = State()


# Define states for terminal viewing
class TerminalStates(StatesGroup):
    waiting_for_terminal_selection = State()


# Define states for registration wizard
class RegistrationWizard(StatesGroup):
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

# Translations for messages
TRANSLATIONS = {
    "uz": {
        "welcome": "<b>Truck2Terminal botiga xush kelibsiz!</b> Iltimos, tilingizni tanlang.",
        "select_language": "<b>Iltimos, tilingizni tanlang.</b>",
        "share_phone": "<b>Ro'yxatdan o'tish uchun telefon raqamingizni ulashing.</b>",
        "share_phone_button": "📱 Telefon raqamni ulashish",
        "registration_success": "✅ <b>Ro'yxatdan o'tish muvaffaqiyatli!</b> Truck2Terminal'ga xush kelibsiz, <b>{}</b>!",
        "registration_failed": "❌ <b>Ro'yxatdan o'tish muvaffaqiyatsiz tugadi.</b> Iltimos, keyinroq qayta urinib ko'ring.\nXato: {}",
        "use_button": "⚠️ <b>Iltimos, quyidagi tugmadan foydalanib telefon raqamingizni ulashing.</b>",
        "welcome_back": "👋 <b>Qaytganingizdan xursandmiz, {}!</b> Quyidagi menyudan foydalanib davom eting.",
        "terminals_title": "📋 <b>Mavjud terminallar ro'yxati:</b>",
        "terminal_details": """
🏢 <b>{name}</b> ({slug})
📍 <b>Manzil:</b> {address}
📱 <b>Telefon:</b> {phone_numbers}
📧 <b>Email:</b> {email}
⏰ <b>Ish vaqti:</b> {working_days}
""",
        "loading_terminals": "⏳ <b>Terminallar ma'lumotlari yuklanmoqda...</b>",
        "terminals_error": "❌ <b>Terminallar ma'lumotlarini olishda xatolik yuz berdi.</b> Iltimos, keyinroq qayta urinib ko'ring.",
        "show_on_map": "🗺️ Xaritada ko'rsatish",
        "back": "⬅️ Orqaga",
        "location_received": "Lokatsiya qabul qilindi!",
        "live_location_received": "Jonli lokatsiya qabul qilindi! Rahmat.",
    },
    "ru": {
        "welcome": "<b>Добро пожаловать в Truck2Terminal!</b> Пожалуйста, выберите язык.",
        "select_language": "<b>Пожалуйста, выберите язык.</b>",
        "share_phone": "<b>Чтобы зарегистрироваться, поделитесь своим номером телефона.</b>",
        "share_phone_button": "📱 Поделиться номером телефона",
        "registration_success": "✅ <b>Регистрация успешна!</b> Добро пожаловать в Truck2Terminal, <b>{}</b>!",
        "registration_failed": "❌ <b>Регистрация не удалась.</b> Пожалуйста, попробуйте позже.\nОшибка: {}",
        "use_button": "⚠️ <b>Пожалуйста, поделитесь своим номером телефона, используя кнопку ниже.</b>",
        "welcome_back": "👋 <b>Рады видеть вас снова, {}!</b> Продолжайте, используя меню ниже.",
        "terminals_title": "📋 <b>Список доступных терминалов:</b>",
        "terminal_details": """
🏢 <b>{name}</b> ({slug})
📍 <b>Адрес:</b> {address}
📱 <b>Телефон:</b> {phone_numbers}
📧 <b>Email:</b> {email}
⏰ <b>Время работы:</b> {working_days}
""",
        "loading_terminals": "⏳ <b>Загрузка информации о терминалах...</b>",
        "terminals_error": "❌ <b>Ошибка при получении информации о терминалах.</b> Пожалуйста, попробуйте позже.",
        "show_on_map": "🗺️ Показать на карте",
        "back": "⬅️ Назад",
        "location_received": "Локация получена!",
        "live_location_received": "Живая локация получена! Спасибо.",
    },
}


# Create keyboard with language options
def get_language_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang)] for lang in LANGUAGES.keys()],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


# Create keyboard with button to request phone number
def get_phone_keyboard(language_code):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=TRANSLATIONS[language_code]["share_phone_button"],
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


# Create localized register button
def get_register_inline_keyboard(language):
    if language == "ru":
        text = "Регистрация"
    else:
        text = "Registratsiya"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data="register:start")]
        ]
    )


# Create phone keyboard
def get_contact_keyboard(language):
    text = "Telefon raqamni ulashish" if language == "uz" else "Поделиться номером"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@user_router.message(CommandStart())
async def user_start(message: Message, state: FSMContext, api_client, language):
    api = api_client or MyApi()
    try:
        login_result = await api.telegram_login(message.from_user.id)
        lang = login_result.get("language", language)
        await message.answer(
            (TRANSLATIONS[lang]["welcome_back"]).format(message.from_user.full_name),
            reply_markup=simple_menu_keyboard(lang),
            parse_mode="HTML",
        )
    except aiohttp.ClientError as e:
        status = getattr(e, "status", None)
        if status == 404:
            language_code = (
                message.from_user.language_code
                if message.from_user.language_code in ["uz", "ru"]
                else language
            )
            await message.answer(
                "Registratsiyadan o`tishni istaysizmi ?",
                reply_markup=get_register_inline_keyboard(language_code),
                parse_mode="HTML",
            )
        elif status == 401:
            await message.reply("⛔ Bot authorization failed. Please contact admin.")
        else:
            await message.reply("⚠️ Server error. Please try again later.")


@user_router.callback_query(lambda c: c.data == "register:start")
async def register_start_callback(
    callback_query: CallbackQuery, state: FSMContext, api_client, language
):
    await state.clear()
    await state.set_state(RegistrationWizard.waiting_for_language)
    await callback_query.message.answer(
        (TRANSLATIONS[language]["select_language"]),
        reply_markup=get_language_keyboard(),
        parse_mode="HTML",
    )
    await callback_query.answer()


@user_router.message(Command("register"))
async def register_command(message: Message, state: FSMContext, api_client, language):
    await state.clear()
    await state.set_state(RegistrationWizard.waiting_for_language)
    await message.answer(
        TRANSLATIONS[language]["select_language"],
        reply_markup=get_language_keyboard(),
        parse_mode="HTML",
    )


@user_router.message(RegistrationWizard.waiting_for_language)
async def reg_process_language(
    message: Message, state: FSMContext, api_client, language
):
    lang = None
    for k, v in LANGUAGES.items():
        if k in message.text or v in message.text.lower():
            lang = v
            break
    if lang is None:
        await message.reply(
            "Iltimos, klaviaturadan tilni tanlang.\nПожалуйста, выберите язык с клавиатуры.",
            reply_markup=get_language_keyboard(),
            parse_mode="HTML",
        )
        return
    await state.update_data(language=lang)
    await state.set_state(RegistrationWizard.waiting_for_phone)
    await message.answer(
        TRANSLATIONS[lang]["share_phone"],
        reply_markup=get_phone_keyboard(lang),
        parse_mode="HTML",
    )


@user_router.message(RegistrationWizard.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext, api_client, language):
    contact = message.contact
    if not contact or not contact.phone_number:
        await message.reply(
            TRANSLATIONS[language]["use_button"],
            reply_markup=get_phone_keyboard(language),
        )
        return
    await state.update_data(phone_number=contact.phone_number)
    await state.set_state(RegistrationWizard.waiting_for_first_name)
    summary = f"<b>📱 {contact.phone_number}</b>"
    await message.answer(
        summary
        + "\n\n"
        + ("Ismingizni kiriting:" if language == "uz" else "Введите ваше имя:"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[]], resize_keyboard=True, one_time_keyboard=True
        ),
        parse_mode="HTML",
    )


@user_router.message(RegistrationWizard.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext, api_client, language):
    first_name = message.text.strip()
    if not first_name:
        await message.reply(
            "Ismingizni kiriting:" if language == "uz" else "Введите ваше имя:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[]], resize_keyboard=True, one_time_keyboard=True
            ),
        )
        return
    await state.update_data(first_name=first_name)
    await state.set_state(RegistrationWizard.waiting_for_last_name)
    summary = f"<b>📱 {message.contact.phone_number}</b>\n<b>👤 {first_name}</b>"
    await message.answer(
        summary
        + "\n\n"
        + ("Familiyangizni kiriting:" if language == "uz" else "Введите вашу фамилию:"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[]], resize_keyboard=True, one_time_keyboard=True
        ),
        parse_mode="HTML",
    )


@user_router.message(RegistrationWizard.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext, api_client, language):
    last_name = message.text.strip()
    if not last_name:
        await message.reply(
            "Familiyangizni kiriting:" if language == "uz" else "Введите вашу фамилию:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[]], resize_keyboard=True, one_time_keyboard=True
            ),
        )
        return
    await state.update_data(last_name=last_name)
    await state.set_state(RegistrationWizard.waiting_for_truck_number)
    summary = (
        f"<b>📱 {message.contact.phone_number}</b>\n<b>👤 {message.text.strip()}</b>"
    )
    await message.answer(
        summary
        + "\n\n"
        + (
            "Yuk mashina raqamini kiriting:"
            if language == "uz"
            else "Введите номер грузовика:"
        ),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[]], resize_keyboard=True, one_time_keyboard=True
        ),
        parse_mode="HTML",
    )


@user_router.message(RegistrationWizard.waiting_for_truck_number)
async def process_truck_number(
    message: Message, state: FSMContext, api_client, language
):
    truck_number = message.text.strip()
    await state.update_data(truck_number=truck_number)
    data = await state.get_data()
    registration_data = {
        "telegram_id": message.from_user.id,
        "phone_number": data.get("phone_number", ""),
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
        "role": "driver",
        "language": language,
        "truck_number": truck_number,
    }
    try:
        api = api_client or MyApi()
        await api.telegram_auth(**registration_data)
        summary = (
            f"<b>📱 {data.get('phone_number', '')}</b>\n"
            f"<b>👤 {data.get('first_name', '')} {data.get('last_name', '')}</b>\n"
            f"<b>🚚 {truck_number}</b>"
        )
        await message.answer(
            TRANSLATIONS[language]["registration_success"].format(
                data.get("first_name", "")
            ),
            reply_markup=simple_menu_keyboard(language),
            parse_mode="HTML",
        )
        await state.clear()
    except Exception as e:
        await message.answer(
            TRANSLATIONS[language]["registration_failed"].format(str(e)),
            parse_mode="HTML",
        )


@user_router.message(Location())
async def handle_location(message: Message, state: FSMContext, api_client, language):
    loc = message.location
    if loc:
        is_live = loc.live_period is not None
        if is_live:
            await message.reply(TRANSLATIONS[language]["live_location_received"])
        else:
            await message.reply(TRANSLATIONS[language]["location_received"])
        # Optionally: save or forward the location to your backend here
