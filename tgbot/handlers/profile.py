from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from infrastructure.some_api.api import MyApi
from tgbot.keyboards.reply import REPLY_TRANSLATIONS, simple_menu_keyboard

profile_router = Router()


@profile_router.message(
    lambda msg: msg.text
    in [
        REPLY_TRANSLATIONS["uz"]["my_profile"],
        REPLY_TRANSLATIONS["ru"]["my_profile"],
    ]
)
async def show_my_profile(message: Message, state: FSMContext, api_client=None):
    """
    Handler to show user's profile info when 'my_profile' button is pressed.
    """

    print("Fetching user profile...")
    # Use the shared API client from middleware instead of creating a new one
    api = api_client or MyApi()
    try:
        profile = await api.get_user_profile(message.from_user.id)
        lang = profile.get("preferred_language", "ru")
        # Format profile info
        if lang == "uz":
            profile_msg = (
                f"<b>👤 Ismingiz:</b> {profile.get('first_name', '')}\n"
                f"<b>👥 Familiyangiz:</b> {profile.get('last_name', '')}\n"
                f"<b>📱 Telefon:</b> {profile.get('phone_number', '')}\n"
                f"<b>🚚 Yuk mashina raqami:</b> {profile.get('truck_number', '')}\n"
                f"<b>🌐 Til:</b> {profile.get('preferred_language', '')}\n"
            )
        else:
            profile_msg = (
                f"<b>👤 Имя:</b> {profile.get('first_name', '')}\n"
                f"<b>👥 Фамилия:</b> {profile.get('last_name', '')}\n"
                f"<b>📱 Телефон:</b> {profile.get('phone_number', '')}\n"
                f"<b>🚚 Номер грузовика:</b> {profile.get('truck_number', '')}\n"
                f"<b>🌐 Язык:</b> {profile.get('preferred_language', '')}\n"
            )
        await message.answer(
            profile_msg, parse_mode="HTML", reply_markup=simple_menu_keyboard(lang)
        )
    except Exception:
        await message.answer(
            "Profil ma'lumotlarini olishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
            if lang == "uz"
            else "Произошла ошибка при получении профиля. Пожалуйста, попробуйте еще раз.",
            reply_markup=simple_menu_keyboard(lang if "lang" in locals() else "ru"),
        )
