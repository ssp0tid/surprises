"""Color management for branches and commits."""

from typing import Literal


BRANCH_COLORS = [
    "cyan",
    "green",
    "magenta",
    "yellow",
    "blue",
    "bright_red",
    "bright_green",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
]

COLOR_HEX = {
    "black": "000000",
    "red": "FF0000",
    "green": "00FF00",
    "yellow": "FFFF00",
    "blue": "0000FF",
    "magenta": "FF00FF",
    "cyan": "00FFFF",
    "white": "FFFFFF",
    "bright_black": "808080",
    "bright_red": "FF8080",
    "bright_green": "80FF80",
    "bright_yellow": "FFFF80",
    "bright_blue": "8080FF",
    "bright_magenta": "FF80FF",
    "bright_cyan": "80FFFF",
    "bright_white": "FFFFFF",
}

MARKUP_COLORS = {
    "black": "dark_khaki",
    "red": "red",
    "green": "green",
    "yellow": "yellow",
    "blue": "blue",
    "magenta": "magenta",
    "cyan": "cyan",
    "white": "white",
    "bright_black": "grey60",
    "bright_red": "bright_red",
    "bright_green": "bright_green",
    "bright_yellow": "bright_yellow",
    "bright_blue": "bright_blue",
    "bright_magenta": "bright_magenta",
    "bright_cyan": "bright_cyan",
    "bright_white": "bright_white",
    "default": "default",
}


class ColorManager:
    """Manages colors for graph branches."""

    def __init__(self):
        self._color_index = 0
        self._branch_colors: dict[str, str] = {}

    def get_color(self, name: str) -> str:
        """Get color for branch name."""
        if name in self._branch_colors:
            return self._branch_colors[name]

        if name in ("main", "master"):
            color = "cyan"
        elif name.startswith("feature/"):
            color = "green"
        elif name.startswith("bugfix/"):
            color = "magenta"
        elif name.startswith("hotfix/"):
            color = "yellow"
        elif name.startswith("release/"):
            color = "bright_blue"
        else:
            color = BRANCH_COLORS[self._color_index % len(BRANCH_COLORS)]
            self._color_index += 1

        self._branch_colors[name] = color
        return color

    def get_markup_color(self, color: str) -> str:
        """Get Textual markup color."""
        return MARKUP_COLORS.get(color, "default")

    def cycle_color(self) -> str:
        """Get next color in cycle."""
        color = BRANCH_COLORS[self._color_index % len(BRANCH_COLORS)]
        self._color_index += 1
        return color

    def reset(self) -> None:
        """Reset color state."""
        self._color_index = 0
        self._branch_colors.clear()


def get_default_color() -> str:
    """Get default color."""
    return "default"


def get_color_for_oid(oid: bytes, branch_colors: dict[bytes, str]) -> str:
    """Get color for commit OID based on branch colors."""
    return branch_colors.get(oid, "default")
