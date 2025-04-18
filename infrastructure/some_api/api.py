import base64
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import backoff

from infrastructure.some_api.base import BaseClient


class MyApi(BaseClient):
    """API client for interacting with the backend service."""

    def __init__(self, base_url: str = "https://khamraev.uz"):
        """Initialize API client with base URL.

        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url
        self.bot_secret = "1234!@qwwqdsgfgh!@!2922U948U"
        self.logger = logging.getLogger(__name__)
        super().__init__(base_url=self.base_url)

    async def telegram_auth(
        self,
        telegram_id: int,
        phone_number: str,
        first_name: str = "",
        last_name: str = "",
        role: str = "driver",
        language: str = "uz",
        truck_number: str = "",
    ) -> Dict[str, Any]:
        """Register or authenticate a user via Telegram ID and phone number.

        Args:
            telegram_id: User's Telegram ID
            phone_number: User's phone number
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            role: User's role (default: "driver")
            language: User's preferred language (default: "uz")
            truck_number: User's truck number (optional)

        Returns:
            Dict containing JWT tokens for authentication
        """
        _, result = await self._make_request(
            method="POST",
            url="/api/users/telegram-auth/",
            json={
                "telegram_id": telegram_id,
                "phone_number": phone_number,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "preferred_language": language,  # Keep the API field name as is
                "truck_number": truck_number,
                "bot_secret": self.bot_secret,
            },
        )

        return result

    async def create_route(
        self,
        truck_number: str,
        start_location: str,
        terminal_id: int,
        container_name: str,
        container_size: str,
        container_type: str,
        eta: str,
        telegram_id: int,
    ) -> Dict[str, Any]:
        """Create a new route.

        Args:
            truck_number: Truck number
            start_location: Starting location
            terminal_id: Terminal ID
            container_name: Container name
            container_size: Container size
            container_type: Container type (laden or empty)
            eta: Estimated time of arrival
            access_token: JWT access token
            telegram_id: User's Telegram ID

        Returns:
            API response data
        """

        data = {
            "truck_number": truck_number,
            "start_location": start_location,
            "terminal_id": terminal_id,
            "container_name": container_name,
            "container_size": container_size,
            "container_type": container_type,
            "eta": eta,
            "telegram_id": telegram_id,
            "bot_secret": self.bot_secret,
        }

        # Use the base _make_request method for consistency
        _, result = await self._make_request(
            method="POST",
            url="/api/routes/telegram_create/",
            json=data,
        )

        return result

    async def telegram_login(
        self,
        telegram_id: int,
    ) -> Dict[str, Any]:
        """Obtain access JWT using telegram_id and bot_secret.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            Dict containing access token or error message
        """
        payload = {"telegram_id": telegram_id, "bot_secret": self.bot_secret}
        _, result = await self._make_request(
            method="POST",
            url="/api/users/telegram-login/",
            json=payload,
        )
        return result

    async def get_user_profile(self, telegram_id: int) -> Dict[str, Any]:
        """Get the authenticated user's profile information.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            Dict containing user profile fields
        """
        _, result = await self._make_request(
            method="POST",
            url="/api/users/telegram-profile/",
            json={"telegram_id": telegram_id, "bot_secret": self.bot_secret},
        )
        return result

    async def get_terminals(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get list of terminals using telegram_id and bot_secret."""
        payload = {"telegram_id": telegram_id, "bot_secret": self.bot_secret}
        _, result = await self._make_request(
            method="POST",
            url="/api/terminals/list-via-telegram/",
            json=payload,
        )
        return result

    async def get_terminal(self, terminal_id: int, telegram_id: int) -> Dict[str, Any]:
        """Get details of a specific terminal using terminal_id and bot_secret."""
        payload = {"telegram_id": telegram_id, "bot_secret": self.bot_secret}
        _, result = await self._make_request(
            method="POST",
            url=f"/api/terminals/detail-via-telegram/{terminal_id}/",
            json=payload,
        )
        return result

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientError,
        max_time=20,
        giveup=lambda e: hasattr(e, "status") and e.status in [400, 401, 403, 404],
    )
    async def _make_request(
        self, method: str, url: str, **kwargs
    ) -> Tuple[int, Union[Dict[str, Any], str]]:
        """Make API request with proper error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: API endpoint URL
            **kwargs: Additional arguments to pass to the request

        Returns:
            Tuple of (status_code, response_data)

        Raises:
            aiohttp.ClientError: On request failure
        """
        session = await self._get_session()

        async with session.request(method, url, **kwargs) as response:
            try:
                if response.content_type == "application/json":
                    data = await response.json()
                else:
                    data = await response.text()

                self.logger.debug(f"Response data: {data}")

                # Treat 201 as success
                if response.status in [200, 201]:
                    return response.status, data

                # For error status codes, raise an exception with status attribute
                error = aiohttp.ClientError(f"Got status {response.status}")
                setattr(error, "status", response.status)
                raise error

            except aiohttp.ClientError as e:
                # Add status attribute if not present
                if not hasattr(e, "status"):
                    setattr(e, "status", response.status)
                raise
