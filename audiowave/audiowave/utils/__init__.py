"""Utilities package initialization."""

from audiowave.utils.exceptions import (
    AudioWaveError,
    AudioLoadError,
    AudioAnalysisError,
    VisualizationError,
    ConfigurationError,
    CLIError,
)

from audiowave.utils.logging import setup_logging
from audiowave.utils.config import get_config, load_config

__all__ = [
    "AudioWaveError",
    "AudioLoadError",
    "AudioAnalysisError",
    "VisualizationError",
    "ConfigurationError",
    "CLIError",
    "setup_logging",
    "get_config",
    "load_config",
]
