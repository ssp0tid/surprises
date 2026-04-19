"""ASCII art rendering widget."""

from textual.widgets import Static


class ASCIIArtWidget(Static):
    """Widget for rendering ASCII art with proper formatting."""

    def __init__(self, art: str, *, color: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._art = art
        self._color = color

    def render(self) -> str:
        """Render the ASCII art."""
        if self._color:
            return f"[{self._color}]{self._art}[/{self._color}]"
        return self._art
