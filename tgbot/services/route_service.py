from typing import Any, Dict, Optional

from infrastructure.some_api.api import MyApi

# Keep this for backward compatibility during transition
TERMINALS = {"ULS": 1, "FTT": 2, "MTT": 3}


class RouteService:
    """Service for handling route-related operations."""

    def __init__(self, api_client=None):
        # Use the provided API client or create a new one if none is provided
        self.api = api_client or MyApi()
        self._terminals_cache = None

    async def get_terminals(self, telegram_id: int) -> Dict[str, int]:
        """
        Get terminals from API and return as a dictionary of name:id pairs.

        Args:
            telegram_id: User's Telegram ID

        Returns:
            Dictionary with terminal names as keys and IDs as values
        """
        try:
            # Fetch terminals from API
            terminals_data = await self.api.get_terminals(telegram_id)

            # Convert to name:id dictionary
            terminals_dict = {}
            for terminal in terminals_data:
                # Assuming the API returns objects with 'id' and 'name' fields
                terminals_dict[terminal["name"]] = terminal["id"]

            # Cache the result
            self._terminals_cache = terminals_dict
            return terminals_dict
        except Exception as e:
            # If API fails, fall back to hardcoded terminals
            print(f"Error fetching terminals: {str(e)}")
            return TERMINALS

    async def get_recent_trucks(self, telegram_id: int, limit: int = 3) -> list:
        """
        Get recent truck numbers used by this driver.
        
        Args:
            telegram_id: User's Telegram ID
            limit: Maximum number of recent trucks to return
            
        Returns:
            List of recent truck numbers as strings
        """
        try:
            # Try to get recent trucks from API
            recent_trucks = await self.api.get_recent_trucks(telegram_id, limit)
            return recent_trucks
        except Exception as e:
            # If API call fails, return empty list
            print(f"Error fetching recent trucks: {str(e)}")
            return []
            
    async def get_recent_back_numbers(self, telegram_id: int, front_number: str, limit: int = 3) -> list:
        """
        Get recent back numbers used with a specific front number.
        
        Args:
            telegram_id: User's Telegram ID
            front_number: Front part of the truck number
            limit: Maximum number of recent back numbers to return
            
        Returns:
            List of recent back numbers as strings
        """
        try:
            # Try to get recent back numbers from API
            recent_back_numbers = await self.api.get_recent_back_numbers(
                telegram_id, front_number, limit
            )
            return recent_back_numbers
        except Exception as e:
            # If API call fails, return empty list
            print(f"Error fetching recent back numbers: {str(e)}")
            return []

    async def validate_terminal(self, terminal_name: str) -> int:
        """
        Validate terminal name and return its ID.

        Args:
            terminal_name: Name of the terminal
            access_token: Optional JWT access token to refresh terminals

        Returns:
            Terminal ID

        Raises:
            ValueError: If terminal name is invalid
        """
        # Check in cache first
        if self._terminals_cache and terminal_name in self._terminals_cache:
            return self._terminals_cache[terminal_name]

        # Fall back to hardcoded terminals
        if terminal_name in TERMINALS:
            return TERMINALS[terminal_name]

        raise ValueError(f"Invalid terminal: {terminal_name}")

    @staticmethod
    def validate_container_size(size: str) -> str:
        """Validate container size."""
        valid_sizes = ["20", "40", "45"]
        if size in valid_sizes:
            return size
        raise ValueError(f"Invalid container size: {size}")

    @staticmethod
    def validate_container_type(container_type: str) -> str:
        """Validate container type."""
        valid_types = ["laden", "empty"]
        if container_type in valid_types:
            return container_type
        raise ValueError(f"Invalid container type: {container_type}")

    async def get_terminal_name_by_id(
        self, terminal_id: int, access_token: Optional[str] = None
    ) -> str:
        """
        Get terminal name by its ID.

        Args:
            terminal_id: Terminal ID
            access_token: Optional JWT access token to refresh terminals

        Returns:
            Terminal name or "Unknown Terminal" if not found
        """
        # If we have a token, try to refresh terminals
        if access_token and not self._terminals_cache:
            await self.get_terminals(access_token)

        # Check in cache first
        if self._terminals_cache:
            for name, id_ in self._terminals_cache.items():
                if id_ == terminal_id:
                    return name

        # Fall back to hardcoded terminals
        for name, id_ in TERMINALS.items():
            if id_ == terminal_id:
                return name

        return "Unknown Terminal"

    async def create_route(
        self,
        truck_number: str,
        terminal: str,
        container_name: str,
        container_size: str,
        container_type: str,
        eta: str,
        telegram_id: int,
    ) -> Dict[str, Any]:
        """Create a new route using the API."""
        try:
            # Validate inputs
            terminal_id = await self.validate_terminal(
                terminal,
            )
            self.validate_container_size(container_size)
            self.validate_container_type(container_type)

            # Call API to create route
            result = await self.api.create_route(
                truck_number=truck_number,
                terminal_id=terminal_id,
                container_name=container_name,
                container_size=container_size,
                container_type=container_type,
                eta=eta,
                telegram_id=telegram_id,
            )

            return result
        except Exception as e:
            # Log the error
            print(f"Error creating route: {str(e)}")
            return {"success": False, "message": str(e)}
