"""Beat detection using energy envelope."""

import numpy as np
from scipy import signal

from audiowave.audio.types import AudioData, BeatInfo
from audiowave.utils.exceptions import InsufficientDataError
from audiowave.utils.logging import get_logger

logger = get_logger(__name__)


def detect_beats(
    audio_data: AudioData,
    sensitivity: float = 1.0,
    min_bpm: float = 60,
    max_bpm: float = 200,
) -> BeatInfo:
    """Detect beats using energy envelope method.

    Args:
        audio_data: Loaded audio data
        sensitivity: Detection sensitivity (0.1-2.0, higher = more beats)
        min_bpm: Minimum BPM to detect
        max_bpm: Maximum BPM to detect

    Returns:
        BeatInfo with detected beats and tempo
    """
    samples = audio_data.samples

    if len(samples) < 1024:
        raise InsufficientDataError("Not enough audio for beat detection")

    sample_rate = audio_data.sample_rate

    energy = compute_energy_envelope(samples, sample_rate)

    onset_times, onset_strengths = detect_onsets(energy, sample_rate, sensitivity)

    if len(onset_times) < 2:
        return BeatInfo(
            beats=onset_times,
            bpm=0.0,
            confidence=0.0,
            energy_envelope=energy,
            onset_times=onset_times,
        )

    bpm, confidence = estimate_tempo(onset_times, sample_rate, min_bpm, max_bpm)

    if bpm < min_bpm:
        bpm *= 2
    if bpm > max_bpm:
        bpm /= 2

    onset_times = onset_times[onset_times > 0]
    onset_times = onset_times[onset_times < audio_data.duration - 0.1]

    return BeatInfo(
        beats=onset_times,
        bpm=bpm,
        confidence=confidence,
        energy_envelope=energy,
        onset_times=onset_times,
    )


def compute_energy_envelope(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    """Compute energy envelope for beat detection.

    Args:
        samples: Audio samples
        sample_rate: Sample rate in Hz

    Returns:
        Energy envelope array
    """
    window_size = int(sample_rate * 0.02)

    if len(samples) < window_size:
        return np.array([np.sum(samples**2)])

    shape = (len(samples) - window_size + 1, window_size)
    strides = (samples.strides[0], samples.strides[0])
    windows = np.lib.stride_tricks.as_strided(samples, shape=shape, strides=strides)

    energy = np.sum(windows**2, axis=1)

    energy = signal.resample(energy, len(energy) // 4)

    energy = np.convolve(energy, np.ones(5) / 5, mode="smooth")

    return energy


def detect_onsets(
    energy: np.ndarray, sample_rate: int, sensitivity: float = 1.0
) -> tuple:
    """Detect onset times from energy envelope.

    Args:
        energy: Energy envelope
        sample_rate: Original sample rate
        sensitivity: Detection sensitivity

    Returns:
        Tuple of (onset_times, onset_strengths)
    """
    resample_factor = 4

    diff = np.diff(energy)
    diff = np.append(diff, 0)

    threshold = np.mean(diff) + sensitivity * np.std(diff)

    onsets = diff > threshold

    onset_indices = np.where(onsets)[0]

    onset_times = onset_indices * resample_factor / sample_rate
    onset_strengths = diff[onset_indices]

    return onset_times, onset_strengths


def estimate_tempo(
    onset_times: np.ndarray, sample_rate: int, min_bpm: float = 60, max_bpm: float = 200
) -> tuple:
    """Estimate BPM from onset times.

    Args:
        onset_times: Array of onset timestamps
        sample_rate: Sample rate (for converting to time)
        min_bpm: Minimum BPM
        max_bpm: Maximum BPM

    Returns:
        Tuple of (estimated_bpm, confidence)
    """
    if len(onset_times) < 2:
        return 0.0, 0.0

    inter_onsets = np.diff(onset_times)
    inter_onsets = inter_onsets[inter_onsets > 0]

    if len(inter_onsets) == 0:
        return 0.0, 0.0

    inter_onsets = inter_onsets[inter_onsets < 5.0]

    if len(inter_onsets) == 0:
        return 0.0, 0.0

    bpm_candidates = 60.0 / inter_onsets
    bpm_candidates = bpm_candidates[
        (bpm_candidates >= min_bpm) & (bpm_candidates <= max_bpm)
    ]

    if len(bpm_candidates) == 0:
        median_bpm = np.median(60.0 / inter_onsets)
        while median_bpm < min_bpm:
            median_bpm *= 2
        while median_bpm > max_bpm:
            median_bpm /= 2
        return float(median_bpm), 0.3

    hist, bin_edges = np.histogram(bpm_candidates, bins=50, range=(min_bpm, max_bpm))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    peak_idx = np.argmax(hist)
    bpm = bin_centers[peak_idx]

    confidence = min(1.0, hist[peak_idx] / max(1, len(bpm_candidates) * 0.5))

    return float(bpm), float(confidence)
