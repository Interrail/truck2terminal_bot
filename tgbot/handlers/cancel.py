from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

cancel_router = Router()


CANCEL_TRANSLATIONS = {
    "uz": {
        "no_active_actions": "❌ Hozir sizda faol harakatlar yo'q.",
        "process_canceled": "✅ Jarayon bekor qilindi. Istalgan vaqtda qayta boshlashingiz mumkin!",
    },
    "ru": {
        "no_active_actions": "❌ У вас сейчас нет активных действий.",
        "process_canceled": "✅ Процесс отменен. Вы можете начать снова в любое время!",
    },
}


@cancel_router.message(F.data == "cancel")
async def cancel_handler(message: Message, state: FSMContext, language: str = "uz"):
    current_state = await state.get_state()

    # Default to Uzbek if language not provided or not supported
    if language not in CANCEL_TRANSLATIONS:
        language = "uz"

    if current_state is None:
        await message.answer(CANCEL_TRANSLATIONS[language]["no_active_actions"])
        return

    await state.clear()
    await message.answer(CANCEL_TRANSLATIONS[language]["process_canceled"])
