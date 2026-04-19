"""Timer model with state machine."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Awaitable
import asyncio


class TimerState(Enum):
    """Timer states."""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()


@dataclass
class Timer:
    """
    Countdown timer with state machine.

    States: IDLE → RUNNING ⇄ PAUSED → COMPLETED
                     ↓
                   RESET → IDLE
    """

    duration_seconds: int = 0
    remaining_seconds: float = 0.0
    state: TimerState = TimerState.IDLE
    _task: asyncio.Task | None = field(default=None, repr=False)
    _on_complete: Callable[[], Awaitable[None]] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize timer after construction."""
        self.remaining_seconds = float(self.duration_seconds)

    @property
    def progress(self) -> float:
        """Get timer progress as percentage (0.0 to 1.0)."""
        if self.duration_seconds == 0:
            return 0.0
        completed = self.duration_seconds - self.remaining_seconds
        return completed / self.duration_seconds

    @property
    def is_running(self) -> bool:
        """Check if timer is running."""
        return self.state == TimerState.RUNNING

    @property
    def is_paused(self) -> bool:
        """Check if timer is paused."""
        return self.state == TimerState.PAUSED

    @property
    def is_completed(self) -> bool:
        """Check if timer is completed."""
        return self.state == TimerState.COMPLETED

    @property
    def is_idle(self) -> bool:
        """Check if timer is idle."""
        return self.state == TimerState.IDLE

    def set_duration(self, hours: int = 0, minutes: int = 0, seconds: int = 0) -> None:
        """Set timer duration."""
        total_seconds = hours * 3600 + minutes * 60 + seconds
        self.duration_seconds = total_seconds
        self.remaining_seconds = float(total_seconds)
        if self.state == TimerState.COMPLETED:
            self.state = TimerState.IDLE

    def start(self, on_complete: Callable[[], Awaitable[None]] | None = None) -> None:
        """Start the timer."""
        if self.state == TimerState.IDLE or self.state == TimerState.COMPLETED:
            self.remaining_seconds = float(self.duration_seconds)
        if self.remaining_seconds > 0:
            self.state = TimerState.RUNNING
            self._on_complete = on_complete

    def pause(self) -> None:
        """Pause the timer."""
        if self.state == TimerState.RUNNING:
            self.state = TimerState.PAUSED

    def resume(self) -> None:
        """Resume a paused timer."""
        if self.state == TimerState.PAUSED:
            self.state = TimerState.RUNNING

    def reset(self) -> None:
        """Reset the timer to idle state."""
        self.state = TimerState.IDLE
        self.remaining_seconds = float(self.duration_seconds)
        self._task = None

    async def tick(self) -> None:
        """Tick the timer forward by one second."""
        if self.state == TimerState.RUNNING and self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.remaining_seconds <= 0:
                self.remaining_seconds = 0
                self.state = TimerState.COMPLETED
                if self._on_complete:
                    await self._on_complete()

    def format_time(self) -> str:
        """Format remaining time as HH:MM:SS."""
        seconds = int(self.remaining_seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"