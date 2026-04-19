import httpx
from typing import Any, Dict


class WeatherAPIClient:
    """Async client for Open-Meteo weather API."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self.client.aclose()

    async def get_weather(
        self, latitude: float, longitude: float, timezone: str = "auto"
    ) -> Dict[str, Any]:
        """
        Fetch weather data for given coordinates.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            timezone: Timezone for weather data (default: "auto")

        Returns:
            Dictionary containing current, hourly, and daily weather data
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "cloud_cover",
                "wind_speed_10m",
                "wind_direction_10m",
                "is_day",
            ],
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation_probability",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "sunrise",
                "sunset",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_direction_10m_dominant",
            ],
            "forecast_days": 7,
        }

        response = await self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        return response.json()

    async def __aenter__(self) -> "WeatherAPIClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
