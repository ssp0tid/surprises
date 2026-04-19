"""Color theme definitions for GitViz."""

from typing import Literal

from textual.color import Color


class Theme:
    """GitViz color theme."""

    background = Color.parse("#1e1e1e")
    surface = Color.parse("#252526")
    surface_bright = Color.parse("#2d2d30")
    primary = Color.parse("#0e639c")
    secondary = Color.parse("#3c3c3c")
    accent = Color.parse("#3794ff")

    text_default = Color.parse("#cccccc")
    text_muted = Color.parse("#808080")
    text_bright = Color.parse("#ffffff")

    branch_main = Color.parse("#3794ff")
    branch_feature = Color.parse("#4ec9b0")
    branch_bugfix = Color.parse("#ce9178")
    branch_hotfix = Color.parse("#dcdcaa")
    branch_release = Color.parse("#c586c0")

    graph_line = Color.parse("#444444")
    graph_node = Color.parse("#ffffff")

    success = Color.parse("#4ec9b0")
    warning = Color.parse("#dcdcaa")
    error = Color.parse("#f14c4c")

    search_highlight = Color.parse("#612e10")
    selected_row = Color.parse("#094771")


THEME_COLORS: dict[str, str] = {
    "background": "#1e1e1e",
    "surface": "#252526",
    "surface_bright": "#2d2d30",
    "primary": "#0e639c",
    "secondary": "#3c3c3c",
    "accent": "#3794ff",
    "text_default": "#cccccc",
    "text_muted": "#808080",
    "text_bright": "#ffffff",
    "branch_main": "#3794ff",
    "branch_feature": "#4ec9b0",
    "branch_bugfix": "#ce9178",
    "branch_hotfix": "#dcdcaa",
    "branch_release": "#c586c0",
    "graph_line": "#444444",
    "graph_node": "#ffffff",
    "success": "#4ec9b0",
    "warning": "#dcdcaa",
    "error": "#f14c4c",
    "search_highlight": "#612e10",
    "selected_row": "#094771",
}


def get_branch_color(branch_name: str) -> str:
    """Get color for branch name."""
    if branch_name in ("main", "master"):
        return "branch_main"
    if branch_name.startswith("feature/"):
        return "branch_feature"
    if branch_name.startswith("bugfix/"):
        return "branch_bugfix"
    if branch_name.startswith("hotfix/"):
        return "branch_hotfix"
    if branch_name.startswith("release/"):
        return "branch_release"
    return "accent"
