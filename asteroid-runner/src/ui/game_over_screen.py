"""Game over screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Static
from textual.containers import Container


class GameOverScreen(Container):
    """Game over screen with score display and high score notification."""

    class PlayAgain:
        pass

    class MainMenu:
        pass

    BINDINGS = [
        Binding("enter", "play_again", "Play Again", show=False),
        Binding("escape", "main_menu", "Main Menu", show=False),
    ]

    def __init__(
        self,
        score: int = 0,
        level: int = 1,
        kills: int = 0,
        is_high_score: bool = False,
    ) -> None:
        super().__init__()
        self._score = score
        self._level = level
        self._kills = kills
        self._is_high_score = is_high_score

    def compose(self) -> ComposeResult:
        """Compose the game over UI."""
        with Container(id="gameover-container"):
            yield Static(
                """
╔═══════════════════════╗
║      GAME OVER        ║
╚═══════════════════════╝
                """,
                id="gameover-title",
            )

            yield Static(
                f"""
╔═══════════════════════╗
║                       ║
║    SCORE: {self._score:05d}     ║
║    LEVEL: {self._level:02d}        ║
║    KILLS: {self._kills:03d}        ║
║                       ║
╚═══════════════════════╝
                """,
                id="gameover-stats",
            )

            if self._is_high_score:
                yield Static(
                    "★ ★ ★ NEW HIGH SCORE! ★ ★ ★",
                    id="high-score-banner",
                    classes="highlight",
                )

            yield Button("PLAY AGAIN", id="btn-play-again")
            yield Button("MAIN MENU", id="btn-main-menu")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        match event.button.id:
            case "btn-play-again":
                self.post_message(GameOverScreen.PlayAgain())
            case "btn-main-menu":
                self.post_message(GameOverScreen.MainMenu())

    def action_play_again(self) -> None:
        """Play again."""
        self.post_message(GameOverScreen.PlayAgain())

    def action_main_menu(self) -> None:
        """Return to main menu."""
        self.post_message(GameOverScreen.MainMenu())
