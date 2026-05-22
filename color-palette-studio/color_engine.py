"""Color math engine: conversions, harmony rules, and WCAG contrast checking."""

import colorsys
import random


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple.

    Args:
        hex_color: Color string like '#ff0000' or 'ff0000'.

    Returns:
        Tuple of (r, g, b) integers 0-255.

    Raises:
        ValueError: If hex_color is not a valid hex color.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: '#{hex_color}'. Expected 6 hex digits.")
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    except ValueError:
        raise ValueError(f"Invalid hex color: '#{hex_color}'. Contains non-hex characters.")
    return (r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color string.

    Args:
        r, g, b: Integer values 0-255.

    Returns:
        Hex color string like '#ff0000'.
    """
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color to HSL.

    Args:
        hex_color: Color string like '#ff0000'.

    Returns:
        Tuple of (h, s, l) where h is 0-360, s and l are 0-100.
    """
    r, g, b = hex_to_rgb(hex_color)
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    h, lightness, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
    return (round(h * 360, 1), round(s * 100, 1), round(lightness * 100, 1))


def hsl_to_hex(h: float, s: float, lightness: float) -> str:
    """Convert HSL values to hex color string.

    Args:
        h: Hue 0-360.
        s: Saturation 0-100.
        lightness: Lightness 0-100.

    Returns:
        Hex color string like '#ff0000'.
    """
    h_norm = (h % 360) / 360.0
    s_norm = max(0.0, min(1.0, s / 100.0))
    l_norm = max(0.0, min(1.0, lightness / 100.0))
    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s_norm)
    return rgb_to_hex(round(r * 255), round(g * 255), round(b * 255))


def generate_harmony(base_hex: str, rule: str) -> list[str]:
    """Generate a color palette based on a harmony rule.

    Args:
        base_hex: Base color as hex string.
        rule: One of 'complementary', 'analogous', 'triadic',
              'split-complementary', 'tetradic', 'monochromatic'.

    Returns:
        List of hex color strings including the base color.

    Raises:
        ValueError: If rule is not recognized.
    """
    h, s, lightness = hex_to_hsl(base_hex)

    rules = {
        "complementary": [0, 180],
        "analogous": [-30, 0, 30],
        "triadic": [0, 120, 240],
        "split-complementary": [0, 150, 210],
        "tetradic": [0, 90, 180, 270],
        "monochromatic": [0, 0, 0, 0, 0],
    }

    if rule not in rules:
        valid = ", ".join(sorted(rules.keys()))
        raise ValueError(f"Unknown harmony rule: '{rule}'. Valid rules: {valid}")

    if rule == "monochromatic":
        colors = []
        for i, lightness_offset in enumerate([-20, -10, 0, 10, 20]):
            new_lightness = max(10, min(90, lightness + lightness_offset))
            colors.append(hsl_to_hex(h, s, new_lightness))
        return colors

    offsets = rules[rule]
    colors = []
    for offset in offsets:
        new_h = (h + offset) % 360
        colors.append(hsl_to_hex(new_h, s, lightness))
    return colors


def relative_luminance(hex_color: str) -> float:
    """Calculate relative luminance per WCAG 2.1.

    Args:
        hex_color: Color as hex string.

    Returns:
        Relative luminance value between 0 and 1.
    """
    r, g, b = hex_to_rgb(hex_color)

    def linearize(channel: int) -> float:
        c = channel / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two colors.

    Args:
        color1, color2: Hex color strings.

    Returns:
        Contrast ratio (1.0 to 21.0).
    """
    lum1 = relative_luminance(color1)
    lum2 = relative_luminance(color2)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def wcag_rating(ratio: float) -> str:
    """Determine WCAG conformance level from contrast ratio.

    Args:
        ratio: Contrast ratio value.

    Returns:
        One of 'AAA', 'AA', 'AA Large', or 'Fail'.
    """
    if ratio >= 7.0:
        return "AAA"
    elif ratio >= 4.5:
        return "AA"
    elif ratio >= 3.0:
        return "AA Large"
    return "Fail"


def random_color() -> str:
    """Generate a random hex color.

    Returns:
        Random hex color string.
    """
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return rgb_to_hex(r, g, b)
