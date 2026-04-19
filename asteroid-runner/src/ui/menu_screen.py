"""Main menu screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Static
from textual.containers import Container, VerticalScroll


class MenuScreen(Container):
    """Main menu screen with ASCII art title and navigation."""

    class StartGame:
        pass

    class ShowHighScores:
        pass

    class QuitGame:
        pass

    BINDINGS = [
        Binding("w", "menu_up", "Move up", show=False),
        Binding("s", "menu_down", "Move down", show=False),
        Binding("up", "menu_up", "Move up", show=False),
        Binding("down", "menu_down", "Move down", show=False),
        Binding("enter", "menu_select", "Select", show=False),
        Binding("escape", "app.bell", "Cancel", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._selected_index = 0
        self._menu_items = ["START GAME", "HIGH SCORES", "QUIT"]

    def compose(self) -> ComposeResult:
        """Compose the menu UI."""
        yield Static(
            """
╔════════════════════════════════════╗
║      ╔═══╗ ╔═══╗ ╔═══╗            ║
║      ║ A ║═║ S ║═║ T ║            ║
║      ╚═══╝ ╚═══╝ ╚═══╝            ║
║   ╔═══════════════════════════╗    ║
║   ║   ASTEROID RUNNER         ║    ║
║   ╚═══════════════════════════╝    ║
║       ~ Space Shooter ~            ║
╚════════════════════════════════════╝
            """,
            id="title-art",
            classes="title",
        )

        yield Static(
            """
    ▲
   /|\\
  / | \\
            """,
            id="ship-art",
            classes="ship",
        )

        with VerticalScroll(id="menu-container"):
            for i, item in enumerate(self._menu_items):
                yield Button(
                    item,
                    id=f"menu-{i}",
                    classes="menu-item selected" if i == 0 else "menu-item",
                )

        yield Static(
            "[WASD/Arrows] Navigate  •  [Enter] Select  •  [Esc] Quit",
            id="controls-hint",
            classes="hint",
        )

    def action_menu_up(self) -> None:
        """Move selection up."""
        self._selected_index = (self._selected_index - 1) % len(self._menu_items)
        self._update_selection()

    def action_menu_down(self) -> None:
        """Move selection down."""
        self._selected_index = (self._selected_index + 1) % len(self._menu_items)
        self._update_selection()

    def action_menu_select(self) -> None:
        """Activate selected menu item."""
        actions = [self.StartGame, self.ShowHighScores, self.QuitGame]
        action_class = actions[self._selected_index]

        if action_class == self.StartGame:
            self.post_message(StartGameEvent())
        elif action_class == self.ShowHighScores:
            self.post_message(ShowHighScoresEvent())
        elif action_class == self.QuitGame:
            self.post_message(QuitGameEvent())

    def _update_selection(self) -> None:
        """Update the visual state of menu items."""
        for i, _ in enumerate(self._menu_items):
            button = self.query_one(f"#menu-{i}", Button)
            if i == self._selected_index:
                button.set_class(True, "selected")
            else:
                button.set_class(False, "selected")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button click."""
        button_id = event.button.id
        if button_id and button_id.startswith("menu-"):
            self._selected_index = int(button_id.split("-")[1])
            self.action_menu_select()


class StartGameEvent:
    """Request to start a new game."""

    pass


class ShowHighScoresEvent:
    """Request to show high scores."""

    pass


class QuitGameEvent:
    """Request to quit the application."""

    pass
