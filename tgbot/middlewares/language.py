from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class LanguageMiddleware(BaseMiddleware):
    """Middleware to inject user's preferred language into handler data."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Attempt to get api_client and user id
        api_client = data.get("api_client")
        user_id = None
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        # Default to Uzbek
        language = "uz"
        if api_client and user_id:
            try:
                profile = await api_client.get_user_profile(user_id)
                language = profile.get("preferred_language", language)
            except Exception:
                pass
        data["language"] = language
        data["truck_number"] = profile.get("truck_number", "")
        return await handler(event, data)
