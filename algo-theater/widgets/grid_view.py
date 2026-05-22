from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text


class GridView(Widget):

    DEFAULT_CSS = """
    GridView {
        height: 1fr;
        min-height: 10;
    }
    """

    grid: reactive[list[list[int]]] = reactive(list, recompose=True)
    visited: reactive[set[tuple[int, int]]] = reactive(set, recompose=True)
    frontier: reactive[set[tuple[int, int]]] = reactive(set, recompose=True)
    path: reactive[list[tuple[int, int]]] = reactive(list, recompose=True)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.grid = []
        self.visited = set()
        self.frontier = set()
        self.path = []

    def update_state(
        self,
        grid: list[list[int]],
        visited: set[tuple[int, int]],
        frontier: set[tuple[int, int]],
        path: list[tuple[int, int]],
    ) -> None:
        self.grid = grid
        self.visited = visited
        self.frontier = frontier
        self.path = path
        self.refresh()

    def render(self) -> Text:
        if not self.grid:
            return Text("No grid")

        path_set = set(self.path)
        lines = []

        for r, row in enumerate(self.grid):
            line = Text()
            for c, cell in enumerate(row):
                pos = (r, c)
                if cell == 1:
                    line.append("██", style="white")
                elif pos in path_set:
                    line.append("██", style="bold green")
                elif pos in self.frontier:
                    line.append("██", style="yellow")
                elif pos in self.visited:
                    line.append("██", style="blue")
                else:
                    line.append("██", style="dim white")
            lines.append(line)

        result = Text()
        for i, line in enumerate(lines):
            result.append_text(line)
            if i < len(lines) - 1:
                result.append("\n")
        return result
