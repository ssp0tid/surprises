"""Search bar widget."""

from textual import events
from textual.message import Message
from textual.widget import Widget


class SearchBar(Widget):
    """Search input widget."""

    class SearchSubmit(Message):
        def __init__(self, query: str) -> None:
            super().__init__()
            self.query = query

    class SearchClear(Message):
        pass

    def __init__(self):
        super().__init__(id="search-bar")
        self.query: str = ""
        self.is_active: bool = False
        self._cursor_pos: int = 0

    def focus(self) -> None:
        """Focus the search bar."""
        self.is_active = True
        self.query = ""
        self._cursor_pos = 0
        self.refresh()

    def blur(self) -> None:
        """Blur the search bar."""
        self.is_active = False
        self.refresh()

    def render(self) -> str:
        """Render the search bar."""
        prefix = "/ "
        if self.is_active:
            return f"{prefix}{self.query}_"
        return f"{prefix}Press / to search..."

    def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        if not self.is_active:
            return

        if event.key == "escape":
            self.blur()
            self.post_message(self.SearchClear())
        elif event.key == "enter":
            self.post_message(self.SearchSubmit(self.query))
        elif event.key == "backspace":
            if self.query:
                self.query = self.query[:-1]
                self._cursor_pos = max(0, self._cursor_pos - 1)
                self.post_message(self.SearchSubmit(self.query))
        elif event.key == "left":
            self._cursor_pos = max(0, self._cursor_pos - 1)
        elif event.key == "right":
            self._cursor_pos = min(len(self.query), self._cursor_pos + 1)
        elif len(event.key) == 1:
            self.query += event.key
            self._cursor_pos += 1
            self.post_message(self.SearchSubmit(self.query))

        self.refresh()
