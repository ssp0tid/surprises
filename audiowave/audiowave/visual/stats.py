"""Statistics visualization."""

from typing import Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from audiowave.audio.types import AudioStatistics
from audiowave.visual.styles import apply_style
from audiowave.utils.exceptions import RenderError


def render_stats(
    statistics: AudioStatistics,
    output_path: Optional[str] = None,
    width: int = 800,
    height: int = 600,
    background: str = "#FFFFFF",
    style: str = "classic",
    dpi: int = 100,
) -> Figure:
    """Render statistics as a figure.

    Args:
        statistics: Audio statistics to visualize
        output_path: Optional path to save image
        width: Image width in pixels
        height: Image height in pixels
        background: Background color
        style: Matplotlib style
        dpi: Image DPI

    Returns:
        Matplotlib Figure object
    """
    try:
        apply_style(style)
    except Exception as e:
        raise RenderError(f"Failed to apply style: {e}")

    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor(background)

    ax = fig.add_subplot(111)
    ax.set_facecolor(background)
    ax.axis("off")

    stats_text = f"""Audio Statistics

Duration: {format_duration(statistics.duration)}
Sample Rate: {statistics.sample_rate} Hz
Channels: {statistics.channels}
Bit Depth: {statistics.bit_depth}-bit

Peak Amplitude: {statistics.peak_amplitude:.4f}
RMS Level: {statistics.rms_db:.2f} dB
Crest Factor: {statistics.crest_factor:.2f}
Dynamic Range: {statistics.dynamic_range:.2f} dB"""

    ax.text(
        0.1,
        0.9,
        stats_text,
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
    )

    plt.tight_layout()

    if output_path:
        try:
            fig.savefig(output_path, facecolor=background, bbox_inches="tight")
        except Exception as e:
            raise RenderError(f"Failed to save statistics: {e}")

    return fig


def format_duration(seconds: float) -> str:
    """Format duration in seconds to mm:ss.ms format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.2f}"
