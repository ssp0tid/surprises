"""Manual trigger handler."""

from typing import Any, Callable


class ManualTrigger:
    def __init__(self, callback: Callable[[dict[str, Any] | None], None]):
        self.callback = callback

    def trigger(self, payload: dict[str, Any] | None = None):
        self.callback(payload)
