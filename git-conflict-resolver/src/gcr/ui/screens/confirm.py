"""Confirmation and error screens."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static
from textual.containers import Center, Vertical


class ConfirmScreen(Screen):
    """Generic confirmation dialog."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }

    #dialog {
        width: 50;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 2 4;
    }

    #message {
        width: 100%;
        text-align: center;
        margin-bottom: 2;
    }

    #buttons {
        width: 100%;
        layout: horizontal;
        align: center middle;
    }
    """

    BINDINGS = [
        ("enter", "confirm", "Confirm"),
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self, message: str = "Confirm?", confirm_label: str = "Yes", cancel_label: str = "No"
    ):
        super().__init__()
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label
        self.result: bool = False

    def compose(self) -> ComposeResult:
        yield Header("Confirm")
        with Center():
            with Vertical(id="dialog"):
                yield Static(self.message, id="message")
                with Vertical(id="buttons"):
                    yield Button(self.confirm_label, id="btn-confirm", variant="primary")
                    yield Button(self.cancel_label, id="btn-cancel", variant="error")
        yield Footer()

    def action_confirm(self) -> None:
        self.result = True
        self.app.pop()

    def action_cancel(self) -> None:
        self.result = False
        self.app.pop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            self.action_confirm()
        elif event.button.id == "btn-cancel":
            self.action_cancel()


class ErrorScreen(Screen):
    """Error display screen."""

    CSS = """
    ErrorScreen {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: auto;
        border: solid $error;
        background: $surface;
        padding: 2 4;
    }

    #title {
        text: $error;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }

    #message {
        width: 100%;
        text-align: center;
        margin-bottom: 2;
    }

    #suggestion {
        text: $text-muted;
        width: 100%;
        text-align: center;
    }
    """

    BINDINGS = [
        ("enter", "dismiss", "Dismiss"),
        ("b", "dismiss", "Back"),
    ]

    def __init__(self, title: str = "Error", message: str = "", suggestion: str = ""):
        super().__init__()
        self.error_title = title
        self.message = message
        self.suggestion = suggestion

    def compose(self) -> ComposeResult:
        yield Header(self.error_title)
        with Center():
            with Vertical(id="dialog"):
                yield Static(self.error_title, id="title")
                yield Static(self.message, id="message")
                if self.suggestion:
                    yield Static(self.suggestion, id="suggestion")
                yield Button("Dismiss", id="btn-dismiss", variant="primary")

    def action_dismiss(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.action_dismiss()
