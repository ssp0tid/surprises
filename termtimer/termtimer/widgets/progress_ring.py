"""Progress ring widget."""

from textual.widgets import Static


class ProgressRing(Static):
    """ASCII/Unicode progress ring indicator."""

    def __init__(self, progress: float = 0.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self._progress = progress
        self._update_display()

    def update_progress(self, progress: float) -> None:
        """Update the progress (0.0 to 1.0)."""
        self._progress = max(0.0, min(1.0, progress))
        self._update_display()

    def _update_display(self) -> None:
        """Update the progress ring display."""
        percentage = int(self._progress * 100)
        
        # Create a visual progress bar
        bar_width = 20
        filled = int(bar_width * self._progress)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        self.update(f"[{bar}] {percentage}%")

    @property
    def progress(self) -> float:
        """Get current progress."""
        return self._progress