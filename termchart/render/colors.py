from __future__ import annotations


def _fg256(color_index: int) -> str:
    return f"\033[38;5;{color_index}m"


def _reset() -> str:
    return "\033[0m"


SCHEMES: dict[str, list[int]] = {
    "rainbow": [196, 208, 220, 226, 118, 46, 48, 51, 45, 39, 63, 129, 165, 201],
    "heat": [16, 52, 88, 124, 160, 196, 202, 208, 214, 220, 226, 228, 230, 231],
    "cool": [17, 18, 19, 20, 21, 27, 33, 39, 45, 51, 87, 123, 159, 195],
    "mono": [232, 235, 238, 241, 244, 247, 250, 253, 255],
    "pastel": [217, 218, 223, 229, 194, 158, 153, 147, 183, 219],
}

DEFAULT_SCHEME = "rainbow"


def colorize(text: str, color_index: int, enabled: bool = True) -> str:
    """Wrap text with ANSI 256-color foreground escape sequences.

    Args:
        text: The text to colorize.
        color_index: ANSI 256-color palette index (0-255).
        enabled: If False, return text unchanged.

    Returns:
        Colorized string or plain text if disabled.
    """
    if not enabled:
        return text
    return f"{_fg256(color_index)}{text}{_reset()}"


def gradient(value: float, min_val: float, max_val: float, scheme: str = DEFAULT_SCHEME, enabled: bool = True) -> int:
    """Map a value to a color index from the given scheme.

    Args:
        value: The value to map.
        min_val: Minimum of the data range.
        max_val: Maximum of the data range.
        scheme: Name of the color scheme.
        enabled: If False, return 255 (white).

    Returns:
        ANSI 256-color index.
    """
    if not enabled:
        return 255
    colors = SCHEMES.get(scheme, SCHEMES[DEFAULT_SCHEME])
    if max_val == min_val:
        return colors[len(colors) // 2]
    ratio = max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
    index = int(ratio * (len(colors) - 1))
    return colors[index]


def scheme_color(index: int, scheme: str = DEFAULT_SCHEME) -> int:
    """Get a color from a scheme by cycling index.

    Args:
        index: Position (will wrap around).
        scheme: Name of the color scheme.

    Returns:
        ANSI 256-color index.
    """
    colors = SCHEMES.get(scheme, SCHEMES[DEFAULT_SCHEME])
    return colors[index % len(colors)]
