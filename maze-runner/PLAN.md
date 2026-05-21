# Maze Runner

> Terminal maze game with generation, solving, and playable mode. Python 3 curses (stdlib only).

## Tech Stack
- Python 3 (stdlib only — curses, random, collections, time, argparse, json)
- No external dependencies

## Constraints
- Single directory, no venv needed
- Must work in standard 80x24 terminal minimum
- No external API keys or network access
- All stdlib — zero pip installs

## File Structure

```
maze-runner/
├── PLAN.md
├── README.md
├── maze.py          # Entry point — CLI argument parsing, mode dispatch
├── generator.py     # Maze generation algorithms
├── solver.py        # Maze solving algorithms
├── renderer.py      # Curses-based rendering engine
├── player.py        # Playable mode — keyboard input, movement, win detection
└── highscores.json  # Auto-created at runtime for storing best times
```

## Features

### 1. Maze Generation (`generator.py`)

Three algorithms, selectable via CLI flag:

```python
def generate_recursive_backtracker(width: int, height: int) -> list[list[int]]:
    """DFS-based maze generation. Produces long winding corridors."""

def generate_kruskals(width: int, height: int) -> list[list[int]]:
    """Kruskal's algorithm. Produces more branching paths."""

def generate_prims(width: int, height: int) -> list[list[int]]:
    """Prim's algorithm. Produces organic-looking mazes."""
```

Maze representation: 2D grid where each cell is a bitmask:
- bit 0 (1): wall north
- bit 1 (2): wall east  
- bit 2 (4): wall south
- bit 3 (8): wall west

Grid dimensions: `width` and `height` refer to cells (not characters). Default 20x10.

### 2. Maze Solving (`solver.py`)

Three solving algorithms with step-by-step state for animation:

```python
def solve_bfs(maze: list[list[int]], start: tuple, end: tuple) -> Generator[tuple[list, list], None, None]:
    """BFS solver. Yields (visited_cells, current_path) at each step."""

def solve_dfs(maze: list[list[int]], start: tuple, end: tuple) -> Generator[tuple[list, list], None, None]:
    """DFS solver. Yields (visited_cells, current_path) at each step."""

def solve_astar(maze: list[list[int]], start: tuple, end: tuple) -> Generator[tuple[list, list], None, None]:
    """A* solver with Manhattan distance heuristic. Yields (visited_cells, current_path) at each step."""
```

Start is always (0, 0), end is always (width-1, height-1).

### 3. Curses Renderer (`renderer.py`)

```python
class MazeRenderer:
    def __init__(self, stdscr, maze: list[list[int]], cell_width: int = 3, cell_height: int = 1):
        """Initialize renderer with curses screen and maze data."""
    
    def draw_maze(self) -> None:
        """Draw the full maze grid with box-drawing characters."""
    
    def highlight_cell(self, row: int, col: int, color_pair: int) -> None:
        """Highlight a specific cell (for solver visualization or player)."""
    
    def draw_path(self, path: list[tuple], color_pair: int) -> None:
        """Draw a path through the maze."""
    
    def draw_status(self, message: str) -> None:
        """Draw status bar at bottom of screen."""
    
    def animate_solve(self, solver_generator, speed: float = 0.05) -> list[tuple]:
        """Animate the solving process step by step. Returns final path."""
```

Color pairs:
- 1: White on black (walls)
- 2: Green on black (solution path)
- 3: Yellow on black (player)
- 4: Red on black (visited cells during solve)
- 5: Cyan on black (start/end markers)

Box-drawing characters for walls: ┌ ┐ └ ┘ │ ─ ├ ┤ ┬ ┴ ┼

### 4. Playable Mode (`player.py`)

```python
class PlayerMode:
    def __init__(self, stdscr, maze: list[list[int]], width: int, height: int):
        """Initialize player at (0,0), target at (width-1, height-1)."""
    
    def run(self) -> float:
        """Main game loop. Returns elapsed time in seconds on win. Arrow keys + WASD to move. Q to quit."""
    
    def can_move(self, direction: str) -> bool:
        """Check if movement in direction is valid (no wall blocking)."""
    
    def move(self, direction: str) -> None:
        """Move player in direction."""
    
    def check_win(self) -> bool:
        """Return True if player reached the end."""
```

Display: Player shown as `@`, start as `S`, end as `E`. Timer shown in status bar. Move counter shown.

### 5. Entry Point (`maze.py`)

```python
"""
Usage:
  maze.py play [--size WxH] [--algo recursive|kruskals|prims]
  maze.py solve [--size WxH] [--algo recursive|kruskals|prims] [--solver bfs|dfs|astar] [--speed FLOAT]
  maze.py generate [--size WxH] [--algo recursive|kruskals|prims] [--no-render]
  maze.py --help
"""
```

Modes:
- `play` — generate maze, then player navigates it. On win, show time + moves, save to highscores.json
- `solve` — generate maze, then animate the solver algorithm
- `generate` — just generate and display a maze (no solving, no playing)

Default: `play` mode if no subcommand given.

### 6. High Scores (`highscores.json`)

```json
[
  {"size": "20x10", "algo": "recursive", "time": 45.2, "moves": 87, "date": "2026-05-21"}
]
```

Top 10 scores per size+algo combo. Shown after winning in play mode.

## Implementation Notes

- Use `curses.wrapper()` for safe terminal init/cleanup
- Handle terminal too small: check `curses.LINES` and `curses.COLS` before rendering, show error if too small
- `nodelay(False)` for play mode (blocking input), `nodelay(True)` for solve animation (non-blocking to allow quit)
- Seed support: `--seed INT` flag for reproducible mazes
- The maze grid uses cell coordinates internally; renderer translates to screen coordinates
