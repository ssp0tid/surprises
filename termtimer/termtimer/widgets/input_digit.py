"""Input digit widget for time input."""

from textual.widgets import Input
from textual.message import Message


class InputDigit(Input):
    """Digit input for setting time (hours, minutes, seconds)."""

    def __init__(self, max_length: int = 2, **kwargs) -> None:
        super().__init__(**kwargs)
        self.max_length = max_length
        self._value = ""

    def on_mount(self) -> None:
        """Handle widget mount."""
        self.styles.width = self.max_length + 2

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input change."""
        # Filter to only digits
        filtered = "".join(c for c in event.value if c.isdigit())
        if len(filtered) > self.max_length:
            filtered = filtered[:self.max_length]
        self._value = filtered
        event.value = filtered

    @property
    def value(self) -> int:
        """Get numeric value."""
        try:
            return int(self._value) if self._value else 0
        except ValueError:
            return 0

    def set_value(self, value: int) -> None:
        """Set numeric value."""
        self._value = str(value)
        self.update(self._value)


class InputDigitComplete(Message):
    """Message sent when digit input is complete."""

    def __init__(self, value: int, input_id: str) -> None:
        super().__init__()
        self.value = value
        self.input_id = input_id