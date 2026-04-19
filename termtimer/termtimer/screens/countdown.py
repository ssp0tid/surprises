"""Countdown timer screen."""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static, Input

from termtimer.models.timer import Timer, TimerState
from termtimer.widgets.time_display import TimeDisplay
from termtimer.widgets.timer_controls import TimerControls
from termtimer.widgets.progress_ring import ProgressRing
from termtimer.services.notifier import Notifier
from termtimer.services.audio import AudioPlayer


class CountdownScreen(Screen):
    """Countdown timer screen."""

    CSS = """
    CountdownScreen {
        align: center middle;
    }

    #timer-container {
        width: 60;
        height: 16;
        align: center middle;
    }

    #time-display {
        text-align: center;
        text-style: bold;
        color: $accent;
    }

    #preset-buttons {
        layout: horizontal;
        align: center middle;
        margin-top: 1;
    }

    .preset-btn {
        width: 8;
    }

    #progress-container {
        align: center middle;
        margin-top: 1;
    }

    #status {
        text-align: center;
        color: $text-muted;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.timer = Timer()
        self.notifier = Notifier()
        self.audio = AudioPlayer()
        self._update_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Compose the countdown screen."""
        yield Container(
            Vertical(
                Static("COUNTDOWN TIMER", id="title"),
                Container(
                    TimeDisplay("00:00:00", id="time-display"),
                    ProgressRing(50, id="progress-ring"),
                    id="timer-container",
                ),
                Static("Press SPACE to start/pause, R to reset", id="status"),
                Horizontal(
                    Button("5m", variant="default", classes="preset-btn"),
                    Button("10m", variant="default", classes="preset-btn"),
                    Button("15m", variant="default", classes="preset-btn"),
                    Button("25m", variant="default", classes="preset-btn"),
                    Button("30m", variant="default", classes="preset-btn"),
                    Button("45m", variant="default", classes="preset-btn"),
                    Button("60m", variant="default", classes="preset-btn"),
                    id="preset-buttons",
                ),
                TimerControls(id="controls"),
            ),
        )

    def on_mount(self) -> None:
        """Handle screen mount."""
        self._start_timer_tick()

    def _start_timer_tick(self) -> None:
        """Start the timer tick loop."""
        async def tick_loop():
            while True:
                await asyncio.sleep(1)
                await self.timer.tick()
                self._update_display()
                if self.timer.is_completed:
                    await self._on_timer_complete()

        self._update_task = asyncio.create_task(tick_loop())

    def _update_display(self) -> None:
        """Update the time display."""
        time_display = self.query_one("#time-display", TimeDisplay)
        time_display.update_time(self.timer.format_time())

        progress_ring = self.query_one("#progress-ring", ProgressRing)
        progress_ring.update_progress(self.timer.progress)

        status = self.query_one("#status", Static)
        if self.timer.state == TimerState.RUNNING:
            status.update("Running...")
        elif self.timer.state == TimerState.PAUSED:
            status.update("Paused - Press SPACE to resume")
        elif self.timer.state == TimerState.COMPLETED:
            status.update("Complete! Press R to reset")
        else:
            status.update("Press SPACE to start")

    async def _on_timer_complete(self) -> None:
        """Handle timer completion."""
        await self.notifier.notify("Timer Complete!", "Your countdown timer has finished.")
        await self.audio.play_alarm()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle preset button presses."""
        button_label = event.button.label
        if button_label:
            minutes = int(button_label.replace("m", ""))
            self.timer.set_duration(minutes=minutes)
            self._update_display()

    def key_space(self) -> None:
        """Handle spacebar to start/pause."""
        if self.timer.state == TimerState.IDLE or self.timer.state == TimerState.COMPLETED:
            self.timer.start()
        elif self.timer.state == TimerState.RUNNING:
            self.timer.pause()
        elif self.timer.state == TimerState.PAUSED:
            self.timer.resume()
        self._update_display()

    def key_r(self) -> None:
        """Handle R key to reset."""
        self.timer.reset()
        self._update_display()

    def key_q(self) -> None:
        """Handle Q key to quit."""
        if self._update_task:
            self._update_task.cancel()
        self.app.action_quit()

    def on_screen_resume(self) -> None:
        """Handle screen resume."""
        self._update_display()