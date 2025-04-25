import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from infrastructure.some_api.api import MyApi
from tgbot.handlers.route import ROUTE_TRANSLATIONS

logger = logging.getLogger(__name__)

# Create a separate router for location tracking
location_router = Router()


@location_router.message(F.location)
async def track_location(message: Message, state: FSMContext):
    """
    Handle ALL location messages.
    If route_id is present in state, send coordinates to backend and reply with route info.
    """
    data = await state.get_data()
    route_id = data.get("route_id")
    location = message.location
    latitude = location.latitude
    longitude = location.longitude
    horizontal_accuracy = getattr(location, "horizontal_accuracy", None)

    # Always save latitude and longitude in FSM state
    await state.update_data(latitude=latitude, longitude=longitude)

    logger.info(
        f"[TRACKING] Received location: lat={latitude}, lon={longitude}, accuracy={horizontal_accuracy}"
    )

    if route_id:
        payload = {
            "route_id": route_id,
            "latitude": latitude,
            "longitude": longitude,
        }
        if horizontal_accuracy is not None:
            payload["horizontal_accuracy"] = horizontal_accuracy
        try:
            api_client = MyApi()
            await api_client.post_location(payload)

        except Exception as e:
            logger.error(f"[TRACKING] Error sending location: {str(e)}")
            await message.reply(
                f"Error sending location to route {route_id}: {str(e)}",
                parse_mode="HTML",
            )


@location_router.edited_message(F.location)
async def track_location_update(message: Message, state: FSMContext):
    """
    Handle ALL live location updates (edited_message events).
    If route_id is present in state, send coordinates to backend and reply with route info.
    """
    data = await state.get_data()
    route_id = data.get("route_id")

    location = message.location
    latitude = location.latitude
    longitude = location.longitude
    horizontal_accuracy = getattr(location, "horizontal_accuracy", None)

    # Always save latitude and longitude in FSM state
    await state.update_data(latitude=latitude, longitude=longitude)

    logger.info(
        f"[TRACKING][EDIT] Updated location: lat={latitude}, lon={longitude}, accuracy={horizontal_accuracy}"
    )

    if route_id:
        payload = {
            "route_id": route_id,
            "latitude": latitude,
            "longitude": longitude,
        }
        if horizontal_accuracy is not None:
            payload["horizontal_accuracy"] = horizontal_accuracy
        try:
            api_client = MyApi()
            await api_client.post_location(payload)

        except Exception as e:
            logger.error(f"[TRACKING][EDIT] Error sending location: {str(e)}")
