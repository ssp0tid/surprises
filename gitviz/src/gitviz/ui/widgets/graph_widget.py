"""Graph widget for displaying commit graph."""

from typing import Callable

from rich.text import Text
from textual import events
from textual.message import Message
from textual.scroll_view import ScrollView


class GraphWidget(ScrollView):
    """Displays the commit graph with scrolling support."""

    class RowSelected(Message):
        """Message sent when a row is selected."""

        def __init__(self, row_index: int) -> None:
            super().__init__()
            self.row_index = row_index

    class RowClicked(Message):
        """Message sent when a row is clicked."""

        def __init__(self, row_index: int, x: int, y: int) -> None:
            super().__init__()
            self.row_index = row_index
            self.x = x
            self.y = y

    def __init__(self):
        super().__init__(id="graph-panel")
        self.commit_rows: list[Text] = []
        self.selected_index: int = 0
        self.visible_start: int = 0
        self.visible_height: int = 20
        self.on_select: Callable[[int], None] | None = None
        self._row_height = 1

    def set_rows(self, rows: list[Text]) -> None:
        """Set commit rows to display."""
        self.commit_rows = rows
        self.refresh()

    def set_selected(self, index: int) -> None:
        """Set selected row index."""
        if 0 <= index < len(self.commit_rows):
            self.selected_index = index
            self._ensure_visible()
            self.refresh()

    def _ensure_visible(self) -> None:
        """Ensure selected row is visible."""
        if self.selected_index < self.visible_start:
            self.visible_start = self.selected_index
        elif self.selected_index >= self.visible_start + self.visible_height:
            self.visible_start = self.selected_index - self.visible_height + 1

    def cursor_up(self) -> None:
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
            self._ensure_visible()
            self.refresh()
            if self.on_select:
                self.on_select(self.selected_index)

    def cursor_down(self) -> None:
        """Move selection down."""
        if self.selected_index < len(self.commit_rows) - 1:
            self.selected_index += 1
            self._ensure_visible()
            self.refresh()
            if self.on_select:
                self.on_select(self.selected_index)

    def page_up(self) -> None:
        """Move selection up by page."""
        self.selected_index = max(0, self.selected_index - self.visible_height)
        self.visible_start = max(0, self.visible_start - self.visible_height)
        self.refresh()
        if self.on_select:
            self.on_select(self.selected_index)

    def page_down(self) -> None:
        """Move selection down by page."""
        max_idx = len(self.commit_rows) - 1
        self.selected_index = min(max_idx, self.selected_index + self.visible_height)
        self.visible_start = min(
            max_idx - self.visible_height + 1, self.visible_start + self.visible_height
        )
        self.refresh()
        if self.on_select:
            self.on_select(self.selected_index)

    def go_top(self) -> None:
        """Go to first row."""
        self.selected_index = 0
        self.visible_start = 0
        self.refresh()
        if self.on_select:
            self.on_select(self.selected_index)

    def go_bottom(self) -> None:
        """Go to last row."""
        self.selected_index = len(self.commit_rows) - 1
        self.visible_start = max(0, self.selected_index - self.visible_height + 1)
        self.refresh()
        if self.on_select:
            self.on_select(self.selected_index)

    def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        if event.key == "up":
            self.cursor_up()
        elif event.key == "down":
            self.cursor_down()
        elif event.key == "pageup":
            self.page_up()
        elif event.key == "pagedown":
            self.page_down()
        elif event.key == "home":
            self.go_top()
        elif event.key == "end":
            self.go_bottom()

    def on_click(self, event: events.Click) -> None:
        """Handle click events."""
        row = self.visible_start + event.y // self._row_height
        if 0 <= row < len(self.commit_rows):
            self.selected_index = row
            self.refresh()
            self.post_message(self.RowSelected(row))
