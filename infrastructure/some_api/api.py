import aiohttp
import backoff

from infrastructure.some_api.base import BaseClient


class MyApi(BaseClient):
    def __init__(self, api_key: str, base_url: str = "https://khamraev.uz"):
        self.api_key = api_key
        self.base_url = base_url
        super().__init__(base_url=self.base_url)

    async def get_something(self, *args, **kwargs):
        # await self._make_request(
        #     ...
        # )
        result = {"id": 1, "name": "test"}
        return result

    async def telegram_auth(
        self,
        telegram_id: int,
        phone_number: str,
        first_name: str = "",
        last_name: str = "",
        role: str = "driver",
    ):
        """
        Register or authenticate a user via Telegram ID and phone number.
        Returns JWT tokens for authentication.
        """
        status, result = await self._make_request(
            method="POST",
            url="/api/users/telegram_auth/",
            json={
                "telegram_id": telegram_id,
                "phone_number": phone_number,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
            },
        )

        return result

    async def create_route(
        self,
        driver_id: int,
        truck_number: str,
        terminal_id: int,
        container_name: str,
        container_size: str,
        container_type: str,
        start_location: str,
        access_token: str,
    ):
        """
        Create a new route with the given parameters.
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            status, result = await self._make_request(
                method="POST",
                url="/api/routes/telegram_create/",
                json={
                    "telegram_id": driver_id,
                    "truck_number": truck_number,
                    "terminal_id": terminal_id,
                    "container_name": container_name,
                    "container_size": container_size,
                    "container_type": container_type,
                    "start_location": start_location,
                },
                headers=headers,
            )
            # The base client might treat 201 as an error, but we know it's a success
            # So we'll handle it explicitly here
            return status, result
        except aiohttp.ClientError as e:
            # Log the error but don't retry
            print(f"Error creating route: {e}")
            return 500, {"error": str(e)}

    # Override the _make_request method from BaseClient
    # to properly handle 201 responses
    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientError,
        max_time=60,
        giveup=lambda e: hasattr(e, "status") and e.status in [201, 400, 401, 403, 404],
    )
    async def _make_request(self, method, url, **kwargs):
        """Override to properly handle 201 responses."""
        session = await self._get_session()

        async with session.request(method, url, **kwargs) as response:
            try:
                if response.content_type == "application/json":
                    data = await response.json()
                else:
                    data = await response.text()

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
