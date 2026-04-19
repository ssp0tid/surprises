from typing import Any, Dict, List

import httpx


class GeocodingClient:
    """Async client for Open-Meteo geocoding API."""

    BASE_URL = "https://geocoding-api.open-meteo.com/v1/search"

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self.client.aclose()

    async def search(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """
        Search for locations by name.

        Args:
            query: Location name to search for
            count: Maximum number of results to return (default: 10)

        Returns:
            List of location results with name, lat, lon, country, etc.
        """
        params = {"name": query, "count": count, "language": "en", "format": "json"}

        response = await self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    async def __aenter__(self) -> "GeocodingClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
