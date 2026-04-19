"""Pause screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Static
from textual.containers import Container


class PauseScreen(Container):
    """Pause overlay screen."""

    class Resume:
        pass

    class Restart:
        pass

    class Quit:
        pass

    BINDINGS = [
        Binding("escape", "resume", "Resume", show=False),
        Binding("r", "restart", "Restart", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the pause UI."""
        with Container(id="pause-content"):
            yield Static("╔═══════════════╗", id="pause-header")
            yield Static("║    PAUSED     ║", id="pause-title")
            yield Static("╚═══════════════╝", id="pause-footer")
            yield Button("Resume", id="btn-resume")
            yield Button("Restart", id="btn-restart")
            yield Button("Quit to Menu", id="btn-quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        match event.button.id:
            case "btn-resume":
                self.post_message(PauseScreen.Resume())
            case "btn-restart":
                self.post_message(PauseScreen.Restart())
            case "btn-quit":
                self.post_message(PauseScreen.Quit())

    def action_resume(self) -> None:
        """Resume game."""
        self.post_message(PauseScreen.Resume())

    def action_restart(self) -> None:
        """Restart game."""
        self.post_message(PauseScreen.Restart())

    def action_quit(self) -> None:
        """Quit to menu."""
        self.post_message(PauseScreen.Quit())
