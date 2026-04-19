"""Pomodoro timer screen."""

import asyncio
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static

from termtimer.models.pomodoro import PomodoroSession, PomodoroPhase
from termtimer.widgets.time_display import TimeDisplay
from termtimer.widgets.progress_ring import ProgressRing
from termtimer.services.notifier import Notifier
from termtimer.services.audio import AudioPlayer


class PomodoroScreen(Screen):
    """Pomodoro timer screen with work/break cycles."""

    CSS = """
    PomodoroScreen {
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
        color: $success;
    }

    #phase-label {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #session-info {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    #progress-container {
        align: center middle;
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
        self.session = PomodoroSession()
        self.notifier = Notifier()
        self.audio = AudioPlayer()
        self._update_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        """Compose the pomodoro screen."""
        yield Container(
            Vertical(
                Static("POMODORO", id="title"),
                Static("WORK", id="phase-label"),
                Container(
                    TimeDisplay("25:00", id="time-display"),
                    ProgressRing(50, id="progress-ring"),
                    id="timer-container",
                ),
                Static("Session: 0 | Next: Work", id="session-info"),
                Static("Press SPACE to start, R to reset", id="status"),
                Horizontal(
                    Button("Start", variant="primary", id="start-btn"),
                    Button("Reset", variant="default", id="reset-btn"),
                ),
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
                await self.session.tick()
                self._update_display()
                if self.session.phase == PomodoroPhase.IDLE:
                    await self._on_phase_complete(PomodoroPhase.WORK)

        self._update_task = asyncio.create_task(tick_loop())

    def _update_display(self) -> None:
        """Update the display."""
        time_display = self.query_one("#time-display", TimeDisplay)
        time_display.update_time(self.session.format_time())

        progress_ring = self.query_one("#progress-ring", ProgressRing)
        progress_ring.update_progress(self.session.progress)

        phase_label = self.query_one("#phase-label", Static)
        phase_label.update(self.session.get_phase_label())

        # Update color based on phase
        if self.session.phase == PomodoroPhase.WORK:
            time_display.update_styles("color: $success;")
        elif self.session.phase in (PomodoroPhase.SHORT_BREAK, PomodoroPhase.LONG_BREAK):
            time_display.update_styles("color: $accent;")
        else:
            time_display.update_styles("color: $text-muted;")

        session_info = self.query_one("#session-info", Static)
        next_phase = "Work" if self.session.phase in (PomodoroPhase.SHORT_BREAK, PomodoroPhase.LONG_BREAK) else "Break"
        session_info.update(f"Session: {self.session.completed_pomodoros} | Next: {next_phase}")

        status = self.query_one("#status", Static)
        if self.session.is_running:
            status.update("Running... Press SPACE to pause (not implemented)")
        elif self.session.is_idle:
            status.update("Press SPACE to start")
        else:
            status.update("Phase complete!")

    async def _on_phase_complete(self, completed_phase: PomodoroPhase) -> None:
        """Handle phase completion."""
        if completed_phase == PomodoroPhase.WORK:
            await self.notifier.notify(
                "Work Session Complete!",
                f"Great job! You've completed {self.session.completed_pomodoros} pomodoro(s)."
            )
            await self.audio.play_alarm()
        else:
            await self.notifier.notify(
                "Break Complete!",
                "Time to get back to work!"
            )
            await self.audio.play_alarm()

    def key_space(self) -> None:
        """Handle spacebar to start."""
        if self.session.is_idle:
            self.session.start()
        self._update_display()

    def key_r(self) -> None:
        """Handle R key to reset."""
        self.session.reset()
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
        elif button_id == "reset-btn":
            self.key_r()

    def on_screen_resume(self) -> None:
        """Handle screen resume."""
        self._update_display()