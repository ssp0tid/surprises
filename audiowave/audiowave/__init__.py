"""AudioWave - CLI tool for audio waveform visualization and frequency spectrum analysis."""

__version__ = "0.1.0"
__author__ = "AudioWave Team"

from audiowave.audio.types import (
    AudioData,
    AudioStatistics,
    SpectrumData,
    BeatInfo,
    AnalysisResult,
)

__all__ = [
    "AudioData",
    "AudioStatistics",
    "SpectrumData",
    "BeatInfo",
    "AnalysisResult",
]
