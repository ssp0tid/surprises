# Maze Runner

Terminal maze game with generation, solving, and playable mode. Python 3, stdlib only (curses).

## Requirements

- Python 3.10+
- A terminal that supports Unicode box-drawing characters
- Minimum terminal size: 80x24

No external dependencies. Everything uses the Python standard library.

## Quick Start

```bash
# Play a maze (default mode)
python maze.py

# Play with custom size
python maze.py play --size 30x15

# Watch A* solve a maze
python maze.py solve --solver astar --speed 0.03

# Generate and display without interaction
python maze.py generate --algo prims --size 25x12

# Print maze to stdout (no curses)
python maze.py generate --no-render --seed 42
```

## Modes

### Play

Navigate the maze from top-left to bottom-right. Arrow keys or WASD to move, Q to quit. Timer and move counter shown in the status bar. High scores saved automatically.

```bash
python maze.py play [--size WxH] [--algo recursive|kruskals|prims] [--seed INT]
```

### Solve

Watch an algorithm solve the maze with step-by-step animation. Red cells show visited nodes, green shows the solution path.

```bash
python maze.py solve [--size WxH] [--algo recursive|kruskals|prims] [--solver bfs|dfs|astar] [--speed FLOAT] [--seed INT]
```

### Generate

Display a generated maze. Use `--no-render` to print ASCII to stdout instead of using curses.

```bash
python maze.py generate [--size WxH] [--algo recursive|kruskals|prims] [--no-render] [--seed INT]
```

## Generation Algorithms

| Algorithm | Flag | Character |
|-----------|------|-----------|
| Recursive Backtracker | `--algo recursive` | Long winding corridors |
| Kruskal's | `--algo kruskals` | More branching paths |
| Prim's | `--algo prims` | Organic-looking layout |

## Solving Algorithms

| Algorithm | Flag | Strategy |
|-----------|------|----------|
| BFS | `--solver bfs` | Shortest path guaranteed |
| DFS | `--solver dfs` | Fast but not shortest |
| A* | `--solver astar` | Shortest path, fewer nodes visited |

## Controls (Play Mode)

| Key | Action |
|-----|--------|
| ↑ / W | Move north |
| → / D | Move east |
| ↓ / S | Move south |
| ← / A | Move west |
| Q | Quit |

## High Scores

Best times are saved to `highscores.json` (auto-created). Top 10 per size+algorithm combination. Shown after completing a maze in play mode.

## Reproducible Mazes

Use `--seed INT` to generate the same maze every time:

```bash
python maze.py play --seed 12345 --size 20x10 --algo recursive
```
