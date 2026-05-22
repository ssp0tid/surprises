from textual.containers import Horizontal
from textual.widgets import Button, Select, Static
from textual.widget import Widget


class Controls(Widget):

    DEFAULT_CSS = """
    Controls {
        height: 3;
        dock: bottom;
        layout: horizontal;
        padding: 0 1;
    }
    Controls Button {
        margin: 0 1;
        min-width: 10;
    }
    Controls Select {
        width: 24;
    }
    Controls .speed-label {
        padding: 0 1;
        content-align: center middle;
    }
    """

    def __init__(
        self,
        algorithm_choices: list[tuple[str, str]],
        size_choices: list[tuple[str, int]] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._algorithm_choices = algorithm_choices
        self._size_choices = size_choices

    def compose(self):
        with Horizontal():
            yield Select(
                self._algorithm_choices,
                value=self._algorithm_choices[0][1] if self._algorithm_choices else None,
                id="algo-select",
                prompt="Algorithm",
            )
            if self._size_choices:
                yield Select(
                    self._size_choices,
                    value=self._size_choices[1][1] if len(self._size_choices) > 1 else self._size_choices[0][1],
                    id="size-select",
                    prompt="Size",
                )
            yield Button("▶ Play", id="btn-play", variant="success")
            yield Button("⏸ Pause", id="btn-pause", variant="default")
            yield Button("→ Step", id="btn-step", variant="primary")
            yield Button("↺ Reset", id="btn-reset", variant="warning")
            yield Button("🎲 Random", id="btn-random", variant="default")
            speed_options = [
                ("Fast (10ms)", 10),
                ("Medium (50ms)", 50),
                ("Normal (100ms)", 100),
                ("Slow (200ms)", 200),
                ("Very Slow (500ms)", 500),
            ]
            yield Select(
                speed_options,
                value=100,
                id="speed-select",
                prompt="Speed",
            )
