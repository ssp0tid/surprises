"""Weather data models for Weather TUI application."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from .location import Location


@dataclass
class CurrentWeather:
    """Current weather conditions."""

    temperature: float
    feels_like: float
    humidity: int
    precipitation: float
    weather_code: int
    cloud_cover: int
    wind_speed: float
    wind_direction: int
    is_day: bool


@dataclass
class HourlyForecast:
    """Hourly weather forecast entry."""

    time: datetime
    temperature: float
    humidity: int
    precipitation_probability: int
    precipitation: float
    weather_code: int
    wind_speed: float
    wind_direction: int


@dataclass
class DailyForecast:
    """Daily weather forecast entry."""

    date: date
    weather_code: int
    temp_max: float
    temp_min: float
    sunrise: datetime
    sunset: datetime
    precipitation_sum: float
    precipitation_probability: int
    wind_speed_max: float
    wind_direction: int


@dataclass
class WeatherData:
    """Complete weather data container."""

    location: Location
    current: CurrentWeather
    hourly: List[HourlyForecast]
    daily: List[DailyForecast]
    timezone: str
    last_updated: datetime
