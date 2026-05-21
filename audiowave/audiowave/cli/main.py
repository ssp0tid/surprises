"""CLI main entry point."""

import click
import sys

from audiowave.utils.logging import setup_logging
from audiowave.utils.exceptions import AudioWaveError
from audiowave.cli import commands


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Suppress non-essential output")
@click.option(
    "--config", type=click.Path(exists=True), help="Custom configuration file"
)
@click.pass_context
def cli(ctx, verbose, quiet, config):
    """AudioWave - CLI tool for audio waveform visualization and frequency spectrum analysis."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["config"] = config

    setup_logging(verbose=verbose, quiet=quiet)


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option(
    "-o", "--output", "output_file", type=click.Path(), help="Save statistics to file"
)
@click.option(
    "--channels",
    "channel",
    type=int,
    help="Channel to analyze (0=left, 1=right, -1=all)",
)
@click.pass_context
def analyze(ctx, filepath, json_output, output_file, channel):
    """Analyze audio file and show statistics."""
    sys.exit(
        commands.analyze_command(
            filepath, json_output=json_output, output_file=output_file, channel=channel
        )
    )


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "-o", "--output", "output_path", type=click.Path(), help="Output image path"
)
@click.option("--width", default=1920, type=int, help="Image width in pixels")
@click.option("--height", default=400, type=int, help="Image height in pixels")
@click.option("--color", default="#2196F3", help="Waveform color")
@click.option("--background", default="#FFFFFF", help="Background color")
@click.option(
    "--style",
    default="classic",
    type=click.Choice(["classic", "seaborn", "ggplot", "dark"]),
    help="Matplotlib style",
)
@click.option("--dpi", default=100, type=int, help="Image DPI")
@click.option("--mono", is_flag=True, help="Mono channel if stereo")
@click.option("--zoom", default=1, type=int, help="Zoom level for detail view (1-10)")
@click.pass_context
def waveform(
    ctx, filepath, output_path, width, height, color, background, style, dpi, mono, zoom
):
    """Generate waveform visualization."""
    sys.exit(
        commands.waveform_command(
            filepath,
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
    )


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "-o", "--output", "output_path", type=click.Path(), help="Output image path"
)
@click.option("--width", default=1280, type=int, help="Image width")
@click.option("--height", default=720, type=int, help="Image height")
@click.option("--bars", default=64, type=int, help="Number of frequency bars")
@click.option(
    "--log", "log_scale", is_flag=True, help="Use logarithmic frequency scale"
)
@click.option("--db-range", default=80.0, type=float, help="dB range for display")
@click.option("--color", default="#4CAF50", help="Bar color")
@click.option("--background", default="#1a1a2e", help="Background color")
@click.option(
    "--style",
    default="dark",
    type=click.Choice(["classic", "seaborn", "ggplot", "dark"]),
    help="Matplotlib style",
)
@click.option("--dpi", default=100, type=int, help="Image DPI")
@click.option(
    "--window",
    default="hann",
    type=click.Choice(["hann", "hamming", "blackman"]),
    help="FFT window function",
)
@click.pass_context
def spectrum(
    ctx,
    filepath,
    output_path,
    width,
    height,
    bars,
    log_scale,
    db_range,
    color,
    background,
    style,
    dpi,
    window,
):
    """Generate frequency spectrum visualization."""
    sys.exit(
        commands.spectrum_command(
            filepath,
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
    )


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "-o", "--output", "output_path", type=click.Path(), help="Output image path"
)
@click.option("--width", default=1920, type=int, help="Image width")
@click.option("--height", default=600, type=int, help="Image height")
@click.option(
    "--sensitivity",
    default=1.0,
    type=float,
    help="Beat detection sensitivity (0.1-2.0)",
)
@click.option("--min-bpm", default=60, type=float, help="Minimum BPM to detect")
@click.option("--max-bpm", default=200, type=float, help="Maximum BPM to detect")
@click.option(
    "--show-bpm", is_flag=True, default=False, help="Display detected BPM on image"
)
@click.option("--color", default="#FF5722", help="Beat marker color")
@click.option("--background", default="#FFFFFF", help="Background color")
@click.option(
    "--style",
    default="classic",
    type=click.Choice(["classic", "seaborn", "ggplot", "dark"]),
    help="Matplotlib style",
)
@click.option("--dpi", default=100, type=int, help="Image DPI")
@click.pass_context
def beats(
    ctx,
    filepath,
    output_path,
    width,
    height,
    sensitivity,
    min_bpm,
    max_bpm,
    show_bpm,
    color,
    background,
    style,
    dpi,
):
    """Detect and visualize beats."""
    sys.exit(
        commands.beats_command(
            filepath,
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
    )


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output-dir",
    "output_dir",
    default="./audiowave_output",
    help="Output directory",
)
@click.option("--prefix", type=str, help="Filename prefix")
@click.option(
    "--format",
    "image_format",
    default="png",
    type=click.Choice(["png", "jpg", "svg", "pdf"]),
    help="Image format",
)
@click.option("--all-options", is_flag=True, help="Apply all options from all commands")
@click.pass_context
def all(ctx, filepath, output_dir, prefix, image_format, all_options):
    """Generate all visualizations at once."""
    sys.exit(
        commands.all_command(
            filepath,
            output_dir=output_dir,
            prefix=prefix,
            format=image_format,
            all_options=all_options,
        )
    )


def main():
    """Main entry point."""
    try:
        cli(obj={})
    except AudioWaveError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
