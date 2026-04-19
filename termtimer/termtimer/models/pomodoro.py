"""Pomodoro session model."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Awaitable


class PomodoroPhase(Enum):
    """Pomodoro phases."""
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()
    IDLE = auto()


@dataclass
class PomodoroSession:
    """
    Pomodoro session manager.

    Manages work intervals, short breaks, long breaks, and session counting.
    """

    work_duration: int = 25 * 60  # 25 minutes in seconds
    short_break_duration: int = 5 * 60  # 5 minutes
    long_break_duration: int = 15 * 60  # 15 minutes
    pomodoros_until_long_break: int = 4

    phase: PomodoroPhase = PomodoroPhase.IDLE
    remaining_seconds: float = 0.0
    completed_pomodoros: int = 0
    _on_phase_complete: Callable[[PomodoroPhase], Awaitable[None]] | None = field(default=None, repr=False)

    @property
    def current_duration(self) -> int:
        """Get duration for current phase."""
        if self.phase == PomodoroPhase.WORK:
            return self.work_duration
        elif self.phase == PomodoroPhase.SHORT_BREAK:
            return self.short_break_duration
        elif self.phase == PomodoroPhase.LONG_BREAK:
            return self.long_break_duration
        return 0

    @property
    def progress(self) -> float:
        """Get progress as percentage (0.0 to 1.0)."""
        duration = self.current_duration
        if duration == 0:
            return 0.0
        completed = duration - self.remaining_seconds
        return completed / duration

    @property
    def is_running(self) -> bool:
        """Check if session is active."""
        return self.phase in (PomodoroPhase.WORK, PomodoroPhase.SHORT_BREAK, PomodoroPhase.LONG_BREAK)

    @property
    def is_idle(self) -> bool:
        """Check if session is idle."""
        return self.phase == PomodoroPhase.IDLE

    def start_work(self) -> None:
        """Start a work phase."""
        self.phase = PomodoroPhase.WORK
        self.remaining_seconds = float(self.work_duration)

    def start_short_break(self) -> None:
        """Start a short break."""
        self.phase = PomodoroPhase.SHORT_BREAK
        self.remaining_seconds = float(self.short_break_duration)

    def start_long_break(self) -> None:
        """Start a long break."""
        self.phase = PomodoroPhase.LONG_BREAK
        self.remaining_seconds = float(self.long_break_duration)

    def start(self) -> None:
        """Start the pomodoro session (work phase)."""
        self.start_work()

    def pause(self) -> None:
        """Pause the current phase (not fully implemented for pomodoro)."""
        pass

    def resume(self) -> None:
        """Resume the current phase (not fully implemented for pomodoro)."""
        pass

    def reset(self) -> None:
        """Reset the session to idle."""
        self.phase = PomodoroPhase.IDLE
        self.remaining_seconds = 0.0
        self.completed_pomodoros = 0

    async def tick(self) -> None:
        """Tick the session forward by one second."""
        if self.is_running and self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.remaining_seconds <= 0:
                self.remaining_seconds = 0
                await self._complete_phase()

    async def _complete_phase(self) -> None:
        """Handle phase completion."""
        completed_phase = self.phase

        if self.phase == PomodoroPhase.WORK:
            self.completed_pomodoros += 1
            # Determine next break type
            if self.completed_pomodoros % self.pomodoros_until_long_break == 0:
                self.start_long_break()
            else:
                self.start_short_break()
        else:
            # After any break, start work
            self.start_work()

        if self._on_phase_complete:
            await self._on_phase_complete(completed_phase)

    def format_time(self) -> str:
        """Format remaining time as MM:SS."""
        seconds = int(self.remaining_seconds)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_phase_label(self) -> str:
        """Get human-readable phase label."""
        if self.phase == PomodoroPhase.WORK:
            return "WORK"
        elif self.phase == PomodoroPhase.SHORT_BREAK:
            return "SHORT BREAK"
        elif self.phase == PomodoroPhase.LONG_BREAK:
            return "LONG BREAK"
        return "IDLE"