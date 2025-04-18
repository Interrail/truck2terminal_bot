from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class ApiMiddleware(BaseMiddleware):
    """Middleware for passing API client to handlers."""

    def __init__(self, api_client):
        self.api_client = api_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Add API client to data which will be passed to handler
        data["api_client"] = self.api_client
        # Call next handler
        return await handler(event, data)
