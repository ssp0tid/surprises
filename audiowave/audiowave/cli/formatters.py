"""Output formatters for CLI."""

import json
from typing import Any, Dict

from audiowave.audio.types import AudioData, AudioStatistics, BeatInfo


def format_text(
    audio_data: AudioData,
    statistics: AudioStatistics,
    beats: BeatInfo = None,
) -> str:
    """Format audio statistics as human-readable text.

    Args:
        audio_data: Audio data
        statistics: Audio statistics
        beats: Optional beat information

    Returns:
        Formatted text string
    """
    duration = format_duration(statistics.duration)
    channel_str = "Stereo" if statistics.channels == 2 else "Mono"

    lines = [
        f"Audio File: {audio_data.filepath}",
        f"Duration: {duration}",
        f"Sample Rate: {statistics.sample_rate} Hz",
        f"Channels: {statistics.channels} ({channel_str})",
        f"Bit Depth: {statistics.bit_depth}-bit",
        "",
        "Statistics:",
        f"  Peak Amplitude: {statistics.peak_amplitude:.4f}",
        f"  RMS Level: {statistics.rms_db:.2f} dB",
        f"  Crest Factor: {statistics.crest_factor:.2f}",
        f"  Dynamic Range: {statistics.dynamic_range:.2f} dB",
    ]

    if beats is not None and beats.bpm > 0:
        lines.extend(
            [
                "",
                "Beat Detection:",
                f"  BPM: {beats.bpm:.1f}",
                f"  Confidence: {beats.confidence:.2f}",
                f"  Beat Count: {len(beats.beats)}",
            ]
        )

    return "\n".join(lines)


def format_json(
    audio_data: AudioData, statistics: AudioStatistics, beats: BeatInfo = None
) -> str:
    result: Dict[str, Any] = {
        "file": audio_data.filepath,
        "format": audio_data.format,
        "duration": audio_data.duration,
        "sample_rate": audio_data.sample_rate,
        "channels": audio_data.channels,
        "bit_depth": audio_data.bit_depth,
        "statistics": {
            "peak_amplitude": float(statistics.peak_amplitude),
            "rms_level": float(statistics.rms_level),
            "rms_db": float(statistics.rms_db),
            "crest_factor": float(statistics.crest_factor),
            "dynamic_range": float(statistics.dynamic_range),
        },
    }

    if beats is not None:
        result["beats"] = {
            "bpm": float(beats.bpm),
            "confidence": float(beats.confidence),
            "count": len(beats.beats),
            "timestamps": [float(t) for t in beats.beats[:100]],
        }

    return json.dumps(result, indent=2)


def format_duration(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.2f}"
