import asyncio
import logging
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from infrastructure.some_api.api import MyApi

logger = logging.getLogger(__name__)
location_router = Router()


async def process_location(message: Message, state: FSMContext, is_edit: bool = False):
    location = message.location
    latitude = location.latitude
    longitude = location.longitude
    horizontal_accuracy = getattr(location, "horizontal_accuracy", None)
    live_period = getattr(location, "live_period", None)

    current_data = await state.get_data()
    live_active = current_data.get("live_location_active", False)

    if not live_period:
        if live_active:
            await state.update_data(live_location_active=False)
            logger.info(
                f"[TRACKING] Live location stopped by user {message.from_user.id}"
            )
            return
        else:
            await message.answer(
                "❗️ Bu oddiy pin. 📍 Iltimos, 'Jonli joylashuv ulashish' ni tanlang.",
                parse_mode="HTML",
            )
            logger.warning(
                f"[TRACKING] Static location received from {message.from_user.id}"
            )
            return

    # Update FSM data
    await state.update_data(
        latitude=latitude,
        longitude=longitude,
        live_location_active=True,
        live_location_last_updated=datetime.now(timezone.utc),
        reminder_active=False,  # Disable old reminder (important!)
    )

    payload = {
        "telegram_id": message.from_user.id,
        "latitude": latitude,
        "longitude": longitude,
    }
    if horizontal_accuracy is not None:
        payload["horizontal_accuracy"] = horizontal_accuracy

    try:
        api_client = MyApi()
        try:
            await api_client.post_location(payload)

            log_prefix = "[TRACKING][EDIT]" if is_edit else "[TRACKING]"
            logger.info(
                f"{log_prefix} Live location updated: lat={latitude}, lon={longitude}, accuracy={horizontal_accuracy}"
            )

            # Mark reminder as active after new task starts
            await state.update_data(reminder_active=True)
        finally:
            # Ensure the API client is properly closed
            await api_client.close()

    except Exception as e:
        logger.error(f"[TRACKING] Error posting location: {str(e)}")
        await message.reply(
            f"❗️ Error sending location to server: {str(e)}",
            parse_mode="HTML",
        )


@location_router.message(F.location)
async def track_location(message: Message, state: FSMContext):
    await process_location(message, state, is_edit=False)


@location_router.edited_message(F.location)
async def track_location_update(message: Message, state: FSMContext):
    await process_location(message, state, is_edit=True)
