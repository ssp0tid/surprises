"""Current weather display widget for Weather TUI."""

from textual.widgets import Static

from .ascii_weather import get_weather_icon
from .wind_compass import get_wind_direction_name, get_wind_arrow


class CurrentWeatherWidget(Static):
    """Widget displaying current weather conditions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._temperature = 0.0
        self._feels_like = 0.0
        self._humidity = 0
        self._wind_speed = 0.0
        self._wind_direction = 0
        self._weather_code = 0
        self._is_day = True

    def update(
        self,
        temperature: float,
        feels_like: float,
        humidity: int,
        wind_speed: float,
        wind_direction: int,
        weather_code: int,
        is_day: bool,
    ) -> None:
        """Update the widget with current weather data."""
        self._temperature = temperature
        self._feels_like = feels_like
        self._humidity = humidity
        self._wind_speed = wind_speed
        self._wind_direction = wind_direction
        self._weather_code = weather_code
        self._is_day = is_day
        self.refresh()

    def render(self) -> str:
        """Render current weather display."""
        weather_icon = get_weather_icon(self._weather_code, self._is_day)
        wind_dir = get_wind_direction_name(self._wind_direction)
        wind_arrow = get_wind_arrow(self._wind_direction)

        return f"""[b]CURRENT WEATHER[/b]
{weather_icon}

[b]Temperature:[/b] {self._temperature:.1f}°
[b]Feels Like:[/b] {self._feels_like:.1f}°
[b]Humidity:[/b] {self._humidity}%
[b]Wind:[/b] {wind_arrow} {self._wind_speed:.1f} km/h ({wind_dir})"""
