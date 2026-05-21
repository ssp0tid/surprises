"""Command handlers for CLI."""

import os
import sys
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from audiowave.audio.loader import load_audio
from audiowave.audio.analyzer import analyze
from audiowave.audio.beat import detect_beats
from audiowave.visual.waveform import render_waveform
from audiowave.visual.spectrum import render_spectrum
from audiowave.visual.beats import render_beats
from audiowave.visual.stats import render_stats
from audiowave.cli.formatters import format_text, format_json
from audiowave.utils.exceptions import AudioWaveError
from audiowave.utils.logging import get_logger

logger = get_logger(__name__)


def analyze_command(
    filepath: str,
    json_output: bool = False,
    output_file: Optional[str] = None,
    channel: Optional[int] = None,
) -> int:
    """Execute analyze command.

    Args:
        filepath: Path to audio file
        json_output: Output as JSON
        output_file: Optional file to save output
        channel: Specific channel to analyze

    Returns:
        Exit code (0 for success)
    """
    try:
        logger.info(f"Analyzing {filepath}")

        audio_data = load_audio(filepath, channel=channel)

        statistics = analyze(audio_data)

        beats = detect_beats(audio_data)

        if json_output:
            output = format_json(audio_data, statistics, beats)
        else:
            output = format_text(audio_data, statistics, beats)

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            print(f"Output saved to {output_file}")
        else:
            print(output)

        return 0

    except AudioWaveError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def waveform_command(
    filepath: str,
    output_path: Optional[str] = None,
    width: int = 1920,
    height: int = 400,
    color: str = "#2196F3",
    background: str = "#FFFFFF",
    style: str = "classic",
    dpi: int = 100,
    mono: bool = False,
    zoom: int = 1,
) -> int:
    """Execute waveform command.

    Args:
        filepath: Path to audio file
        output_path: Output image path
        width: Image width
        height: Image height
        color: Waveform color
        background: Background color
        style: Matplotlib style
        dpi: Image DPI
        mono: Use mono channel
        zoom: Zoom level

    Returns:
        Exit code
    """
    try:
        logger.info(f"Generating waveform for {filepath}")

        if output_path is None:
            base = Path(filepath).stem
            output_path = f"{base}_waveform.png"

        audio_data = load_audio(filepath, mono=mono)

        with tqdm(total=100, desc="Rendering waveform", unit="%"):
            fig = render_waveform(
                audio_data,
                output_path=output_path,
                width=width,
                height=height,
                color=color,
                background=background,
                style=style,
                dpi=dpi,
                mono=mono,
                zoom=zoom,
            )
            import matplotlib.pyplot as plt

            plt.close(fig)

        print(f"Waveform saved to {output_path}")
        return 0

    except AudioWaveError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def spectrum_command(
    filepath: str,
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
) -> int:
    """Execute spectrum command.

    Args:
        filepath: Path to audio file
        output_path: Output image path
        width: Image width
        height: Image height
        bars: Number of frequency bars
        log_scale: Logarithmic frequency scale
        db_range: dB range
        color: Bar color
        background: Background color
        style: Matplotlib style
        dpi: Image DPI
        window: FFT window type

    Returns:
        Exit code
    """
    try:
        logger.info(f"Generating spectrum for {filepath}")

        if output_path is None:
            base = Path(filepath).stem
            output_path = f"{base}_spectrum.png"

        audio_data = load_audio(filepath, mono=True)

        with tqdm(total=100, desc="Rendering spectrum", unit="%"):
            fig = render_spectrum(
                audio_data,
                output_path=output_path,
                width=width,
                height=height,
                bars=bars,
                log_scale=log_scale,
                db_range=db_range,
                color=color,
                background=background,
                style=style,
                dpi=dpi,
                window=window,
            )
            import matplotlib.pyplot as plt

            plt.close(fig)

        print(f"Spectrum saved to {output_path}")
        return 0

    except AudioWaveError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def beats_command(
    filepath: str,
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
) -> int:
    """Execute beats command.

    Args:
        filepath: Path to audio file
        output_path: Output image path
        width: Image width
        height: Image height
        sensitivity: Beat detection sensitivity
        min_bpm: Minimum BPM
        max_bpm: Maximum BPM
        show_bpm: Display BPM
        color: Beat marker color
        background: Background color
        style: Matplotlib style
        dpi: Image DPI

    Returns:
        Exit code
    """
    try:
        logger.info(f"Detecting beats in {filepath}")

        if output_path is None:
            base = Path(filepath).stem
            output_path = f"{base}_beats.png"

        audio_data = load_audio(filepath, mono=True)

        with tqdm(total=100, desc="Detecting beats", unit="%"):
            beat_info = detect_beats(
                audio_data, sensitivity=sensitivity, min_bpm=min_bpm, max_bpm=max_bpm
            )

            fig = render_beats(
                audio_data,
                output_path=output_path,
                width=width,
                height=height,
                sensitivity=sensitivity,
                min_bpm=min_bpm,
                max_bpm=max_bpm,
                show_bpm=show_bpm,
                color=color,
                background=background,
                style=style,
                dpi=dpi,
            )
            import matplotlib.pyplot as plt

            plt.close(fig)

        print(f"Beat visualization saved to {output_path}")
        if beat_info.bpm > 0:
            print(
                f"Detected BPM: {beat_info.bpm:.1f} (confidence: {beat_info.confidence:.2f})"
            )
        return 0

    except AudioWaveError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def all_command(
    filepath: str,
    output_dir: str = "./audiowave_output",
    prefix: Optional[str] = None,
    format: str = "png",
    all_options: bool = False,
) -> int:
    """Execute all command - generate all visualizations.

    Args:
        filepath: Path to audio file
        output_dir: Output directory
        prefix: Filename prefix
        format: Image format
        all_options: Apply all options

    Returns:
        Exit code
    """
    try:
        logger.info(f"Generating all visualizations for {filepath}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        if prefix is None:
            prefix = Path(filepath).stem

        audio_data = load_audio(filepath)

        print("Generating waveform...")
        wf_path = f"{output_dir}/{prefix}_waveform.{format}"
        fig = render_waveform(audio_data, output_path=wf_path)
        import matplotlib.pyplot as plt

        plt.close(fig)
        print(f"  -> {wf_path}")

        print("Generating spectrum...")
        sp_path = f"{output_dir}/{prefix}_spectrum.{format}"
        mono_data = load_audio(filepath, mono=True)
        fig = render_spectrum(mono_data, output_path=sp_path)
        plt.close(fig)
        print(f"  -> {sp_path}")

        print("Detecting beats...")
        beat_info = detect_beats(audio_data, sensitivity=1.0, min_bpm=60, max_bpm=200)
        bt_path = f"{output_dir}/{prefix}_beats.{format}"
        fig = render_beats(audio_data, output_path=bt_path)
        plt.close(fig)
        print(f"  -> {bt_path}")

        print("Generating statistics...")
        statistics = analyze(audio_data)
        st_path = f"{output_dir}/{prefix}_stats.{format}"
        fig = render_stats(statistics, output_path=st_path)
        plt.close(fig)
        print(f"  -> {st_path}")

        print(f"\nAll visualizations saved to {output_dir}/")
        if beat_info.bpm > 0:
            print(f"Detected BPM: {beat_info.bpm:.1f}")

        return 0

    except AudioWaveError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
