"""High scores screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Static
from textual.containers import Container, VerticalScroll


class HighScoresScreen(Container):
    """High scores display screen."""

    class Back:
        pass

    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("enter", "back", "Back", show=False),
    ]

    def __init__(self, scores: list[tuple[str, int]] | None = None) -> None:
        super().__init__()
        self._scores = scores or []

    def update_scores(self, scores: list[tuple[str, int]]) -> None:
        """Update the displayed scores."""
        self._scores = scores

    def compose(self) -> ComposeResult:
        """Compose the high scores UI."""
        yield Static(
            """
╔═══════════════════════╗
║     HIGH SCORES       ║
╚═══════════════════════╝
            """,
            id="scores-title",
        )

        with VerticalScroll(id="scores-container"):
            if self._scores:
                for i, (name, score) in enumerate(self._scores):
                    rank = f"{i + 1}."
                    yield Static(
                        f"  {rank:<3} {name:<20} {score:>8}",
                        classes="score-entry",
                    )
            else:
                yield Static(
                    "    No high scores yet!",
                    classes="score-entry",
                )

        yield Button("BACK", id="btn-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "btn-back":
            self.post_message(HighScoresScreen.Back())

    def action_back(self) -> None:
        """Go back."""
        self.post_message(HighScoresScreen.Back())
