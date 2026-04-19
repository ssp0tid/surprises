"""Time display widget."""

from textual.widgets import Static


class TimeDisplay(Static):
    """Large monospace time display widget."""

    def __init__(self, time_str: str = "00:00:00", **kwargs) -> None:
        super().__init__(time_str, **kwargs)
        self._time_str = time_str

    def update_time(self, time_str: str) -> None:
        """Update the displayed time."""
        self._time_str = time_str
        self.update(time_str)

    def update_styles(self, styles: str) -> None:
        """Update the widget styles."""
        self.styles.color = styles

    @property
    def time_str(self) -> str:
        """Get current time string."""
        return self._time_str