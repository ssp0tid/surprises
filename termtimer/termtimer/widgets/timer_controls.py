"""Timer controls widget."""

from textual.widgets import Button
from textual.containers import Horizontal


class TimerControls(Horizontal):
    """Start/Pause/Reset buttons for timer controls."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._start_button = Button("Start", variant="primary", id="start-btn")
        self._pause_button = Button("Pause", variant="default", id="pause-btn")
        self._reset_button = Button("Reset", variant="default", id="reset-btn")

    def on_mount(self) -> None:
        """Handle widget mount."""
        self.mount(self._start_button)
        self.mount(self._pause_button)
        self.mount(self._reset_button)

    def set_start_mode(self) -> None:
        """Set controls to start mode."""
        self._start_button.disabled = False
        self._pause_button.disabled = True

    def set_running_mode(self) -> None:
        """Set controls to running mode."""
        self._start_button.disabled = True
        self._pause_button.disabled = False

    def set_paused_mode(self) -> None:
        """Set controls to paused mode."""
        self._start_button.disabled = False
        self._pause_button.disabled = True

    def set_completed_mode(self) -> None:
        """Set controls to completed mode."""
        self._start_button.disabled = False
        self._pause_button.disabled = True