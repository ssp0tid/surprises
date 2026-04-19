"""Stopwatch model with lap functionality."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List


class StopwatchState(Enum):
    """Stopwatch states."""
    IDLE = auto()
    RUNNING = auto()
    STOPPED = auto()


@dataclass
class Lap:
    """Represents a single lap time."""
    number: int
    time_seconds: float
    lap_time: float

    @property
    def formatted_lap_time(self) -> str:
        """Format lap time as MM:SS.ms."""
        minutes, seconds = divmod(self.lap_time, 60)
        return f"{int(minutes):02d}:{seconds:06.3f}"

    @property
    def formatted_total_time(self) -> str:
        """Format total time as MM:SS.ms."""
        minutes, seconds = divmod(self.time_seconds, 60)
        return f"{int(minutes):02d}:{seconds:06.3f}"


@dataclass
class Stopwatch:
    """
    Stopwatch with lap functionality.
    """

    state: StopwatchState = StopwatchState.IDLE
    elapsed_seconds: float = 0.0
    laps: List[Lap] = field(default_factory=list)
    _last_lap_time: float = 0.0

    @property
    def is_running(self) -> bool:
        """Check if stopwatch is running."""
        return self.state == StopwatchState.RUNNING

    @property
    def is_stopped(self) -> bool:
        """Check if stopwatch is stopped."""
        return self.state == StopwatchState.STOPPED

    @property
    def is_idle(self) -> bool:
        """Check if stopwatch is idle."""
        return self.state == StopwatchState.IDLE

    @property
    def total_laps(self) -> int:
        """Get total number of laps."""
        return len(self.laps)

    def start(self) -> None:
        """Start the stopwatch."""
        if self.state == StopwatchState.IDLE:
            self.state = StopwatchState.RUNNING
            self.elapsed_seconds = 0.0
            self.laps = []
            self._last_lap_time = 0.0

    def stop(self) -> None:
        """Stop the stopwatch."""
        if self.state == StopwatchState.RUNNING:
            self.state = StopwatchState.STOPPED

    def resume(self) -> None:
        """Resume a stopped stopwatch."""
        if self.state == StopwatchState.STOPPED:
            self.state = StopwatchState.RUNNING

    def lap(self) -> Lap | None:
        """Record a lap time."""
        if self.state != StopwatchState.RUNNING:
            return None

        lap_number = len(self.laps) + 1
        lap_time = self.elapsed_seconds - self._last_lap_time
        self._last_lap_time = self.elapsed_seconds

        lap = Lap(
            number=lap_number,
            time_seconds=self.elapsed_seconds,
            lap_time=lap_time
        )
        self.laps.append(lap)
        return lap

    def reset(self) -> None:
        """Reset the stopwatch."""
        self.state = StopwatchState.IDLE
        self.elapsed_seconds = 0.0
        self.laps = []
        self._last_lap_time = 0.0

    async def tick(self, delta: float = 0.01) -> None:
        """Tick the stopwatch forward by delta seconds."""
        if self.state == StopwatchState.RUNNING:
            self.elapsed_seconds += delta

    def format_time(self) -> str:
        """Format elapsed time as HH:MM:SS.ms."""
        hours, remainder = divmod(self.elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

    def format_short_time(self) -> str:
        """Format elapsed time as MM:SS.ms (without hours if < 1 hour)."""
        if self.elapsed_seconds >= 3600:
            return self.format_time()
        minutes, seconds = divmod(self.elapsed_seconds, 60)
        return f"{int(minutes):02d}:{seconds:06.3f}"