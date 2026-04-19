"""ASCII art weather icons and Unicode symbols for Weather TUI."""

from textual.widget import Widget

WEATHER_SYMBOLS = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌧️",
    53: "🌧️",
    55: "🌧️",
    56: "🌧️",
    57: "🌧️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    66: "🌧️",
    67: "🌧️",
    71: "🌨️",
    73: "🌨️",
    75: "❄️",
    77: "🌨️",
    80: "🌦️",
    81: "🌦️",
    82: "⛈️",
    85: "🌨️",
    86: "🌨️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}

CLEAR_SKY = r"""
    \   |   /
      .---.
   -- (   ) --
      '---'
    /   |   \
"""

SUNNY = r"""
     \  o  /
   o .---. o
      |   |
     / .---. \
    o  | |  o
     /  |  \
"""

CLOUDY = r"""
      .--.
   .-(    ).
  (___.__)__)
     |  |
   __|  |__
  (        )
"""

RAINY = r"""
      .--.
   .-(    ).
  (___.__)__)
  ' ' ' ' '
  ' ' ' ' '
  ~~~~~~~~~~~
"""

SNOWY = r"""
      .--.
   .-(    ).
  (___.__)__)
   *  *  *
  *  *  *  *
   *  *  *
"""

THUNDERSTORM = r"""
      .--.
   .-(    ).
  (___.__)__)
   ⚡ || ⚡
   ||  ||
  ~~~~~~~~~~~
"""

NIGHT = r"""
      *   *
    *   .-.   *
   (    -   )
    *       *
      *   *
"""


def get_weather_icon(weather_code: int, is_day: bool = True) -> str:
    """Get Unicode weather symbol for WMO weather code."""
    if not is_day:
        if weather_code in (0, 1):
            return "🌙"
        elif weather_code in (2, 3):
            return "☁️"
        elif weather_code >= 45:
            return "🌫️"
    return WEATHER_SYMBOLS.get(weather_code, "❓")


def get_weather_ascii(weather_code: int, is_day: bool = True) -> str:
    """Get ASCII art for weather code."""
    if not is_day:
        return NIGHT

    if weather_code == 0:
        return CLEAR_SKY
    elif weather_code == 1:
        return SUNNY
    elif weather_code in (2, 3):
        return CLOUDY
    elif weather_code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return RAINY
    elif weather_code in (71, 73, 75, 77, 85, 86):
        return SNOWY
    elif weather_code in (95, 96, 99):
        return THUNDERSTORM
    elif weather_code in (45, 48):
        return CLOUDY
    return CLEAR_SKY
