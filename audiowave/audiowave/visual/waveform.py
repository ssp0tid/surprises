"""Waveform visualization."""

from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from audiowave.audio.types import AudioData
from audiowave.visual.styles import apply_style, get_color_palette
from audiowave.utils.exceptions import RenderError


def render_waveform(
    audio_data: AudioData,
    output_path: Optional[str] = None,
    width: int = 1920,
    height: int = 400,
    color: str = "#2196F3",
    background: str = "#FFFFFF",
    style: str = "classic",
    dpi: int = 100,
    mono: bool = False,
    zoom: int = 1,
) -> Figure:
    """Render waveform visualization.

    Args:
        audio_data: Audio data to visualize
        output_path: Optional path to save image
        width: Image width in pixels
        height: Image height in pixels
        color: Waveform color
        background: Background color
        style: Matplotlib style
        dpi: Image DPI
        mono: Use mono channel
        zoom: Zoom level (1-10)

    Returns:
        Matplotlib Figure object
    """
    try:
        apply_style(style)
    except Exception as e:
        raise RenderError(f"Failed to apply style: {e}")

    if audio_data.channels > 1 and not mono:
        fig, axes = plt.subplots(2, 1, figsize=(width / dpi, height / dpi * 2), dpi=dpi)
        fig.patch.set_facecolor(background)

        for i, ax in enumerate(axes):
            channel_data = (
                audio_data.samples[:, i]
                if audio_data.samples.ndim > 1
                else audio_data.samples
            )

            if zoom > 1:
                start = len(channel_data) // 2 - len(channel_data) // (2 * zoom)
                end = len(channel_data) // 2 + len(channel_data) // (2 * zoom)
                channel_data = channel_data[start:end]

            ax.plot(channel_data, color=color, linewidth=0.5)
            ax.set_facecolor(background)
            ax.set_title(f"Channel {i + 1}", color=color)
            ax.set_xlabel("Samples")
            ax.set_ylabel("Amplitude")

        plt.tight_layout()
    else:
        fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
        fig.patch.set_facecolor(background)

        ax = fig.add_subplot(111)
        samples = audio_data.samples
        if audio_data.channels > 1:
            samples = np.mean(audio_data.samples, axis=1)

        if zoom > 1:
            start = len(samples) // 2 - len(samples) // (2 * zoom)
            end = len(samples) // 2 + len(samples) // (2 * zoom)
            samples = samples[start:end]

        ax.plot(samples, color=color, linewidth=0.5)
        ax.set_facecolor(background)
        ax.set_title("Waveform")
        ax.set_xlabel("Samples")
        ax.set_ylabel("Amplitude")

    if output_path:
        try:
            fig.savefig(output_path, facecolor=background, bbox_inches="tight")
        except Exception as e:
            raise RenderError(f"Failed to save waveform: {e}")

    return fig
