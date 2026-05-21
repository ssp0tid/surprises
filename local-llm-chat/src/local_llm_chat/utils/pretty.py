"""Pretty output utilities - status indicators and spinners."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from rich.console import Console
from rich.live import Live
from rich.style import Style
from rich.text import Text

if TYPE_CHECKING:
    from collections.abc import Generator


class StatusIndicator:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def success(self, message: str) -> None:
        self.console.print(
            Text("✓ ", style=Style(color="green", bold=True))
            + Text(message, style=Style(color="white"))
        )

    def error(self, message: str) -> None:
        self.console.print(
            Text("✗ ", style=Style(color="red", bold=True))
            + Text(message, style=Style(color="white"))
        )

    def warning(self, message: str) -> None:
        self.console.print(
            Text("⚠ ", style=Style(color="yellow", bold=True))
            + Text(message, style=Style(color="white"))
        )

    def info(self, message: str) -> None:
        self.console.print(
            Text("i ", style=Style(color="blue", bold=True))
            + Text(message, style=Style(color="white"))
        )


class Spinner:
    _frames = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    def __init__(
        self,
        message: str = "Loading...",
        console: Console | None = None,
    ) -> None:
        self.message = message
        self.console = console or Console()
        self._live: Live | None = None
        self._frame_index = 0

    def __enter__(self) -> Spinner:
        self._live = Live(
            self._render_frame(),
            console=self.console,
            transient=False,
            refresh_per_second=20,
        )
        self._live.start()
        return self

    def __exit__(self, exc_type: type, exc_val: BaseException, exc_tb: object) -> None:
        if self._live:
            self._live.stop()

    def spin(self) -> None:
        """Advance to the next spinner frame."""
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        if self._live:
            self._live.update(self._render_frame())

    def _render_frame(self) -> Text:
        frame = self._frames[self._frame_index]
        return Text(
            f"{frame} {self.message}",
            style=Style(color="cyan"),
        )


@contextmanager
def spinner_context(
    message: str = "Loading...",
    console: Console | None = None,
) -> Generator[Spinner, None, None]:
    """Context manager for a temporary spinner."""
    spinner = Spinner(message=message, console=console)
    try:
        yield spinner.__enter__()
    finally:
        spinner.__exit__(None, None, None)
