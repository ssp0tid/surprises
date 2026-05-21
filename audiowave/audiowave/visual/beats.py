"""Beat visualization."""

from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from audiowave.audio.types import AudioData, BeatInfo
from audiowave.audio.beat import detect_beats
from audiowave.visual.styles import apply_style
from audiowave.utils.exceptions import RenderError


def render_beats(
    audio_data: AudioData,
    output_path: Optional[str] = None,
    width: int = 1920,
    height: int = 600,
    sensitivity: float = 1.0,
    min_bpm: float = 60,
    max_bpm: float = 200,
    show_bpm: bool = True,
    color: str = "#FF5722",
    background: str = "#FFFFFF",
    style: str = "classic",
    dpi: int = 100,
) -> Figure:
    """Render beat visualization with waveform overlay.

    Args:
        audio_data: Audio data to visualize
        output_path: Optional path to save image
        width: Image width in pixels
        height: Image height in pixels
        sensitivity: Beat detection sensitivity
        min_bpm: Minimum BPM to detect
        max_bpm: Maximum BPM to detect
        show_bpm: Display detected BPM on image
        color: Beat marker color
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

    beats = detect_beats(
        audio_data, sensitivity=sensitivity, min_bpm=min_bpm, max_bpm=max_bpm
    )

    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor(background)

    ax = fig.add_subplot(111)
    ax.set_facecolor(background)

    time = np.linspace(0, audio_data.duration, len(audio_data.samples))

    if audio_data.channels > 1:
        samples = np.mean(audio_data.samples, axis=1)
    else:
        samples = audio_data.samples.squeeze()

    ax.plot(time, samples, color="#2196F3", linewidth=0.3, alpha=0.7, label="Waveform")

    if len(beats.beats) > 0:
        ax.vlines(
            beats.beats, -1, 1, colors=color, linewidth=1, alpha=0.8, label="Beats"
        )

    ax.set_xlim(0, audio_data.duration)
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel("Time (s)", color=color)
    ax.set_ylabel("Amplitude", color=color)
    ax.set_title("Beat Detection", color=color, fontsize=14, fontweight="bold")

    if show_bpm and beats.bpm > 0:
        bpm_text = f"Detected BPM: {beats.bpm:.1f}"
        ax.text(
            0.02,
            0.95,
            bpm_text,
            transform=ax.transAxes,
            fontsize=12,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

    ax.tick_params(colors=color)
    for spine in ax.spines.values():
        spine.set_color(color)

    plt.tight_layout()

    if output_path:
        try:
            fig.savefig(output_path, facecolor=background, bbox_inches="tight")
        except Exception as e:
            raise RenderError(f"Failed to save beats visualization: {e}")

    return fig
