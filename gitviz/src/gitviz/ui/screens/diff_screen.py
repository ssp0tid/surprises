"""Diff viewer screen."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Button, Static


class DiffScreen(Screen):
    """Shows diff for selected commit."""

    def __init__(self, commit_oid: bytes | None = None):
        super().__init__()
        self.commit_oid = commit_oid
        self.diff_content: str = ""

    def compose(self) -> ComposeResult:
        """Compose the diff screen."""
        yield Header()
        yield Static("Diff Viewer", id="diff-title")
        yield Static("Diff content will be displayed here", id="diff-content")
        yield Button("Close", id="close-btn")

    def on_mount(self) -> None:
        """Initialize screen."""
        close_btn = self.query_one("#close-btn", Button)
        close_btn.focus()

    def on_button_pressed(self, event) -> None:
        """Handle button press."""
        if event.button.id == "close-btn":
            self.app.pop_screen()
