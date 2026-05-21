"""Welcome screen for GCR."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static
from textual.containers import Center, Vertical


class WelcomeScreen(Screen):
    """Welcome screen shown on application start."""

    CSS = """
    WelcomeScreen {
        align: center middle;
    }

    #welcome-container {
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 2 4;
    }

    #title {
        text: $accent;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #subtitle {
        text: $text-muted;
        text-align: center;
        width: 100%;
        margin-bottom: 2;
    }

    #instructions {
        width: 100%;
        margin-bottom: 2;
    }

    #start-button {
        width: 100%;
    }
    """

    BINDINGS = [
        ("enter", "start", "Start"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="welcome-container"):
                yield Static("Git Conflict Resolver", id="title")
                yield Static("3-way merge made visual", id="subtitle")
                yield Static(
                    "Press [b]Enter[/b] to start resolving conflicts\nPress [b]q[/b] to quit",
                    id="instructions",
                )
                yield Button("Start Resolving", id="start-button", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-button":
            self.action_start()

    def action_start(self) -> None:
        self.app.push_screen("picker")
