"""Main game screen."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator
from dataclasses import dataclass

from textual.app import RenderResult
from textual.widget import Widget
from textual.scrollbar import ScrollBarTheme

if TYPE_CHECKING:
    from ..game.engine import GameEngine


@dataclass
class RenderLayer:
    """A single layer of rendered entities for sorting."""

    entities: list["Entity"]


class GameScreen(Widget):
    """Main game rendering widget using Textual's chunked rendering."""

    COLORS = {
        "white": "\x1b[37m",
        "bright_green": "\x1b[92m",
        "bright_cyan": "\x1b[96m",
        "bright_red": "\x1b[91m",
        "bright_yellow": "\x1b[93m",
        "yellow": "\x1b[33m",
        "red": "\x1b[31m",
        "cyan": "\x1b[36m",
        "reset": "\x1b[0m",
        "bold": "\x1b[1m",
    }

    def __init__(self, engine: "GameEngine | None" = None) -> None:
        super().__init__()
        self._engine = engine
        self._framebuffer: list[list[str]] = []
        self._dirty = True

    def set_engine(self, engine: "GameEngine") -> None:
        """Set the game engine."""
        self._engine = engine

    def on_mount(self) -> None:
        """Initialize renderer on mount."""
        self.update_scrollbar_theme(ScrollBarTheme())

    def render(self) -> RenderResult:
        """Main render method called by Textual."""
        if not self._engine or not self._engine.is_running:
            yield from self._render_empty()
            return

        self._update_framebuffer()

        for row in self._framebuffer:
            yield "".join(row)
            yield "\n"

    def _render_empty(self) -> Iterator[str]:
        """Render empty state."""
        if self.size.width > 0:
            for _ in range(self.size.height):
                yield " " * self.size.width
                yield "\n"
        else:
            yield ""

    def _update_framebuffer(self) -> None:
        """Update the ASCII framebuffer from game state."""
        width = max(1, self.size.width)
        height = max(1, self.size.height)

        self._framebuffer = [[" " for _ in range(width)] for _ in range(height)]

        if not self._engine or not self._engine.context:
            return

        context = self._engine.context

        entities = sorted(
            context.entities.values(), key=lambda e: e.render.layer if e.render else 0
        )

        if context.player and context.player.active:
            self._render_entity(context.player)

        for entity in entities:
            if entity.active and entity.render:
                self._render_entity(entity)

    def _render_entity(self, entity) -> None:
        """Render a single entity."""
        if not entity.render:
            return

        pos = entity.position
        art = entity.render.ascii_art
        color = entity.render.color

        screen_x = int(pos.x)
        screen_y = int(pos.y)

        for dy, line in enumerate(art.split("\n")):
            row = screen_y + dy
            if 0 <= row < len(self._framebuffer):
                for dx, char in enumerate(line):
                    col = screen_x + dx - len(line) // 2
                    if 0 <= col < len(self._framebuffer[0]) and char != " ":
                        cell = self.COLORS.get(color, "") + char + self.COLORS["reset"]
                        self._framebuffer[row][col] = cell

    def clear(self) -> None:
        """Mark renderer as needing full refresh."""
        self._dirty = True
