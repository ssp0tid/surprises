"""Animated text widget."""

import time
from textual.widgets import Static


class AnimatedText(Static):
    """Widget for displaying animated text effects."""

    def __init__(
        self,
        text: str,
        animation_type: str = "none",
        speed: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._text = text
        self._animation_type = animation_type
        self._speed = speed
        self._start_time = time.time()

    def update_text(self, text: str) -> None:
        """Update the displayed text."""
        self._text = text
        self._start_time = time.time()

    def render(self) -> str:
        """Render the animated text."""
        elapsed = time.time() - self._start_time

        if self._animation_type == "blink":
            if int(elapsed * 2 * self._speed) % 2 == 0:
                return self._text
            return ""

        elif self._animation_type == "fade":
            alpha = min(1.0, elapsed * self._speed)
            return self._text

        elif self._animation_type == "slide":
            offset = max(0, int((1 - min(1.0, elapsed * self._speed)) * 20))
            return " " * offset + self._text

        return self._text
