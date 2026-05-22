from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text


class BarChart(Widget):

    DEFAULT_CSS = """
    BarChart {
        height: 1fr;
        min-height: 10;
    }
    """

    array: reactive[list[int]] = reactive(list, recompose=True)
    highlighted: reactive[list[int]] = reactive(list, recompose=True)
    sorted_indices: reactive[set[int]] = reactive(set, recompose=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.array = []
        self.highlighted = []
        self.sorted_indices = set()

    def update_state(self, array: list[int], highlighted: list[int], sorted_indices: set[int] | None = None) -> None:
        self.array = array
        self.highlighted = highlighted
        self.sorted_indices = sorted_indices or set()
        self.refresh()

    def render(self) -> Text:
        if not self.array:
            return Text("No data")

        height = self.size.height
        width = self.size.width
        max_val = max(self.array) if self.array else 1
        n = len(self.array)

        bar_width = max(1, width // n)
        available_bars = width // bar_width

        lines = []
        for row in range(height):
            line = Text()
            threshold = max_val * (height - row) / height
            for i in range(min(n, available_bars)):
                if self.array[i] >= threshold:
                    if i in self.highlighted:
                        style = "bold red"
                    elif i in self.sorted_indices:
                        style = "green"
                    else:
                        style = "cyan"
                    line.append("█" * bar_width, style=style)
                else:
                    line.append(" " * bar_width)
            lines.append(line)

        result = Text()
        for i, line in enumerate(lines):
            result.append_text(line)
            if i < len(lines) - 1:
                result.append("\n")
        return result
