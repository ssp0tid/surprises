"""Timing utilities for the game loop."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeltaTimer:
    """
    Accumulates time for fixed timestep updates.

    Usage:
        timer = DeltaTimer()
        timer.start()

        while running:
            dt = timer.tick()  # Returns elapsed since last tick
            if dt is not None:
                update(dt)  # Fixed timestep update
    """

    fixed_dt: float = 1.0 / 60.0
    accumulator: float = 0.0
    _last_time: float = 0.0
    _running: bool = False

    def start(self) -> None:
        """Start the timer."""
        self._last_time = self._get_time()
        self.accumulator = 0.0
        self._running = True

    def stop(self) -> None:
        """Stop the timer."""
        self._running = False

    def tick(self) -> Optional[float]:
        """
        Call each frame to accumulate time.

        Returns:
            The accumulated time if it exceeds fixed_dt, None otherwise.
            Call this repeatedly until it returns None for fixed timestep updates.
        """
        if not self._running:
            return None

        current_time = self._get_time()
        frame_time = current_time - self._last_time
        self._last_time = current_time

        # Clamp to prevent spiral of death
        if frame_time > 0.25:
            frame_time = 0.25

        self.accumulator += frame_time

        if self.accumulator >= self.fixed_dt:
            self.accumulator -= self.fixed_dt
            return self.fixed_dt

        return None

    def get_accumulator(self) -> float:
        """Get current accumulator value."""
        return self.accumulator

    def reset_accumulator(self) -> None:
        """Reset accumulator to zero."""
        self.accumulator = 0.0

    @staticmethod
    def _get_time() -> float:
        """Get high-resolution time."""
        return time.perf_counter()


@dataclass
class FPSTracker:
    """
    Tracks frames per second with rolling average.

    Usage:
        tracker = FPSTracker()
        while running:
            tracker.start_frame()
            render()
            tracker.end_frame()
            print(f"FPS: {tracker.fps}")
    """

    sample_size: int = 60
    _frame_times: deque[float] = field(default_factory=lambda: deque(maxlen=60))
    _frame_start: float = 0.0
    _fps: float = 60.0

    def start_frame(self) -> None:
        """Mark the start of a frame."""
        self._frame_start = time.perf_counter()

    def end_frame(self) -> None:
        """Mark the end of a frame and update FPS."""
        frame_time = time.perf_counter() - self._frame_start
        self._frame_times.append(frame_time)

        if self._frame_times:
            avg_time = sum(self._frame_times) / len(self._frame_times)
            if avg_time > 0:
                self._fps = 1.0 / avg_time

    @property
    def fps(self) -> float:
        """Get current FPS."""
        return self._fps

    @property
    def frame_time_ms(self) -> float:
        """Get average frame time in milliseconds."""
        if self._frame_times:
            return (sum(self._frame_times) / len(self._frame_times)) * 1000
        return 0.0

    @property
    def min_fps(self) -> float:
        """Get minimum FPS from samples."""
        if self._frame_times:
            max_time = max(self._frame_times)
            return 1.0 / max_time if max_time > 0 else 0.0
        return 0.0

    @property
    def max_fps(self) -> float:
        """Get maximum FPS from samples."""
        if self._frame_times:
            min_time = min(self._frame_times)
            return 1.0 / min_time if min_time > 0 else 0.0
        return 0.0

    def reset(self) -> None:
        """Reset all tracking data."""
        self._frame_times.clear()
        self._fps = 60.0
        self._frame_start = 0.0


class Stopwatch:
    """
    Simple stopwatch for measuring elapsed time.

    Usage:
        stopwatch = Stopwatch()
        stopwatch.start()
        do_something()
        elapsed = stopwatch.elapsed()  # Seconds since start
        stopwatch.stop()
        do_something_else()
        total = stopwatch.total()  # Total time including pauses
    """

    _start_time: float = 0.0
    _stop_time: float = 0.0
    _running: bool = False
    _total_paused: float = 0.0

    def start(self) -> None:
        """Start the stopwatch."""
        if not self._running:
            self._start_time = time.perf_counter()
            self._running = True
            self._total_paused = 0.0

    def stop(self) -> float:
        """Stop the stopwatch and return elapsed time."""
        if self._running:
            self._stop_time = time.perf_counter()
            self._running = False
        return self.elapsed()

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self._running:
            return time.perf_counter() - self._start_time - self._total_paused
        return self._stop_time - self._start_time - self._total_paused

    def pause(self) -> None:
        """Pause the stopwatch."""
        if self._running:
            self._stop_time = time.perf_counter()
            self._running = False

    def resume(self) -> None:
        """Resume the stopwatch."""
        if not self._running:
            self._total_paused += time.perf_counter() - self._stop_time
            self._running = True

    def reset(self) -> None:
        """Reset the stopwatch."""
        self._start_time = 0.0
        self._stop_time = 0.0
        self._running = False
        self._total_paused = 0.0

    @property
    def is_running(self) -> bool:
        """Check if stopwatch is running."""
        return self._running
