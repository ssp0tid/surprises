"""Alarm model with scheduling."""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Callable, Awaitable
from datetime import datetime, time, timedelta


class AlarmRepeat(Enum):
    """Alarm repeat options."""
    ONCE = auto()
    DAILY = auto()
    WEEKDAYS = auto()
    WEEKENDS = auto()


@dataclass
class Alarm:
    """
    Alarm with scheduling and snooze functionality.
    """

    label: str = "Alarm"
    hour: int = 0
    minute: int = 0
    repeat: AlarmRepeat = AlarmRepeat.ONCE
    sound_path: str = ""
    enabled: bool = True
    snooze_minutes: int = 5
    _snooze_until: datetime | None = field(default=None, repr=False)
    _on_trigger: Callable[[], Awaitable[None]] | None = field(default=None, repr=False)

    @property
    def time_str(self) -> str:
        """Get alarm time as string HH:MM."""
        return f"{self.hour:02d}:{self.minute:02d}"

    @property
    def repeat_str(self) -> str:
        """Get repeat setting as string."""
        if self.repeat == AlarmRepeat.ONCE:
            return "Once"
        elif self.repeat == AlarmRepeat.DAILY:
            return "Daily"
        elif self.repeat == AlarmRepeat.WEEKDAYS:
            return "Weekdays"
        elif self.repeat == AlarmRepeat.WEEKENDS:
            return "Weekends"
        return "Unknown"

    @property
    def is_snoozed(self) -> bool:
        """Check if alarm is currently snoozed."""
        if self._snooze_until is None:
            return False
        return datetime.now() < self._snooze_until

    def get_next_trigger_time(self) -> datetime | None:
        """Calculate the next trigger time for the alarm."""
        now = datetime.now()
        alarm_time = time(self.hour, self.minute)

        # Check if currently snoozed
        if self.is_snoozed and self._snooze_until:
            return self._snooze_until

        # Find next occurrence
        for days_ahead in range(8):  # Check up to a week ahead
            candidate = now + timedelta(days=days_ahead)
            candidate_date = candidate.date()
            candidate_datetime = datetime.combine(candidate_date, alarm_time)

            if candidate_datetime <= now:
                continue

            if self._should_trigger_on(candidate_date):
                return candidate_datetime

        return None

    def _should_trigger_on(self, date: datetime.date) -> bool:
        """Check if alarm should trigger on given date."""
        weekday = date.weekday()  # 0 = Monday, 6 = Sunday

        if self.repeat == AlarmRepeat.ONCE:
            return True
        elif self.repeat == AlarmRepeat.DAILY:
            return True
        elif self.repeat == AlarmRepeat.WEEKDAYS:
            return weekday < 5  # Monday to Friday
        elif self.repeat == AlarmRepeat.WEEKENDS:
            return weekday >= 5  # Saturday and Sunday

        return True

    def snooze(self) -> None:
        """Snooze the alarm for configured duration."""
        self._snooze_until = datetime.now() + timedelta(minutes=self.snooze_minutes)

    def cancel_snooze(self) -> None:
        """Cancel any active snooze."""
        self._snooze_until = None

    async def trigger(self) -> None:
        """Trigger the alarm."""
        self.cancel_snooze()
        if self._on_trigger:
            await self._on_trigger()

    def set_trigger_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Set callback to be called when alarm triggers."""
        self._on_trigger = callback

    def to_dict(self) -> dict:
        """Serialize alarm to dictionary."""
        return {
            "label": self.label,
            "hour": self.hour,
            "minute": self.minute,
            "repeat": self.repeat.name,
            "sound_path": self.sound_path,
            "enabled": self.enabled,
            "snooze_minutes": self.snooze_minutes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alarm":
        """Deserialize alarm from dictionary."""
        repeat = AlarmRepeat[data.get("repeat", "ONCE")]
        alarm = cls(
            label=data.get("label", "Alarm"),
            hour=data.get("hour", 0),
            minute=data.get("minute", 0),
            repeat=repeat,
            sound_path=data.get("sound_path", ""),
            enabled=data.get("enabled", True),
            snooze_minutes=data.get("snooze_minutes", 5),
        )
        return alarm