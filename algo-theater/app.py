from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, Select, Button
from textual.timer import Timer
from collections.abc import Generator

from algorithms import SORTING_ALGORITHMS, SEARCHING_ALGORITHMS, PATHFINDING_ALGORITHMS
from algorithms.pathfinding import PathState
from widgets.bar_chart import BarChart
from widgets.grid_view import GridView
from widgets.controls import Controls
from utils import generate_random_array, generate_sorted_array, generate_grid

import random


class AlgoTheaterApp(App):

    CSS = """
    Screen {
        layout: vertical;
    }
    #stats {
        height: 1;
        dock: top;
        padding: 0 2;
        background: $surface;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        layout: vertical;
    }
    .viz-container {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_play", "Play/Pause"),
        ("s", "step", "Step"),
        ("r", "reset", "Reset"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._playing = False
        self._timer: Timer | None = None
        self._speed_ms = 100
        self._array_size = 20

        self._sort_array: list[int] = []
        self._sort_gen: Generator | None = None
        self._sort_algo_name = "Bubble Sort"

        self._search_array: list[int] = []
        self._search_target: int = 0
        self._search_gen: Generator | None = None
        self._search_algo_name = "Linear Search"

        self._grid: list[list[int]] = []
        self._path_gen: Generator | None = None
        self._path_algo_name = "BFS"

        self._active_tab = "sorting"
        self._comparisons = 0
        self._swaps = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("Comparisons: 0 | Swaps: 0", id="stats")
        with TabbedContent():
            with TabPane("Sorting", id="sorting"):
                yield BarChart(id="bar-chart")
                sort_choices = [(name, name) for name in SORTING_ALGORITHMS]
                size_choices = [("10", 10), ("20", 20), ("30", 30), ("50", 50)]
                yield Controls(sort_choices, size_choices, id="sort-controls")
            with TabPane("Searching", id="searching"):
                yield BarChart(id="search-chart")
                search_choices = [(name, name) for name in SEARCHING_ALGORITHMS]
                yield Controls(search_choices, id="search-controls")
            with TabPane("Pathfinding", id="pathfinding"):
                yield GridView(id="grid-view")
                path_choices = [(name, name) for name in PATHFINDING_ALGORITHMS]
                yield Controls(path_choices, id="path-controls")
        yield Footer()

    def on_mount(self) -> None:
        self._reset_sorting()
        self._reset_searching()
        self._reset_pathfinding()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self._stop_playing()
        tab_id = event.pane.id
        if tab_id:
            self._active_tab = tab_id

    def on_select_changed(self, event: Select.Changed) -> None:
        select_id = event.select.id
        if select_id == "algo-select":
            self._stop_playing()
            if self._active_tab == "sorting":
                self._sort_algo_name = str(event.value)
                self._reset_sorting()
            elif self._active_tab == "searching":
                self._search_algo_name = str(event.value)
                self._reset_searching()
            elif self._active_tab == "pathfinding":
                self._path_algo_name = str(event.value)
                self._reset_pathfinding()
        elif select_id == "size-select" and event.value is not None:
            self._stop_playing()
            try:
                self._array_size = int(event.value)
            except (ValueError, TypeError):
                pass
            self._reset_sorting()
        elif select_id == "speed-select" and event.value is not None:
            try:
                self._speed_ms = int(event.value)
            except (ValueError, TypeError):
                pass
            if self._playing:
                self._stop_timer()
                self._start_timer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-play":
            self._start_playing()
        elif btn_id == "btn-pause":
            self._stop_playing()
        elif btn_id == "btn-step":
            self._stop_playing()
            self._do_step()
        elif btn_id == "btn-reset":
            self._stop_playing()
            self._reset_current()
        elif btn_id == "btn-random":
            self._stop_playing()
            self._randomize_current()

    def action_toggle_play(self) -> None:
        if self._playing:
            self._stop_playing()
        else:
            self._start_playing()

    def action_step(self) -> None:
        self._stop_playing()
        self._do_step()

    def action_reset(self) -> None:
        self._stop_playing()
        self._reset_current()

    def _start_playing(self) -> None:
        self._playing = True
        self._start_timer()

    def _stop_playing(self) -> None:
        self._playing = False
        self._stop_timer()

    def _start_timer(self) -> None:
        self._stop_timer()
        self._timer = self.set_interval(self._speed_ms / 1000.0, self._tick)

    def _stop_timer(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None

    def _tick(self) -> None:
        if not self._do_step():
            self._stop_playing()

    def _do_step(self) -> bool:
        if self._active_tab == "sorting":
            return self._step_sorting()
        elif self._active_tab == "searching":
            return self._step_searching()
        elif self._active_tab == "pathfinding":
            return self._step_pathfinding()
        return False

    def _reset_current(self) -> None:
        if self._active_tab == "sorting":
            self._reset_sorting()
        elif self._active_tab == "searching":
            self._reset_searching()
        elif self._active_tab == "pathfinding":
            self._reset_pathfinding()

    def _randomize_current(self) -> None:
        if self._active_tab == "sorting":
            self._sort_array = generate_random_array(self._array_size)
            self._reset_sorting(keep_array=True)
        elif self._active_tab == "searching":
            self._search_array = generate_sorted_array(self._array_size)
            self._search_target = random.choice(self._search_array)
            self._reset_searching(keep_array=True)
        elif self._active_tab == "pathfinding":
            self._grid = generate_grid(20, 20)
            self._reset_pathfinding(keep_grid=True)

    def _reset_sorting(self, keep_array: bool = False) -> None:
        if not keep_array:
            self._sort_array = generate_random_array(self._array_size)
        algo_fn = SORTING_ALGORITHMS[self._sort_algo_name]
        self._sort_gen = algo_fn(self._sort_array)
        self._comparisons = 0
        self._swaps = 0
        self._update_stats()
        chart = self.query_one("#bar-chart", BarChart)
        chart.update_state(self._sort_array, [])

    def _reset_searching(self, keep_array: bool = False) -> None:
        if not keep_array:
            self._search_array = generate_sorted_array(self._array_size)
            self._search_target = random.choice(self._search_array)
        algo_fn = SEARCHING_ALGORITHMS[self._search_algo_name]
        self._search_gen = algo_fn(self._search_array, self._search_target)
        chart = self.query_one("#search-chart", BarChart)
        chart.update_state(self._search_array, [])

    def _reset_pathfinding(self, keep_grid: bool = False) -> None:
        if not keep_grid:
            self._grid = generate_grid(20, 20)
        start = (0, 0)
        end = (19, 19)
        algo_fn = PATHFINDING_ALGORITHMS[self._path_algo_name]
        self._path_gen = algo_fn(self._grid, start, end)
        grid_view = self.query_one("#grid-view", GridView)
        grid_view.update_state(self._grid, set(), set(), [])

    def _step_sorting(self) -> bool:
        if self._sort_gen is None:
            return False
        try:
            arr, highlighted, comparisons, swaps = next(self._sort_gen)
            self._comparisons = comparisons
            self._swaps = swaps
            self._update_stats()
            chart = self.query_one("#bar-chart", BarChart)
            sorted_indices = set()
            if not highlighted:
                sorted_indices = set(range(len(arr)))
            chart.update_state(arr, highlighted, sorted_indices)
            return True
        except StopIteration:
            self._sort_gen = None
            return False

    def _step_searching(self) -> bool:
        if self._search_gen is None:
            return False
        try:
            arr, current_idx, low, high, found = next(self._search_gen)
            chart = self.query_one("#search-chart", BarChart)
            highlighted = [current_idx] if current_idx >= 0 else []
            sorted_indices = {current_idx} if found else set()
            chart.update_state(arr, highlighted, sorted_indices)
            return not found
        except StopIteration:
            self._search_gen = None
            return False

    def _step_pathfinding(self) -> bool:
        if self._path_gen is None:
            return False
        try:
            state: PathState = next(self._path_gen)
            grid_view = self.query_one("#grid-view", GridView)
            grid_view.update_state(state.grid, state.visited, state.frontier, state.path)
            return True
        except StopIteration:
            self._path_gen = None
            return False

    def _update_stats(self) -> None:
        stats = self.query_one("#stats", Static)
        stats.update(f"Comparisons: {self._comparisons} | Swaps: {self._swaps}")


if __name__ == "__main__":
    app = AlgoTheaterApp()
    app.run()
