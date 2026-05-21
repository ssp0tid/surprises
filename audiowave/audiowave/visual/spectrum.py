"""Spectrum visualization."""

from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from audiowave.audio.types import AudioData, SpectrumData
from audiowave.audio.spectrum import compute_spectrum, get_frequency_bands
from audiowave.visual.styles import apply_style
from audiowave.utils.exceptions import RenderError


def render_spectrum(
    audio_data: AudioData,
    output_path: Optional[str] = None,
    width: int = 1280,
    height: int = 720,
    bars: int = 64,
    log_scale: bool = False,
    db_range: float = 80.0,
    color: str = "#4CAF50",
    background: str = "#1a1a2e",
    style: str = "dark",
    dpi: int = 100,
    window: str = "hann",
) -> Figure:
    """Render frequency spectrum visualization.

    Args:
        audio_data: Audio data to visualize
        output_path: Optional path to save image
        width: Image width in pixels
        height: Image height in pixels
        bars: Number of frequency bars
        log_scale: Use logarithmic frequency scale
        db_range: dB range for display
        color: Bar color
        background: Background color
        style: Matplotlib style
        dpi: Image DPI
        window: FFT window type

    Returns:
        Matplotlib Figure object
    """
    try:
        apply_style(style)
    except Exception as e:
        raise RenderError(f"Failed to apply style: {e}")

    spectrum = compute_spectrum(audio_data, window_type=window, log_scale=True)

    band_centers, band_mags = get_frequency_bands(
        spectrum, num_bands=bars, log_scale=log_scale
    )

    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor(background)

    ax = fig.add_subplot(111)
    ax.set_facecolor(background)

    x = np.arange(len(band_centers))

    ax.bar(x, band_mags, color=color, width=0.8, alpha=0.8)

    ax.set_xlim(-1, len(band_centers))
    ax.set_ylim(max(-100, min(band_mags) - 5), min(0, max(band_mags) + 5))

    ax.set_xlabel("Frequency", color=color)
    ax.set_ylabel("Magnitude (dB)", color=color)
    ax.set_title("Frequency Spectrum", color=color, fontsize=14, fontweight="bold")

    if log_scale:
        tick_positions = np.linspace(0, len(band_centers) - 1, min(10, bars)).astype(
            int
        )
    else:
        tick_positions = np.linspace(0, len(band_centers) - 1, min(10, bars)).astype(
            int
        )

    freq_labels = []
    for pos in tick_positions:
        if pos < len(band_centers):
            freq = band_centers[pos]
            if freq >= 1000:
                freq_labels.append(f"{freq / 1000:.1f}k")
            else:
                freq_labels.append(f"{freq:.0f}")

    ax.set_xticks(tick_positions)
    ax.set_xticklabels(freq_labels)

    ax.tick_params(colors=color)
    for spine in ax.spines.values():
        spine.set_color(color)

    if output_path:
        try:
            fig.savefig(output_path, facecolor=background, bbox_inches="tight")
        except Exception as e:
            raise RenderError(f"Failed to save spectrum: {e}")

    return fig
