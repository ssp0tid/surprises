"""Moon phase calculation and display widget for Weather TUI."""

from datetime import datetime
from math import cos, pi

from textual.widgets import Static


def calculate_moon_phase(date: datetime = None):
    """Calculate moon phase for a given date."""
    if date is None:
        date = datetime.now()
    known_new_moon = datetime(2000, 1, 6, 18, 14)
    lunation = 29.53058867

    days_since_new = (date - known_new_moon).total_seconds() / 86400
    lunar_cycle = (days_since_new % lunation) / lunation

    illumination = (1 - cos(lunar_cycle * 2 * pi)) / 2 * 100

    if lunar_cycle < 0.026:
        name = "New Moon"
    elif lunar_cycle < 0.223:
        name = "Waxing Crescent"
    elif lunar_cycle < 0.476:
        name = "First Quarter"
    elif lunar_cycle < 0.726:
        name = "Waxing Gibbous"
    elif lunar_cycle < 0.976:
        name = "Full Moon"
    else:
        name = "Waning Gibbous"

    return name, illumination


def get_moon_ascii(phase: float) -> str:
    """Get moon emoji based on illumination (0-100)."""
    if phase < 12.5:
        return "🌑"
    elif phase < 37.5:
        return "🌒"
    elif phase < 62.5:
        return "🌓"
    elif phase < 87.5:
        return "🌔"
    else:
        return "🌕"


def get_moon_name_from_api(phase: float) -> str:
    """Convert API moon phase (0.0-1.0) to moon phase name."""
    if phase < 0.0625 or phase >= 0.9375:
        return "New Moon"
    elif phase < 0.1875:
        return "Waxing Crescent"
    elif phase < 0.3125:
        return "First Quarter"
    elif phase < 0.4375:
        return "Waxing Gibbous"
    elif phase < 0.5625:
        return "Full Moon"
    elif phase < 0.6875:
        return "Waning Gibbous"
    elif phase < 0.8125:
        return "Last Quarter"
    else:
        return "Waning Crescent"


class MoonPhase(Static):
    """Widget displaying current moon phase."""

    def __init__(self, date=None, moon_phase_api: float = None, **kwargs):
        super().__init__(**kwargs)
        self.date = date or datetime.now()
        self.moon_phase_api = moon_phase_api

    def set_date(self, date: datetime) -> None:
        """Update the date for moon phase calculation."""
        self.date = date
        self.refresh()

    def set_moon_phase_from_api(self, phase: float) -> None:
        """Set moon phase from Open-Meteo API."""
        self.moon_phase_api = phase
        self.refresh()

    def render(self) -> str:
        """Render moon phase display."""
        if self.moon_phase_api is not None:
            name = get_moon_name_from_api(self.moon_phase_api)
            moon_emoji = get_moon_ascii(self.moon_phase_api * 100)
            return f"Moon: {moon_emoji} {name}"
        else:
            name, illumination = calculate_moon_phase(self.date)
            moon_emoji = get_moon_ascii(illumination)
            return f"Moon: {moon_emoji} {name}"


class MoonPhaseLarge(Static):
    """Large moon phase display with ASCII art visualization."""

    def __init__(self, date=None, moon_phase_api: float = None, **kwargs):
        super().__init__(**kwargs)
        self.date = date or datetime.now()
        self.moon_phase_api = moon_phase_api

    def set_date(self, date: datetime) -> None:
        """Update the date for moon phase calculation."""
        self.date = date
        self.refresh()

    def set_moon_phase_from_api(self, phase: float) -> None:
        """Set moon phase from Open-Meteo API."""
        self.moon_phase_api = phase
        self.refresh()

    def render(self) -> str:
        """Render large moon phase display with box."""
        if self.moon_phase_api is not None:
            name = get_moon_name_from_api(self.moon_phase_api)
            moon_emoji = get_moon_ascii(self.moon_phase_api * 100)
        else:
            name, illumination = calculate_moon_phase(self.date)
            moon_emoji = get_moon_ascii(illumination)

        return f"""
┌─────────────────────┐
│     Moon Phase      │
├─────────────────────┤
│                     │
│       {moon_emoji}         │
│                     │
│    {name:^17}   │
│                     │
└─────────────────────┘
"""
