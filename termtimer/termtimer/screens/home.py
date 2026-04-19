"""Home screen with mode selection."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Static, Label


class HomeScreen(Screen):
    """Home screen displaying mode selection."""

    CSS = """
    HomeScreen {
        align: center middle;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }

    .mode-grid {
        layout: grid;
        grid-size: 3 2;
        grid-gutter: 1 1;
        align: center middle;
    }

    .mode-button {
        width: 20;
        height: 5;
        margin: 1;
    }

    #countdown-btn { color: $accent; }
    #stopwatch-btn { color: $text; }
    #pomodoro-btn { color: $success; }
    #alarm-btn { color: $warning; }

    .mode-button:hover {
        background: $surface;
    }

    #footer-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 2;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the home screen."""
        yield Container(
            Static("TERMTIMER", id="title"),
            Vertical(
                Horizontal(
                    Button("COUNTDOWN", id="countdown-btn", variant="default"),
                    Button("STOPWATCH", id="stopwatch-btn", variant="default"),
                    Button("POMODORO", id="pomodoro-btn", variant="default"),
                    classes="mode-grid",
                ),
                Horizontal(
                    Button("ALARM", id="alarm-btn", variant="default"),
                    classes="mode-grid",
                ),
                Static("Press 1-4 or click to select mode | Press q to quit", id="footer-hint"),
            ),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press to navigate to selected mode."""
        button_id = event.button.id
        if button_id == "countdown-btn":
            self.app.action_switch_mode("countdown")
        elif button_id == "stopwatch-btn":
            self.app.action_switch_mode("stopwatch")
        elif button_id == "pomodoro-btn":
            self.app.action_switch_mode("pomodoro")
        elif button_id == "alarm-btn":
            self.app.action_switch_mode("alarm")