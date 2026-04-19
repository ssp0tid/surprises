from datetime import datetime
from typing import Any, Dict, List, Optional

from api.client import WeatherAPIClient
from api.geocoding import GeocodingClient
from models.location import Location
from models.weather import CurrentWeather, DailyForecast, HourlyForecast, WeatherData
from utils.units import Units

from .cache_service import CacheService


class WeatherServiceError(Exception):
    """Base exception for weather service errors."""

    pass


class OfflineError(WeatherServiceError):
    """Raised when network is unavailable."""

    pass


class WeatherService:
    def __init__(
        self,
        weather_client: WeatherAPIClient,
        geocoding_client: GeocodingClient,
        cache_service: Optional[CacheService] = None,
    ):
        self._weather_client = weather_client
        self._geocoding_client = geocoding_client
        self._cache = cache_service or CacheService()
        self._units = Units.METRIC
        self._current_location: Optional[Location] = None

    def toggle_units(self) -> None:
        if self._units == Units.METRIC:
            self._units = Units.IMPERIAL
        else:
            self._units = Units.METRIC

    @property
    def units(self) -> Units:
        return self._units

    async def get_weather(
        self, latitude: float, longitude: float, location: Optional[Location] = None
    ) -> WeatherData:
        cache_key = f"weather:{latitude},{longitude}"
        cached_data, is_fresh = self._cache.get(cache_key)

        if cached_data and is_fresh:
            return self._convert_units(cached_data)

        if cached_data and not is_fresh:
            try:
                weather_data = await self._fetch_and_parse(
                    latitude, longitude, location
                )
                self._cache.set(cache_key, weather_data)
                return self._convert_units(weather_data)
            except Exception:
                return self._convert_units(cached_data)

        try:
            weather_data = await self._fetch_and_parse(latitude, longitude, location)
            self._cache.set(cache_key, weather_data)
            return self._convert_units(weather_data)
        except Exception as e:
            cached, _, _ = self._cache.get_stale(cache_key)
            if cached:
                return self._convert_units(cached)
            raise OfflineError(f"Unable to fetch weather data: {e}") from e

    async def _fetch_and_parse(
        self, latitude: float, longitude: float, location: Optional[Location] = None
    ) -> WeatherData:
        try:
            raw_data = await self._weather_client.get_weather(latitude, longitude)
        except Exception as e:
            raise OfflineError(f"Network error: {e}") from e

        timezone = raw_data.get("timezone", "UTC")

        loc = location or Location(
            name="Unknown",
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )

        current = self._parse_current(raw_data.get("current", {}))
        hourly = self._parse_hourly(raw_data.get("hourly", {}))
        daily = self._parse_daily(raw_data.get("daily", {}), timezone)

        return WeatherData(
            location=loc,
            current=current,
            hourly=hourly,
            daily=daily,
            timezone=timezone,
            last_updated=datetime.now(),
        )

    def _parse_current(self, data: Dict[str, Any]) -> CurrentWeather:
        return CurrentWeather(
            temperature=data.get("temperature_2m", 0.0),
            feels_like=data.get("apparent_temperature", 0.0),
            humidity=int(data.get("relative_humidity_2m", 0)),
            precipitation=data.get("precipitation", 0.0),
            weather_code=int(data.get("weather_code", 0)),
            cloud_cover=int(data.get("cloud_cover", 0)),
            wind_speed=data.get("wind_speed_10m", 0.0),
            wind_direction=int(data.get("wind_direction_10m", 0)),
            is_day=bool(data.get("is_day", 1)),
        )

    def _parse_hourly(self, data: Dict[str, Any]) -> List[HourlyForecast]:
        times = data.get("time", [])
        temps = data.get("temperature_2m", [])
        humids = data.get("relative_humidity_2m", [])
        precip_probs = data.get("precipitation_probability", [])
        precips = data.get("precipitation", [])
        codes = data.get("weather_code", [])
        winds = data.get("wind_speed_10m", [])
        wind_dirs = data.get("wind_direction_10m", [])

        forecasts = []
        for i in range(min(len(times), 48)):
            forecasts.append(
                HourlyForecast(
                    time=datetime.fromisoformat(times[i])
                    if i < len(times)
                    else datetime.now(),
                    temperature=temps[i] if i < len(temps) else 0.0,
                    humidity=int(humids[i]) if i < len(humids) else 0,
                    precipitation_probability=int(precip_probs[i])
                    if i < len(precip_probs)
                    else 0,
                    precipitation=precips[i] if i < len(precips) else 0.0,
                    weather_code=int(codes[i]) if i < len(codes) else 0,
                    wind_speed=winds[i] if i < len(winds) else 0.0,
                    wind_direction=int(wind_dirs[i]) if i < len(wind_dirs) else 0,
                )
            )

        return forecasts

    def _parse_daily(self, data: Dict[str, Any], timezone: str) -> List[DailyForecast]:
        dates = data.get("time", [])
        codes = data.get("weather_code", [])
        temp_max = data.get("temperature_2m_max", [])
        temp_min = data.get("temperature_2m_min", [])
        sunrises = data.get("sunrise", [])
        sunsets = data.get("sunset", [])
        precip_sums = data.get("precipitation_sum", [])
        precip_probs = data.get("precipitation_probability_max", [])
        wind_max = data.get("wind_speed_10m_max", [])
        wind_dirs = data.get("wind_direction_10m_dominant", [])

        from datetime import date as dt_date

        forecasts = []
        for i in range(min(len(dates), 7)):
            try:
                sunrise_dt = (
                    datetime.fromisoformat(sunrises[i])
                    if i < len(sunrises)
                    else datetime.now()
                )
                sunset_dt = (
                    datetime.fromisoformat(sunsets[i])
                    if i < len(sunsets)
                    else datetime.now()
                )
            except (ValueError, IndexError):
                sunrise_dt = datetime.now()
                sunset_dt = datetime.now()

            forecasts.append(
                DailyForecast(
                    date=dt_date.fromisoformat(dates[i])
                    if i < len(dates)
                    else dt_date.today(),
                    weather_code=int(codes[i]) if i < len(codes) else 0,
                    temp_max=temp_max[i] if i < len(temp_max) else 0.0,
                    temp_min=temp_min[i] if i < len(temp_min) else 0.0,
                    sunrise=sunrise_dt,
                    sunset=sunset_dt,
                    precipitation_sum=precip_sums[i] if i < len(precip_sums) else 0.0,
                    precipitation_probability=int(precip_probs[i])
                    if i < len(precip_probs)
                    else 0,
                    wind_speed_max=wind_max[i] if i < len(wind_max) else 0.0,
                    wind_direction=int(wind_dirs[i]) if i < len(wind_dirs) else 0,
                )
            )

        return forecasts

    def _convert_units(self, weather_data: WeatherData) -> WeatherData:
        if self._units == Units.METRIC:
            return weather_data

        from utils.units import (
            celsius_to_fahrenheit,
            kmh_to_mph,
            mm_to_inches,
        )

        current = weather_data.current
        weather_data.current = type(current)(
            temperature=celsius_to_fahrenheit(current.temperature),
            feels_like=celsius_to_fahrenheit(current.feels_like),
            humidity=current.humidity,
            precipitation=mm_to_inches(current.precipitation),
            weather_code=current.weather_code,
            cloud_cover=current.cloud_cover,
            wind_speed=kmh_to_mph(current.wind_speed),
            wind_direction=current.wind_direction,
            is_day=current.is_day,
        )

        weather_data.hourly = [
            type(h)(
                time=h.time,
                temperature=celsius_to_fahrenheit(h.temperature),
                humidity=h.humidity,
                precipitation_probability=h.precipitation_probability,
                precipitation=mm_to_inches(h.precipitation),
                weather_code=h.weather_code,
                wind_speed=kmh_to_mph(h.wind_speed),
                wind_direction=h.wind_direction,
            )
            for h in weather_data.hourly
        ]

        weather_data.daily = [
            type(d)(
                date=d.date,
                weather_code=d.weather_code,
                temp_max=celsius_to_fahrenheit(d.temp_max),
                temp_min=celsius_to_fahrenheit(d.temp_min),
                sunrise=d.sunrise,
                sunset=d.sunset,
                precipitation_sum=mm_to_inches(d.precipitation_sum),
                precipitation_probability=d.precipitation_probability,
                wind_speed_max=kmh_to_mph(d.wind_speed_max),
                wind_direction=d.wind_direction,
            )
            for d in weather_data.daily
        ]

        return weather_data

    async def search_locations(self, query: str) -> List[Location]:
        if len(query) < 2:
            return []

        try:
            results = await self._geocoding_client.search(query)
        except Exception:
            return []

        locations = []
        for result in results:
            locations.append(
                Location(
                    name=result.get("name", "Unknown"),
                    latitude=result.get("latitude", 0.0),
                    longitude=result.get("longitude", 0.0),
                    timezone=result.get("timezone", "UTC"),
                    country=result.get("country"),
                    admin1=result.get("admin1"),
                )
            )

        return locations
