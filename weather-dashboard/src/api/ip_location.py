from typing import Any, Dict

import httpx


class IPLocationClient:
    """Async client for IP-based location detection."""

    BASE_URL = "http://ip-api.com/json/"

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self.client.aclose()

    async def get_location(self) -> Dict[str, Any]:
        """
        Detect user's location based on their IP address.

        Returns:
            Dictionary containing lat, lon, city, country, etc.
        """
        response = await self.client.get(self.BASE_URL)
        response.raise_for_status()
        return response.json()

    async def __aenter__(self) -> "IPLocationClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
