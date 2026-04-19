"""Health bar widget."""

from textual.widgets import Static


class HealthBar(Static):
    """Widget for displaying a health bar."""

    def __init__(
        self,
        current: int = 100,
        maximum: int = 100,
        width: int = 10,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._current = current
        self._maximum = maximum
        self._width = width

    def update(self, current: int, maximum: int) -> None:
        """Update the health bar values."""
        self._current = current
        self._maximum = maximum

    def render(self) -> str:
        """Render the health bar."""
        ratio = max(0.0, min(1.0, self._current / max(1, self._maximum)))
        filled = int(ratio * self._width)
        empty = self._width - filled
        return f"[green]{'█' * filled}[red]{'░' * empty}[/]"
