"""ANSI color utilities for terminal output."""

from enum import Enum


class TextColor(Enum):
    """ANSI text colors."""

    # Temperature colors
    HOT = "\033[38;5;203m"  # Red (#FF6B6B)
    WARM = "\033[38;5;215m"  # Orange (#FFA94D)
    MILD = "\033[38;5;226m"  # Yellow (#FFE066)
    COOL = "\033[38;5;109m"  # Cyan (#66D9E8)
    COLD = "\033[38;5;75m"  # Blue (#339AF0)
    FREEZE = "\033[38;5;141m"  # Purple (#9775FA)

    # Weather colors
    RAIN = "\033[38;5;75m"  # Blue
    SNOW = "\033[38;5;15m"  # White
    CLOUDS = "\033[38;5;145m"  # Gray
    SUN = "\033[38;5;227m"  # Yellow
    MOON = "\033[38;5;117m"  # Light Cyan
    WIND = "\033[38;5;82m"  # Green

    # UI colors
    ERROR = "\033[38;5;203m"  # Red
    INFO = "\033[38;5;44m"  # Cyan
    SUCCESS = "\033[38;5;82m"  # Green
    WARNING = "\033[38;5;214m"  # Orange

    # Neutrals
    WHITE = "\033[38;5;15m"
    GRAY = "\033[38;5;145m"
    DARK_GRAY = "\033[38;5;240m"

    # Textual theme integration
    PRIMARY = "\033[38;5;75m"
    SECONDARY = "\033[38;5;109m"


# Reset code
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def get_temperature_color(temp: float, is_fahrenheit: bool = False) -> str:
    """
    Get color for temperature.

    Args:
        temp: Temperature in Celsius (or Fahrenheit if is_fahrenheit=True)
        is_fahrenheit: Whether the temperature is in Fahrenheit
    """
    # Convert to Celsius for comparison if needed
    if is_fahrenheit:
        temp = (temp - 32) * 5 / 9

    if temp >= 35:
        return TextColor.HOT.value
    elif temp >= 25:
        return TextColor.WARM.value
    elif temp >= 15:
        return TextColor.MILD.value
    elif temp >= 5:
        return TextColor.COOL.value
    elif temp >= -5:
        return TextColor.COLD.value
    else:
        return TextColor.FREEZE.value


def colorize(text: str, color: TextColor) -> str:
    """Apply color to text."""
    return f"{color.value}{text}{RESET}"


def colorize_temperature(temp: float, is_fahrenheit: bool = False) -> str:
    """Colorize temperature text with appropriate color."""
    color = get_temperature_color(temp, is_fahrenheit)
    return f"{color}{temp:.1f}{RESET}"


def bold(text: str) -> str:
    """Make text bold."""
    return f"{BOLD}{text}{RESET}"


def dim(text: str) -> str:
    """Make text dim."""
    return f"{DIM}{text}{RESET}"


def success(text: str) -> str:
    """Format text as success."""
    return colorize(text, TextColor.SUCCESS)


def error(text: str) -> str:
    """Format text as error."""
    return colorize(text, TextColor.ERROR)


def warning(text: str) -> str:
    """Format text as warning."""
    return colorize(text, TextColor.WARNING)


def info(text: str) -> str:
    """Format text as info."""
    return colorize(text, TextColor.INFO)
