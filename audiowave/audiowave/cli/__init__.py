"""CLI package initialization."""

from audiowave.cli.main import main
from audiowave.cli.commands import (
    analyze_command,
    waveform_command,
    spectrum_command,
    beats_command,
    all_command,
)

__all__ = [
    "main",
    "analyze_command",
    "waveform_command",
    "spectrum_command",
    "beats_command",
    "all_command",
]
