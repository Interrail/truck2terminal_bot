from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class LanguageMiddleware(BaseMiddleware):
    """Middleware to inject user's preferred language into handler data."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Default values
        language = "uz"
        truck_number = ""

        # Attempt to get api_client and user id
        api_client = data.get("api_client")
        user_id = None

        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id

            # Only try to get profile if we have both api_client and user_id
            if api_client and user_id:
                try:
                    profile = await api_client.get_user_profile(user_id)
                    language = profile.get("preferred_language", language)
                    truck_number = profile.get("truck_number", "")
                except Exception:
                    pass

        # Set data values regardless of whether we found a user or not
        data["language"] = language
        data["truck_number"] = truck_number
        return await handler(event, data)
