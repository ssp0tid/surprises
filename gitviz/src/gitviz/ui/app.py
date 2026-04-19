"""Main TUI application."""

from pathlib import Path
from typing import Optional

from textual.app import App
from textual.binding import Binding
from textual.driver import Driver
from textual.screen import Screen

from ..models.repository import Repository
from ..parser.repository_loader import RepositoryLoader
from .screens.main_screen import MainScreen
from .screens.diff_screen import DiffScreen


class GitVizApp(App):
    """Main TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #graph-panel {
        height: 70%;
        border: solid $primary;
    }

    #detail-panel {
        height: 25%;
        border: solid $secondary;
    }

    #search-bar {
        height: 3;
        background: $surface-darken-1;
    }

    #status-bar {
        height: 3;
        background: $surface-darken-1;
    }

    .commit-row {
        width: 100%;
        padding: 0 1;
    }

    .commit-row.selected {
        background: $primary;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(
        self,
        repo_path: Path,
        *,
        max_commits: Optional[int] = None,
        driver_class: Optional[type[Driver]] = None,
        size: Optional[tuple[int, int]] = None,
        title: str = "GitViz",
    ):
        super().__init__(driver_class, size, title)
        self.repo_path = repo_path
        self.max_commits = max_commits
        self.repository: Repository | None = None
        self._loading = False

    async def on_mount(self) -> None:
        """Initialize application after mount."""
        await self.load_repository()
        self.push_screen(MainScreen(self))

    async def load_repository(self) -> None:
        """Load git repository data."""
        self._loading = True
        try:
            loader = RepositoryLoader()
            self.repository = await loader.load(
                self.repo_path,
                max_commits=self.max_commits,
            )
        except Exception as e:
            self.exit(message=f"Error loading repository: {e}")
        finally:
            self._loading = False

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


async def run_app(
    repo_path: Path,
    *,
    max_commits: Optional[int] = None,
) -> None:
    """Run the GitViz application."""
    app = GitVizApp(repo_path, max_commits=max_commits)
    await app.run_async()
