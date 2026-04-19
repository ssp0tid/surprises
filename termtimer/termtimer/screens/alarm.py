"""Alarm screen."""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static, Input

from termtimer.models.alarm import Alarm, AlarmRepeat
from termtimer.services.notifier import Notifier
from termtimer.services.audio import AudioPlayer
from termtimer.services.storage import Storage


from datetime import datetime


class AlarmScreen(Screen):
    """Alarm clock screen with scheduling."""

    CSS = """
    AlarmScreen {
        align: center middle;
    }

    #alarm-container {
        width: 60;
        height: 20;
        align: center middle;
    }

    #time-input {
        text-align: center;
        text-style: bold;
        color: $warning;
    }

    #alarm-list {
        width: 60;
        height: 8;
        border: solid $text-muted;
        margin-top: 1;
    }

    #status {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.notifier = Notifier()
        self.audio = AudioPlayer()
        self.storage = Storage()
        self.alarms: list[Alarm] = []
        self._alarm_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Compose the alarm screen."""
        yield Container(
            Vertical(
                Static("ALARM CLOCK", id="title"),
                Container(
                    Static("00:00", id="time-input"),
                    id="alarm-container",
                ),
                Horizontal(
                    Button("Set Alarm", variant="primary", id="set-btn"),
                    Button("Snooze", variant="default", id="snooze-btn"),
                    Button("Clear", variant="default", id="clear-btn"),
                ),
                Static("Current alarm: Not set", id="status"),
                Container(id="alarm-list"),
                Static("Press SPACE to set alarm, S to snooze, C to clear", id="hint"),
            ),
        )

    def on_mount(self) -> None:
        """Handle screen mount."""
        self._load_alarms()
        self._start_alarm_check()

    def _load_alarms(self) -> None:
        """Load alarms from storage."""
        try:
            alarms_data = self.storage.load_alarms()
            self.alarms = [Alarm.from_dict(d) for d in alarms_data]
        except Exception:
            self.alarms = []
        self._update_display()

    def _save_alarms(self) -> None:
        """Save alarms to storage."""
        try:
            alarms_data = [a.to_dict() for a in self.alarms]
            self.storage.save_alarms(alarms_data)
        except Exception:
            pass

    def _start_alarm_check(self) -> None:
        """Start the alarm check loop."""
        async def check_loop():
            while True:
                await asyncio.sleep(1)
                self._check_alarms()

        self._alarm_task = asyncio.create_task(check_loop())

    def _check_alarms(self) -> None:
        """Check if any alarm should trigger."""
        now = datetime.now()
        for alarm in self.alarms:
            if not alarm.enabled:
                continue

            next_time = alarm.get_next_trigger_time()
            if next_time:
                # Check if we should trigger (within 1 second window)
                time_diff = (next_time - now).total_seconds()
                if 0 <= time_diff <= 1:
                    asyncio.create_task(self._trigger_alarm(alarm))

    async def _trigger_alarm(self, alarm: Alarm) -> None:
        """Trigger an alarm."""
        await self.notifier.notify(
            alarm.label,
            f"Alarm at {alarm.time_str}"
        )
        await self.audio.play_alarm()

    def _update_display(self) -> None:
        """Update the display."""
        if self.alarms:
            alarm = self.alarms[0]
            time_display = self.query_one("#time-input", Static)
            time_display.update(alarm.time_str)
            status = self.query_one("#status", Static)
            status.update(f"Alarm: {alarm.label} ({alarm.repeat_str})")
        else:
            time_display = self.query_one("#time-input", Static)
            time_display.update("00:00")
            status = self.query_one("#status", Static)
            status.update("No alarm set")

    def key_space(self) -> None:
        """Handle spacebar to set alarm."""
        # Cycle through preset times: 6:00, 7:00, 8:00, 9:00, etc.
        if not self.alarms:
            alarm = Alarm(hour=6, minute=0, label="Wake up")
            alarm.set_trigger_callback(self._on_alarm_triggered)
            self.alarms.append(alarm)
        else:
            alarm = self.alarms[0]
            alarm.hour = (alarm.hour + 1) % 24

        self._save_alarms()
        self._update_display()

    def key_s(self) -> None:
        """Handle S key to snooze."""
        if self.alarms:
            self.alarms[0].snooze()
            status = self.query_one("#status", Static)
            status.update("Snoozed for 5 minutes")
            self._save_alarms()

    def key_c(self) -> None:
        """Handle C key to clear alarm."""
        if self.alarms:
            self.alarms.clear()
            self._save_alarms()
            self._update_display()

    def key_q(self) -> None:
        """Handle Q key to quit."""
        if self._alarm_task:
            self._alarm_task.cancel()
        self.app.action_quit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id == "set-btn":
            self.key_space()
        elif button_id == "snooze-btn":
            self.key_s()
        elif button_id == "clear-btn":
            self.key_c()

    async def _on_alarm_triggered(self) -> None:
        """Handle alarm triggered callback."""
        pass

    def on_screen_resume(self) -> None:
        """Handle screen resume."""
        self._update_display()