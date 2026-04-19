"""Stopwatch screen."""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static

from termtimer.models.stopwatch import Stopwatch, StopwatchState
from termtimer.widgets.time_display import TimeDisplay
from termtimer.services.audio import AudioPlayer


class StopwatchScreen(Screen):
    """Stopwatch screen with lap functionality."""

    CSS = """
    StopwatchScreen {
        align: center middle;
    }

    #timer-container {
        width: 60;
        height: 12;
        align: center middle;
    }

    #time-display {
        text-align: center;
        text-style: bold;
        color: $text;
    }

    #laps-container {
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

    .lap-row {
        height: 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.stopwatch = Stopwatch()
        self.audio = AudioPlayer()
        self._update_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Compose the stopwatch screen."""
        yield Container(
            Vertical(
                Static("STOPWATCH", id="title"),
                Container(
                    TimeDisplay("00:00:00.000", id="time-display"),
                    id="timer-container",
                ),
                Static("Press SPACE to start/stop, L for lap, R to reset", id="status"),
                Horizontal(
                    Button("Start", variant="primary", id="start-btn"),
                    Button("Lap", variant="default", id="lap-btn"),
                    Button("Reset", variant="default", id="reset-btn"),
                ),
                Container(id="laps-container"),
            ),
        )

    def on_mount(self) -> None:
        """Handle screen mount."""
        self._start_timer_tick()

    def _start_timer_tick(self) -> None:
        """Start the timer tick loop."""
        async def tick_loop():
            while True:
                await asyncio.sleep(0.01)  # 10ms for smooth updates
                await self.stopwatch.tick(0.01)
                self._update_display()

        self._update_task = asyncio.create_task(tick_loop())

    def _update_display(self) -> None:
        """Update the time display."""
        time_display = self.query_one("#time-display", TimeDisplay)
        time_display.update_time(self.stopwatch.format_short_time())

        status = self.query_one("#status", Static)
        if self.stopwatch.state == StopwatchState.RUNNING:
            status.update("Running - Press SPACE to stop, L for lap")
        elif self.stopwatch.state == StopwatchState.STOPPED:
            status.update("Stopped - Press SPACE to resume, R to reset")
        else:
            status.update("Press SPACE to start")

    def _update_laps(self) -> None:
        """Update the laps display."""
        laps_container = self.query_one("#laps-container", Container)
        laps_container.remove_children()

        if self.stopwatch.laps:
            # Show last 8 laps
            laps_to_show = self.stopwatch.laps[-8:]
            for lap in laps_to_show:
                lap_text = f"Lap {lap.number}: {lap.formatted_lap_time}  |  Total: {lap.formatted_total_time}"
                laps_container.mount(Static(lap_text, classes="lap-row"))

    def key_space(self) -> None:
        """Handle spacebar to start/stop."""
        if self.stopwatch.state == StopwatchState.IDLE:
            self.stopwatch.start()
        elif self.stopwatch.state == StopwatchState.RUNNING:
            self.stopwatch.stop()
        elif self.stopwatch.state == StopwatchState.STOPPED:
            self.stopwatch.resume()
        self._update_display()

    def key_l(self) -> None:
        """Handle L key to record lap."""
        if self.stopwatch.state == StopwatchState.RUNNING:
            self.stopwatch.lap()
            self._update_laps()

    def key_r(self) -> None:
        """Handle R key to reset."""
        self.stopwatch.reset()
        self._update_display()
        self._update_laps()

    def key_s(self) -> None:
        """Handle S key to stop (alias for space when running)."""
        if self.stopwatch.state == StopwatchState.RUNNING:
            self.stopwatch.stop()
            self._update_display()

    def key_q(self) -> None:
        """Handle Q key to quit."""
        if self._update_task:
            self._update_task.cancel()
        self.app.action_quit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id == "start-btn":
            self.key_space()
        elif button_id == "lap-btn":
            self.key_l()
        elif button_id == "reset-btn":
            self.key_r()

    def on_screen_resume(self) -> None:
        """Handle screen resume."""
        self._update_display()