import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.types import Message


async def auto_cancel_after_timeout(
    message: Message, state: FSMContext, timeout_seconds: int = 300
):
    """
    Automatically cancels the current FSM state after a timeout if the user is inactive.

    Args:
        message: aiogram Message object
        state: FSMContext for current user
        timeout_seconds: How many seconds to wait before auto-cancel (default: 5 minutes)
    """
    await asyncio.sleep(timeout_seconds)

    current_state = await state.get_state()
    if current_state:  # if driver still stuck in a state
        await state.clear()
        await message.answer(
            "⌛️ 5 daqiqa davomida hech qanday faoliyat kuzatilmadi.\n✅ Jarayon avtomatik ravishda bekor qilindi.\n\n/start"
        )



