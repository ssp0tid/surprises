"""Debug utilities for development and testing."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum, auto

import textual.logging

logger = textual.logging.get_logger()


class DebugLevel(Enum):
    """Debug output levels."""

    NONE = auto()
    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    DEBUG = auto()
    TRACE = auto()


@dataclass
class DebugConfig:
    """Configuration for debug features."""

    enabled: bool = False
    level: DebugLevel = DebugLevel.INFO
    show_fps: bool = True
    show_positions: bool = False
    show_collision_bounds: bool = False
    show_entity_count: bool = True
    log_performance: bool = True
    performance_threshold_ms: float = 16.67  # 60 FPS = 16.67ms per frame


@dataclass
class DebugStats:
    """Runtime statistics for debugging."""

    frames: int = 0
    updates: int = 0
    dropped_frames: int = 0
    entities_created: int = 0
    entities_destroyed: int = 0
    collisions_checked: int = 0
    collisions_detected: int = 0
    last_update_time: float = 0.0
    last_render_time: float = 0.0
    _custom_stats: dict[str, Any] = field(default_factory=dict)

    def reset(self) -> None:
        """Reset all stats."""
        self.frames = 0
        self.updates = 0
        self.dropped_frames = 0
        self.entities_created = 0
        self.entities_destroyed = 0
        self.collisions_checked = 0
        self.collisions_detected = 0
        self.last_update_time = 0.0
        self.last_render_time = 0.0
        self._custom_stats.clear()


class Debugger:
    """
    Centralized debug utilities.

    Usage:
        debugger = Debugger()

        # Enable debug mode
        debugger.enable(level=DebugLevel.DEBUG)

        # Track performance
        with debugger.profile("update"):
            game.update(dt)

        # Log debug info
        debugger.log("Player position", player.pos)

        # Check if debug is enabled
        if debugger.enabled:
            render_debug_overlay()
    """

    def __init__(self) -> None:
        self._config = DebugConfig()
        self._stats = DebugStats()
        self._profiler_stack: list[tuple[str, float]] = []

    @property
    def config(self) -> DebugConfig:
        """Get debug configuration."""
        return self._config

    @property
    def stats(self) -> DebugStats:
        """Get debug statistics."""
        return self._stats

    @property
    def enabled(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config.enabled

    def enable(self, level: DebugLevel = DebugLevel.DEBUG) -> None:
        """Enable debug mode."""
        self._config.enabled = True
        self._config.level = level
        logger.info(f"Debug mode enabled at level {level.name}")

    def disable(self) -> None:
        """Disable debug mode."""
        self._config.enabled = False
        logger.info("Debug mode disabled")

    def set_level(self, level: DebugLevel) -> None:
        """Set debug level."""
        self._config.level = level

    def log(self, *args: Any, level: DebugLevel = DebugLevel.INFO) -> None:
        """Log a debug message if enabled."""
        if not self._config.enabled:
            return

        if level.value <= self._config.level.value:
            message = " ".join(str(arg) for arg in args)
            logger.log(self._level_to_logging(level), message)

    def trace(self, *args: Any) -> None:
        """Log a trace message."""
        self.log(*args, level=DebugLevel.TRACE)

    def debug(self, *args: Any) -> None:
        """Log a debug message."""
        self.log(*args, level=DebugLevel.DEBUG)

    def info(self, *args: Any) -> None:
        """Log an info message."""
        self.log(*args, level=DebugLevel.INFO)

    def warning(self, *args: Any) -> None:
        """Log a warning message."""
        self.log(*args, level=DebugLevel.WARNING)

    def error(self, *args: Any) -> None:
        """Log an error message."""
        self.log(*args, level=DebugLevel.ERROR)

    def profile(self, name: str) -> "ProfileContext":
        """Context manager for profiling code blocks."""
        return ProfileContext(self, name)

    def tick(self) -> None:
        """Called each frame for stats tracking."""
        self._stats.frames += 1

    def update(self) -> None:
        """Called each update for stats tracking."""
        self._stats.updates += 1

    def frame_dropped(self) -> None:
        """Record a dropped frame."""
        self._stats.dropped_frames += 1

    def entity_created(self) -> None:
        """Record entity creation."""
        self._stats.entities_created += 1

    def entity_destroyed(self) -> None:
        """Record entity destruction."""
        self._stats.entities_destroyed += 1

    def collision_checked(self, count: int = 1) -> None:
        """Record collision checks."""
        self._stats.collisions_checked += count

    def collision_detected(self, count: int = 1) -> None:
        """Record collision detections."""
        self._stats.collisions_detected += count

    def set_custom_stat(self, name: str, value: Any) -> None:
        """Set a custom statistic."""
        self._stats._custom_stats[name] = value

    def get_custom_stat(self, name: str) -> Any:
        """Get a custom statistic."""
        return self._stats._custom_stats.get(name)

    def get_summary(self) -> str:
        """Get a formatted summary of debug stats."""
        if not self._config.enabled:
            return "Debug mode disabled"

        stats = self._stats
        uptime = stats.frames / 60.0  # Assuming 60 FPS

        lines = [
            f"=== Debug Stats ===",
            f"Uptime: {uptime:.1f}s",
            f"Frames: {stats.frames} ({stats.frames / uptime:.1f} FPS avg)",
            f"Updates: {stats.updates}",
            f"Dropped: {stats.dropped_frames}",
            f"Entities: {stats.entities_created - stats.entities_destroyed} active",
            f"Created: {stats.entities_created}",
            f"Destroyed: {stats.entities_destroyed}",
            f"Collisions: {stats.collisions_checked} checked, {stats.collisions_detected} detected",
        ]

        if stats._custom_stats:
            lines.append("Custom Stats:")
            for name, value in stats._custom_stats.items():
                lines.append(f"  {name}: {value}")

        return "\n".join(lines)

    @staticmethod
    def _level_to_logging(level: DebugLevel) -> int:
        """Convert DebugLevel to logging level."""
        mapping = {
            DebugLevel.NONE: logging.CRITICAL + 1,
            DebugLevel.ERROR: logging.ERROR,
            DebugLevel.WARNING: logging.WARNING,
            DebugLevel.INFO: logging.INFO,
            DebugLevel.DEBUG: logging.DEBUG,
            DebugLevel.TRACE: 5,  # Below DEBUG
        }
        return mapping.get(level, logging.INFO)


class ProfileContext:
    """Context manager for profiling code blocks."""

    def __init__(self, debugger: Debugger, name: str) -> None:
        self._debugger = debugger
        self._name = name
        self._start_time: float = 0.0

    def __enter__(self) -> "ProfileContext":
        import time

        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        import time

        elapsed_ms = (time.perf_counter() - self._start_time) * 1000

        if self._debugger._config.log_performance:
            if elapsed_ms > self._debugger._config.performance_threshold_ms:
                self._debugger.warning(f"Performance: {self._name} took {elapsed_ms:.2f}ms")
            else:
                self._debugger.trace(f"Performance: {self._name} took {elapsed_ms:.2f}ms")


# Global debugger instance
_debugger: Optional[Debugger] = None


def get_debugger() -> Debugger:
    """Get the global debugger instance."""
    global _debugger
    if _debugger is None:
        _debugger = Debugger()
        # Check for DEBUG environment variable
        if os.environ.get("DEBUG"):
            _debugger.enable()
    return _debugger


def debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    return get_debugger().enabled
