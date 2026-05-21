"""Matplotlib style configurations."""

from typing import Dict, Any

AVAILABLE_STYLES = ["classic", "seaborn", "ggplot", "dark"]

STYLE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "classic": {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "black",
        "axes.labelcolor": "black",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.color": "gray",
        "lines.color": "black",
        "text.color": "black",
        "xtick.color": "black",
        "ytick.color": "black",
    },
    "seaborn": {
        "figure.facecolor": "#f0f0f0",
        "axes.facecolor": "#f0f0f0",
        "axes.edgecolor": "#cccccc",
        "axes.labelcolor": "#333333",
        "axes.grid": True,
        "grid.alpha": 0.4,
        "grid.color": "white",
        "lines.color": "#333333",
        "text.color": "#333333",
        "xtick.color": "#333333",
        "ytick.color": "#333333",
    },
    "ggplot": {
        "figure.facecolor": "#f5f5f5",
        "axes.facecolor": "#f5f5f5",
        "axes.edgecolor": "#cccccc",
        "axes.labelcolor": "#333333",
        "axes.grid": True,
        "grid.alpha": 0.5,
        "grid.color": "white",
        "lines.color": "#333333",
        "text.color": "#333333",
        "xtick.color": "#333333",
        "ytick.color": "#333333",
    },
    "dark": {
        "figure.facecolor": "#1a1a2e",
        "axes.facecolor": "#1a1a2e",
        "axes.edgecolor": "#444444",
        "axes.labelcolor": "#e0e0e0",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.color": "#444444",
        "lines.color": "#e0e0e0",
        "text.color": "#e0e0e0",
        "xtick.color": "#e0e0e0",
        "ytick.color": "#e0e0e0",
    },
}

DEFAULT_COLORS = {
    "waveform": "#2196F3",
    "spectrum": "#4CAF50",
    "beats": "#FF5722",
    "background": "#FFFFFF",
    "background_dark": "#1a1a2e",
}


def apply_style(style_name: str) -> None:
    """Apply matplotlib style configuration.

    Args:
        style_name: Name of style to apply
    """
    import matplotlib.pyplot as plt

    if style_name == "default":
        plt.style.use("default")
        return

    if style_name in STYLE_CONFIGS:
        plt.rcParams.update(STYLE_CONFIGS[style_name])
    else:
        import warnings

        warnings.warn(f"Unknown style '{style_name}', using default")
        plt.style.use("default")


def get_color_palette(style: str) -> Dict[str, str]:
    """Get color palette for a style.

    Args:
        style: Style name

    Returns:
        Dictionary of color assignments
    """
    if style == "dark":
        return {
            **DEFAULT_COLORS,
            "background": DEFAULT_COLORS["background_dark"],
        }
    return DEFAULT_COLORS.copy()
