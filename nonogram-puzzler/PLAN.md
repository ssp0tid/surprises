# Nonogram Puzzler

A browser-based Nonogram (Picross) puzzle game where players solve logic puzzles by filling in cells on a grid based on numeric clues. Includes puzzle generation, multiple difficulty levels, timer, and progress saving.

## Tech Stack

- **Backend:** Python 3 Flask (single file)
- **Frontend:** Vanilla HTML/CSS/JS (embedded in templates)
- **Storage:** SQLite via sqlite3 stdlib
- **No external API keys required**

## File Structure

```
nonogram-puzzler/
├── PLAN.md
├── README.md
├── app.py                  # Flask app — routes, puzzle generation, API
├── nonogram.py             # Core puzzle logic — generation, validation, solver
├── templates/
│   ├── index.html          # Landing page — difficulty select, saved games
│   └── play.html           # Game board — grid, clues, timer, controls
├── static/
│   ├── style.css           # Grid styling, responsive layout, animations
│   └── game.js             # Client-side game logic — click handling, validation, timer
└── requirements.txt        # Flask only
```

## Features

### 1. Puzzle Generation (`nonogram.py`)
- `generate_puzzle(rows: int, cols: int, density: float) -> dict`
  - Creates a random binary grid (1 = filled, 0 = empty)
  - `density` controls fill ratio (0.4 for easy, 0.6 for hard)
  - Returns `{"solution": [[int]], "row_clues": [[int]], "col_clues": [[int]]}`
- `compute_clues(line: list[int]) -> list[int]`
  - Computes consecutive-filled-cell counts for a single row/column
  - Example: `[1,1,0,1,1,1,0,1]` → `[2, 3, 1]`
- `validate_solution(grid: list[list[int]], row_clues: list[list[int]], col_clues: list[list[int]]) -> bool`
  - Checks if player's grid matches the clues (not necessarily the original solution — multiple valid solutions possible)

### 2. Difficulty Levels
- **Easy:** 5×5 grid, density 0.4
- **Medium:** 10×10 grid, density 0.5
- **Hard:** 15×15 grid, density 0.55

### 3. Game State Persistence (SQLite)
- Table `puzzles`: id, difficulty, row_clues (JSON), col_clues (JSON), solution (JSON), created_at
- Table `saves`: id, puzzle_id, player_grid (JSON), elapsed_seconds, completed (bool), created_at, updated_at
- API endpoints:
  - `GET /` — landing page
  - `POST /api/new-game` — generate puzzle, return puzzle_id + clues
  - `GET /api/game/<id>` — load saved game state
  - `POST /api/save` — save current grid state + timer
  - `POST /api/check` — validate current grid against clues
  - `GET /play/<id>` — render game page

### 4. Frontend Game Board (`game.js`)
- CSS Grid layout for the nonogram board
- Left-click to fill cell (black), right-click to mark as empty (X)
- Click again to clear cell
- Row/column clues displayed along edges
- Timer (mm:ss) starts on first click
- "Check Solution" button — highlights incorrect cells in red briefly
- Win animation when puzzle is solved
- Auto-save every 30 seconds via fetch POST

### 5. Landing Page (`index.html`)
- Three difficulty buttons (Easy/Medium/Hard) to start new game
- List of saved in-progress games with resume button
- Completed games with time shown

## Constraints

- Single `pip install flask` dependency (use stdlib sqlite3)
- No JavaScript frameworks — vanilla JS only
- Responsive: works on mobile (touch = left-click)
- All game logic validation happens server-side (no cheating by inspecting JS)
- Puzzles must be solvable (generated from a known solution)

## Data Structures

```python
# Puzzle dict (returned by generate_puzzle)
{
    "solution": [[0,1,1,0,1], [1,0,1,1,0], ...],  # rows x cols
    "row_clues": [[2,1], [1,2], ...],               # clue groups per row
    "col_clues": [[1], [1,1], [2], ...]             # clue groups per col
}

# Player grid state (0=empty, 1=filled, 2=marked-X)
[[0, 1, 2, 0, 1], ...]
```

## Entry Point

```bash
python3 app.py
# Starts Flask dev server on http://localhost:5001
```
