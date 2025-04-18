from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from infrastructure.some_api.api import MyApi
from tgbot.filters.admin import AdminFilter
from tgbot.keyboards.reply import REPLY_TRANSLATIONS, simple_menu_keyboard

support_router = Router()


# Define states for support requests
class SupportStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_admin_reply = State()


# Translations for support messages
SUPPORT_TRANSLATIONS = {
    "uz": {
        "ask_question": "<b>Savolingizni yoki muammoingizni kiriting.</b> Biz imkon qadar tezroq javob berishga harakat qilamiz.",
        "question_received": "✅ <b>Savolingiz qabul qilindi!</b> Tez orada javob olasiz.",
        "no_active_requests": "❌ <b>Hozirda faol so'rovlar yo'q.</b>",
        "support_requests": "📬 <b>Qo'llab-quvvatlash so'rovlari:</b>",
        "from_user": "👤 <b>Foydalanuvchi:</b> {}",
        "question": "❓ <b>Savol:</b> {}",
        "reply_button": "↩️ Javob berish",
        "enter_reply": "<b>Foydalanuvchiga javobingizni kiriting:</b>",
        "reply_sent": "✅ <b>Javobingiz foydalanuvchiga yuborildi!</b>",
        "new_reply": "📨 <b>Qo'llab-quvvatlashdan yangi xabar:</b>\n\n{}",
        "cancel": "❌ Bekor qilish",
    },
    "ru": {
        "ask_question": "<b>Введите ваш вопрос или опишите проблему.</b> Мы постараемся ответить как можно скорее.",
        "question_received": "✅ <b>Ваш вопрос получен!</b> Вы получите ответ в ближайшее время.",
        "no_active_requests": "❌ <b>В настоящее время нет активных запросов.</b>",
        "support_requests": "📬 <b>Запросы в поддержку:</b>",
        "from_user": "👤 <b>Пользователь:</b> {}",
        "question": "❓ <b>Вопрос:</b> {}",
        "reply_button": "↩️ Ответить",
        "enter_reply": "<b>Введите ваш ответ пользователю:</b>",
        "reply_sent": "✅ <b>Ваш ответ отправлен пользователю!</b>",
        "new_reply": "📨 <b>Новое сообщение от поддержки:</b>\n\n{}",
        "cancel": "❌ Отмена",
    },
}


@support_router.message(F.text.in_(["Qo'llab-quvvatlash", "Поддержка"]))
async def start_support_request(message: Message, state: FSMContext):
    """
    Start the support request process.
    """
    # Get user language
    user_data = await state.get_data()
    language_code = user_data.get("language", "ru")  # Default to Russian if not set

    # Set state to waiting for question
    await state.set_state(SupportStates.waiting_for_question)

    # Create cancel button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=SUPPORT_TRANSLATIONS[language_code]["cancel"],
                    callback_data="support:cancel",
                )
            ]
        ]
    )

    # Ask for the question
    await message.reply(
        SUPPORT_TRANSLATIONS[language_code]["ask_question"],
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@support_router.callback_query(F.data == "support:cancel")
async def cancel_support_request(callback: CallbackQuery, state: FSMContext):
    """
    Cancel the support request process.
    """
    await callback.answer()

    # Get user language
    user_data = await state.get_data()
    language_code = user_data.get("language", "ru")

    # Clear the state
    await state.clear()

    # Return to main menu
    await callback.message.edit_text(
        SUPPORT_TRANSLATIONS[language_code]["ask_question"] + "\n\n❌ <b>Отменено</b>",
        parse_mode="HTML",
    )

    # Show main menu
    await callback.message.answer(
        "👋",
        reply_markup=simple_menu_keyboard(language_code),
    )


@support_router.message(SupportStates.waiting_for_question)
async def process_support_question(message: Message, state: FSMContext, api_client=None):
    """
    Process the support question and notify admins.
    """
    # Get user data
    user_data = await state.get_data()
    language_code = user_data.get("language", "ru")
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = user_data.get("first_name", message.from_user.first_name or "")
    question = message.text

    # Store the question in state or database
    # For simplicity, we'll use the API to store the support request
    try:
        # Use the shared API client from middleware instead of creating a new one
        api = api_client or MyApi()
        await api.create_support_request(
            user_id=user_id,
            username=username,
            first_name=first_name,
            question=question,
            language_code=language_code,
        )
    except Exception as e:
        print(f"Error creating support request: {e}")

    # Clear the state
    await state.clear()

    # Confirm receipt of question
    await message.reply(
        SUPPORT_TRANSLATIONS[language_code]["question_received"],
        reply_markup=simple_menu_keyboard(language_code),
        parse_mode="HTML",
    )

    # Notify admins about the new support request
    # This would typically be done by fetching admin IDs from a database
    # For simplicity, we'll use a hardcoded admin ID (you should replace this)
    admin_ids = [5331201165]  # Replace with actual admin IDs

    for admin_id in admin_ids:
        # Create reply button for admin
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=SUPPORT_TRANSLATIONS["ru"]["reply_button"],
                        callback_data=f"support:reply:{user_id}",
                    )
                ]
            ]
        )

        # Format message for admin
        admin_message = (
            f"{SUPPORT_TRANSLATIONS['ru']['support_requests']}\n\n"
            f"{SUPPORT_TRANSLATIONS['ru']['from_user'].format(first_name)} (@{username})\n"
            f"{SUPPORT_TRANSLATIONS['ru']['question'].format(question)}"
        )

        try:
            # Send notification to admin
            await message.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as e:
            print(f"Error notifying admin {admin_id}: {e}")


