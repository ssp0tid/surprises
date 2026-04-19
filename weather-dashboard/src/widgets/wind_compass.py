"""Wind direction utilities and compass widget for Weather TUI."""

from textual.widgets import Static

WIND_DIRECTIONS = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]

WIND_ARROWS = [
    "↓",
    "↙",
    "↙",
    "←",
    "←",
    "↔",
    "↗",
    "↗",
    "↑",
    "↗",
    "↗",
    "→",
    "→",
    "↘",
    "↘",
    "↓",
]


def get_wind_direction_name(degrees: int) -> str:
    """Convert degrees to compass direction."""
    index = round(degrees / 22.5) % 16
    return WIND_DIRECTIONS[index]


def get_wind_arrow(degrees: int) -> str:
    """Get arrow character pointing in wind direction."""
    index = round(degrees / 22.5) % 16
    return WIND_ARROWS[index]


class WindCompass(Static):
    """Widget displaying wind direction as a visual compass."""

    def __init__(self, wind_speed: float = 0.0, wind_direction: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction

    def set_wind(self, speed: float, direction: int) -> None:
        """Update wind data."""
        self.wind_speed = speed
        self.wind_direction = direction
        self.refresh()

    def render(self) -> str:
        """Render the wind compass display."""
        direction_name = get_wind_direction_name(self.wind_direction)
        arrow = get_wind_arrow(self.wind_direction)
        speed_str = f"{self.wind_speed:.1f}"

        return f"{arrow} {speed_str} {direction_name}"


class WindCompassLarge(Static):
    """Large wind compass with ASCII art visualization."""

    def __init__(self, wind_speed: float = 0.0, wind_direction: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction

    def set_wind(self, speed: float, direction: int) -> None:
        """Update wind data."""
        self.wind_speed = speed
        self.wind_direction = direction
        self.refresh()

    def render(self) -> str:
        """Render large wind compass with direction display."""
        direction = self.wind_direction
        direction_name = get_wind_direction_name(direction)
        arrow = get_wind_arrow(direction)
        speed_str = f"{self.wind_speed:.1f}"

        return f"""
    ┌───────────────┐
    │  Wind Compass │
    ├───────────────┤
    │               │
    │      {arrow}       │
    │               │
    │  {direction_name:^11}  │
    │               │
    │  {speed_str:^11}  │
    │               │
    └───────────────┘
"""
