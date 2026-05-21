"""Statistical analysis of audio data."""

import numpy as np
from typing import Optional

from audiowave.audio.types import AudioData, AudioStatistics
from audiowave.utils.exceptions import InsufficientDataError
from audiowave.utils.logging import get_logger

logger = get_logger(__name__)


def analyze(audio_data: AudioData) -> AudioStatistics:
    """Compute statistical analysis of audio data.

    Args:
        audio_data: Loaded audio data

    Returns:
        AudioStatistics with computed values
    """
    samples = audio_data.samples

    if len(samples) == 0:
        raise InsufficientDataError("No audio samples to analyze")

    peak_amplitude = float(np.max(np.abs(samples)))

    rms = float(np.sqrt(np.mean(samples**2)))

    rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf

    crest_factor = peak_amplitude / rms if rms > 0 else np.inf

    min_amp = np.min(samples)
    max_amp = np.max(samples)
    dynamic_range = 20 * np.log10(max_amp / min_amp) if min_amp != 0 else np.inf

    return AudioStatistics(
        duration=audio_data.duration,
        sample_rate=audio_data.sample_rate,
        channels=audio_data.channels,
        bit_depth=audio_data.bit_depth,
        peak_amplitude=peak_amplitude,
        rms_level=rms,
        rms_db=rms_db,
        crest_factor=crest_factor,
        dynamic_range=dynamic_range,
    )


def compute_rms(samples: np.ndarray, window_size: int = 1024) -> np.ndarray:
    """Compute rolling RMS energy.

    Args:
        samples: Audio samples
        window_size: Window size for RMS calculation

    Returns:
        Array of RMS values
    """
    if len(samples) < window_size:
        return np.array([np.sqrt(np.mean(samples**2))])

    shape = (len(samples) - window_size + 1, window_size)
    strides = (samples.strides[0], samples.strides[0])
    windows = np.lib.stride_tricks.as_strided(samples, shape=shape, strides=strides)
    return np.sqrt(np.mean(windows**2, axis=1))


def compute_peak_envelope(samples: np.ndarray, window_size: int = 1024) -> np.ndarray:
    """Compute rolling peak envelope.

    Args:
        samples: Audio samples
        window_size: Window size for peak detection

    Returns:
        Array of peak values
    """
    if len(samples) < window_size:
        return np.array([np.max(np.abs(samples))])

    shape = (len(samples) - window_size + 1, window_size)
    strides = (samples.strides[0], samples.strides[0])
    windows = np.lib.stride_tricks.as_strided(samples, shape=shape, strides=strides)
    return np.max(np.abs(windows), axis=1)


def compute_zcr(samples: np.ndarray, window_size: int = 1024) -> np.ndarray:
    """Compute zero crossing rate.

    Args:
        samples: Audio samples
        window_size: Window size for ZCR calculation

    Returns:
        Array of ZCR values (0-1)
    """
    if len(samples) < window_size:
        return np.array([0.0])

    shape = (len(samples) - window_size + 1, window_size)
    strides = (samples.strides[0], samples.strides[0])
    windows = np.lib.stride_tricks.as_strided(samples, shape=shape, strides=strides)

    signs = np.sign(windows)
    zero_crossings = np.sum(np.abs(np.diff(signs, axis=1)) > 0, axis=1)
    return zero_crossings / window_size
