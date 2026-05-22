# Algo Theater

**One-line:** Interactive terminal algorithm visualizer — watch sorting, searching, and pathfinding algorithms execute step-by-step with animated bar charts and grids.

## Tech Stack

- Python 3 + Textual (TUI framework)
- No external API keys required
- Virtual environment for dependencies

## Dependencies

- textual>=0.50.0
- rich>=13.0.0

## File Structure

```
algo-theater/
├── PLAN.md
├── README.md
├── requirements.txt
├── run.sh              # Setup venv + run
├── app.py              # Main Textual app entry point
├── algorithms/
│   ├── __init__.py
│   ├── sorting.py      # Sorting algorithm generators
│   ├── searching.py    # Search algorithm generators
│   └── pathfinding.py  # Grid pathfinding generators
├── widgets/
│   ├── __init__.py
│   ├── bar_chart.py    # Animated bar chart widget for sorting
│   ├── grid_view.py    # Grid widget for pathfinding
│   └── controls.py     # Speed/algorithm selection controls
└── utils.py            # Shared helpers (array generation, timing)
```

## Features

### 1. Sorting Visualizer
- Algorithms: Bubble Sort, Selection Sort, Insertion Sort, Merge Sort, Quick Sort
- Each algorithm is a Python generator that yields `(array_state, highlighted_indices, comparison_count, swap_count)` after each step
- Bar chart widget renders array as colored vertical bars (height = value)
- Active comparisons highlighted in yellow, swaps in red, sorted elements in green

### 2. Search Visualizer
- Algorithms: Linear Search, Binary Search
- Array displayed as horizontal cells
- Current position highlighted, search space dimmed as eliminated
- Yields `(array, current_index, low, high, found)` per step

### 3. Pathfinding Visualizer
- Algorithms: BFS, DFS, A* (Manhattan heuristic)
- 20x20 grid with configurable walls (random generation)
- Start = top-left, End = bottom-right
- Colors: unvisited=dark, visited=blue, frontier=yellow, path=green, wall=white
- Yields `(grid, visited_set, frontier_set, current_path)` per step

### 4. Controls
- Algorithm selector (dropdown/select)
- Speed slider: 10ms to 500ms per step
- Play/Pause/Step/Reset buttons
- Array size selector (10, 20, 30, 50 for sorting)
- Randomize button to generate new data

## Implementation Notes

### app.py — Main Application
```python
class AlgoTheaterApp(App):
    CSS_PATH = None  # Inline CSS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_play", "Play/Pause"),
        ("s", "step", "Step"),
        ("r", "reset", "Reset"),
    ]
```

Screens: Single screen with tabbed interface (Sorting | Searching | Pathfinding)

### algorithms/sorting.py
Each algorithm is a generator function:
```python
def bubble_sort(arr: list[int]) -> Generator[tuple[list[int], list[int], int, int], None, None]:
    """Yields (array_copy, highlighted_indices, comparisons, swaps) at each step."""
    comparisons = swaps = 0
    arr = arr.copy()
    for i in range(len(arr)):
        for j in range(len(arr) - 1 - i):
            comparisons += 1
            yield (arr.copy(), [j, j+1], comparisons, swaps)
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
                swaps += 1
                yield (arr.copy(), [j, j+1], comparisons, swaps)
    yield (arr.copy(), [], comparisons, swaps)
```

### algorithms/pathfinding.py
Grid is a 2D list: 0=open, 1=wall. Generator yields state per expansion:
```python
def bfs(grid: list[list[int]], start: tuple, end: tuple) -> Generator[PathState, None, None]:
    """Yields PathState(grid, visited, frontier, path) per step."""
```

### widgets/bar_chart.py
Custom Textual Widget using Rich renderable. Each bar is a column of block characters (█). Height scaled to widget height. Colors via Rich Style.

### widgets/grid_view.py
Custom widget rendering a grid of cells. Each cell is 2 chars wide ("██"). Color-coded by state.

### widgets/controls.py
Horizontal container with Select, Button, and Slider widgets from Textual.

## Constraints

- Single-file entry point: `python3 app.py`
- No external API keys
- Works in standard 80x24+ terminal (responsive to larger)
- All algorithms are educational — prioritize clarity over optimization
- run.sh handles venv creation and dependency installation automatically
