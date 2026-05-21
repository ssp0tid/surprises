"""Spectrum analysis using FFT."""

from typing import Optional
import numpy as np
from scipy import signal

from audiowave.audio.types import AudioData, SpectrumData
from audiowave.utils.exceptions import InsufficientDataError
from audiowave.utils.logging import get_logger

logger = get_logger(__name__)

WINDOW_FUNCTIONS = {
    "hann": signal.windows.hann,
    "hamming": signal.windows.hamming,
    "blackman": signal.windows.blackman,
}


def compute_spectrum(
    audio_data: AudioData,
    window_type: str = "hann",
    fft_size: Optional[int] = None,
    log_scale: bool = True,
) -> SpectrumData:
    """Compute frequency spectrum using FFT.

    Args:
        audio_data: Loaded audio data
        window_type: Window function (hann, hamming, blackman)
        fft_size: FFT size (defaults to next power of 2 >= sample rate)
        log_scale: Use logarithmic magnitude scale

    Returns:
        SpectrumData with frequency and magnitude information
    """
    samples = audio_data.samples

    if len(samples) == 0:
        raise InsufficientDataError("No audio samples for spectrum analysis")

    if fft_size is None:
        fft_size = 2 ** int(np.ceil(np.log2(audio_data.sample_rate)))

    fft_size = min(fft_size, len(samples))

    if window_type not in WINDOW_FUNCTIONS:
        logger.warning(f"Unknown window type '{window_type}', using hann")
        window_type = "hann"

    window = WINDOW_FUNCTIONS[window_type](fft_size)

    if len(samples) >= fft_size:
        segment = samples[:fft_size]
    else:
        segment = np.pad(samples, (0, fft_size - len(samples)))

    windowed = segment * window

    fft_result = np.fft.rfft(windowed)

    frequencies = np.fft.rfftfreq(fft_size, 1.0 / audio_data.sample_rate)

    magnitudes = np.abs(fft_result)

    if log_scale:
        magnitudes_db = 20 * np.log10(magnitudes + 1e-10)
    else:
        magnitudes_db = magnitudes

    return SpectrumData(
        frequencies=frequencies,
        magnitudes=magnitudes,
        magnitudes_db=magnitudes_db,
        sample_rate=audio_data.sample_rate,
        window_type=window_type,
    )


def compute_spectrogram(
    audio_data: AudioData,
    fft_size: int = 2048,
    hop_size: int = 512,
    window_type: str = "hann",
) -> tuple:
    """Compute spectrogram for time-frequency visualization.

    Args:
        audio_data: Loaded audio data
        fft_size: FFT window size
        hop_size: Hop size between windows
        window_type: Window function

    Returns:
        Tuple of (frequencies, times, spectrogram_db)
    """
    if window_type not in WINDOW_FUNCTIONS:
        window_type = "hann"

    window = WINDOW_FUNCTIONS[window_type](fft_size)

    frequencies, times, spec = signal.spectrogram(
        audio_data.samples,
        fs=audio_data.sample_rate,
        window=window,
        nperseg=fft_size,
        noverlap=fft_size - hop_size,
        scaling="density",
    )

    spec_db = 10 * np.log10(spec + 1e-10)

    return frequencies, times, spec_db


def get_frequency_bands(
    spectrum: SpectrumData, num_bands: int = 64, log_scale: bool = True
) -> tuple:
    """Group frequencies into bands for bar visualization.

    Args:
        spectrum: Spectrum data
        num_bands: Number of frequency bands
        log_scale: Use logarithmic frequency spacing

    Returns:
        Tuple of (band_centers, band_magnitudes)
    """
    freqs = spectrum.frequencies
    mags = spectrum.magnitudes_db

    valid_idx = freqs > 0
    freqs = freqs[valid_idx]
    mags = mags[valid_idx]

    if len(freqs) == 0:
        return np.array([]), np.array([])

    min_freq = freqs[0]
    max_freq = freqs[-1]

    if log_scale:
        band_edges = np.logspace(np.log10(min_freq), np.log10(max_freq), num_bands + 1)
    else:
        band_edges = np.linspace(min_freq, max_freq, num_bands + 1)

    band_centers = (band_edges[:-1] + band_edges[1:]) / 2

    band_mags = []
    for i in range(num_bands):
        mask = (freqs >= band_edges[i]) & (freqs < band_edges[i + 1])
        if np.any(mask):
            band_mags.append(np.max(mags[mask]))
        else:
            band_mags.append(-100.0)

    return band_centers, np.array(band_mags)
