# Algo Theater

Interactive terminal algorithm visualizer — watch sorting, searching, and pathfinding algorithms execute step-by-step with animated bar charts and grids.

## Quick Start

```bash
./run.sh
```

This creates a virtual environment, installs dependencies, and launches the app.

## Requirements

- Python 3.10+
- Terminal with 80x24+ size (responsive to larger)

## Controls

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| S | Step (advance one frame) |
| R | Reset current algorithm |
| Q | Quit |

Use the on-screen buttons and dropdowns to select algorithms, adjust speed (10ms–500ms per step), change array size (10–50 for sorting), and randomize data.

## Algorithms

### Sorting
- Bubble Sort
- Selection Sort
- Insertion Sort
- Merge Sort
- Quick Sort

### Searching
- Linear Search
- Binary Search

### Pathfinding (20x20 grid)
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- A* (Manhattan heuristic)

## Color Legend

### Sorting
- Cyan: default bar
- Red: active comparison/swap
- Green: sorted/final position

### Searching
- Cyan: default bar
- Red: active position being checked
- Green: target found

### Pathfinding
- Dim white: unvisited
- Blue: visited
- Yellow: frontier
- Green: final path
- White: wall
