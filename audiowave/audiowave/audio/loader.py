"""Audio file loading and format detection."""

import os
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

from audiowave.audio.types import AudioData
from audiowave.utils.exceptions import (
    AudioLoadError,
    UnsupportedFormatError,
    FileAccessError,
)
from audiowave.utils.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_FORMATS = {".wav", ".mp3", ".flac", ".ogg", ".aiff", ".aif"}


def detect_format(filepath: str) -> str:
    """Detect audio format from file extension.

    Args:
        filepath: Path to audio file

    Returns:
        Lowercase format string (mp3, wav, flac, ogg, aiff)

    Raises:
        UnsupportedFormatError: If format is not supported
    """
    ext = Path(filepath).suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(
            filepath,
            f"Unsupported format '{ext}'. Supported: {', '.join(SUPPORTED_FORMATS)}",
        )
    return ext[1:]


def load_audio(
    filepath: str, mono: bool = False, channel: Optional[int] = None
) -> AudioData:
    """Load audio file and return AudioData object.

    Args:
        filepath: Path to audio file
        mono: Convert to mono by averaging channels
        channel: Specific channel to load (0=left, 1=right). If None, loads all

    Returns:
        AudioData object with loaded audio

    Raises:
        FileAccessError: If file cannot be accessed
        UnsupportedFormatError: If format is not supported
        CorruptedFileError: If file appears corrupted
    """
    path = Path(filepath)

    if not path.exists():
        raise FileAccessError(filepath, "File not found")

    if not os.access(filepath, os.R_OK):
        raise FileAccessError(filepath, "Permission denied")

    audio_format = detect_format(filepath)

    try:
        samples, sample_rate = sf.read(filepath, dtype="float32", always_2d=True)
    except Exception as e:
        logger.error(f"Failed to read audio file: {e}")
        raise AudioLoadError(filepath, f"Failed to decode: {str(e)}")

    if samples.size == 0:
        raise AudioLoadError(filepath, "Audio file is empty")

    channels = samples.shape[1] if samples.ndim > 1 else 1

    if channels == 1:
        samples = samples.squeeze()
    elif channel is not None:
        if channel >= channels:
            raise AudioLoadError(
                filepath, f"Channel {channel} not found (file has {channels} channels)"
            )
        samples = samples[:, channel]
    elif mono:
        samples = np.mean(samples, axis=1)

    duration = len(samples) / sample_rate

    bit_depth = 32

    return AudioData(
        samples=samples,
        sample_rate=sample_rate,
        channels=channels,
        bit_depth=bit_depth,
        duration=duration,
        filepath=str(path.absolute()),
        format=audio_format,
    )


def get_audio_info(filepath: str) -> dict:
    """Get basic audio file information without loading full data.

    Args:
        filepath: Path to audio file

    Returns:
        Dictionary with audio metadata
    """
    try:
        info = sf.info(filepath)
        return {
            "format": info.format,
            "channels": info.channels,
            "sample_rate": info.samplerate,
            "duration": info.duration,
            "frames": info.frames,
            "subtype": info.subtype,
        }
    except Exception as e:
        raise AudioLoadError(filepath, f"Cannot read info: {str(e)}")