# Admin handlers for responding to support requests
@support_router.callback_query(F.data.startswith("support:reply:"))
async def admin_reply_to_support(callback: CallbackQuery, state: FSMContext):
    """
    Handle admin's request to reply to a support question.
    """
    await callback.answer()

    # Extract user ID from callback data
    user_id = callback.data.split(":")[2]

    # Store user ID in state for later use
    await state.update_data(reply_to_user_id=user_id)
    await state.set_state(SupportStates.waiting_for_admin_reply)

    # Create cancel button
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=SUPPORT_TRANSLATIONS["ru"]["cancel"],
                    callback_data="support:cancel_reply",
                )
            ]
        ]
    )

    # Prompt admin for reply
    await callback.message.reply(
        SUPPORT_TRANSLATIONS["ru"]["enter_reply"],
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@support_router.callback_query(
    SupportStates.waiting_for_admin_reply, F.data == "support:cancel_reply"
)
async def cancel_admin_reply(callback: CallbackQuery, state: FSMContext):
    """
    Cancel the admin reply process.
    """
    await callback.answer()

    # Clear the state
    await state.clear()

    # Confirm cancellation
    await callback.message.edit_text(
        SUPPORT_TRANSLATIONS["ru"]["enter_reply"] + "\n\n❌ <b>Отменено</b>",
        parse_mode="HTML",
    )


@support_router.message(SupportStates.waiting_for_admin_reply)
async def process_admin_reply(message: Message, state: FSMContext):
    """
    Process admin's reply to a support question and send it to the user.
    """
    # Get the user ID to reply to
    user_data = await state.get_data()
    user_id = user_data.get("reply_to_user_id")

    if not user_id:
        await message.reply("Error: User ID not found.")
        await state.clear()
        return

    reply_text = message.text

    try:
        # Send the reply to the user
        await message.bot.send_message(
            chat_id=int(user_id),
            text=SUPPORT_TRANSLATIONS["ru"]["new_reply"].format(reply_text),
            parse_mode="HTML",
        )

        # Confirm to admin that reply was sent
        await message.reply(
            SUPPORT_TRANSLATIONS["ru"]["reply_sent"],
            parse_mode="HTML",
        )
    except Exception as e:
        await message.reply(f"Error sending reply: {e}")

    # Clear the state
    await state.clear()


# Command for admins to view active support requests
@support_router.message(F.text == "/support_requests", AdminFilter())
async def list_support_requests(message: Message, api_client=None):
    """
    List all active support requests for admin.
    """
    try:
        # Fetch support requests from API or database
        # Use the shared API client from middleware instead of creating a new one
        api = api_client or MyApi()
        requests = await api.get_support_requests()

        if not requests:
            await message.reply(
                SUPPORT_TRANSLATIONS["ru"]["no_active_requests"],
                parse_mode="HTML",
            )
            return

        # Send each request to admin
        for req in requests:
            user_id = req.get("user_id")
            username = req.get("username", "")
            first_name = req.get("first_name", "")
            question = req.get("question", "")

            # Create reply button
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=SUPPORT_TRANSLATIONS["ru"]["reply_button"],
                            callback_data=f"support:reply:{user_id}",
                        )
                    ]
                ]
            )

            # Format message
            admin_message = (
                f"{SUPPORT_TRANSLATIONS['ru']['from_user'].format(first_name)} (@{username})\n"
                f"{SUPPORT_TRANSLATIONS['ru']['question'].format(question)}"
            )

            await message.reply(
                admin_message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
    except Exception as e:
        await message.reply(f"Error fetching support requests: {e}")
