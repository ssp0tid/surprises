"""Data structures for audio data."""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class AudioData:
    """Container for loaded audio data."""

    samples: np.ndarray
    sample_rate: int
    channels: int
    bit_depth: int
    duration: float
    filepath: str
    format: str


@dataclass
class AudioStatistics:
    """Statistical analysis results."""

    duration: float
    sample_rate: int
    channels: int
    bit_depth: int
    peak_amplitude: float
    rms_level: float
    rms_db: float
    crest_factor: float
    dynamic_range: float


@dataclass
class SpectrumData:
    """Frequency spectrum data."""

    frequencies: np.ndarray
    magnitudes: np.ndarray
    magnitudes_db: np.ndarray
    sample_rate: int
    window_type: str


@dataclass
class BeatInfo:
    """Beat detection results."""

    beats: np.ndarray
    bpm: float
    confidence: float
    energy_envelope: np.ndarray
    onset_times: np.ndarray


@dataclass
class AnalysisResult:
    """Complete analysis results."""

    audio: AudioData
    statistics: AudioStatistics
    spectrum: Optional[SpectrumData] = None
    beats: Optional[BeatInfo] = None
