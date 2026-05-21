# Tetris Terminal

A fully-featured Tetris game for the terminal using Python curses. No external dependencies — stdlib only.

## Tech Stack
- Python 3 (stdlib only)
- `curses` for terminal rendering
- `json` for high score persistence

## File Structure
```
tetris-terminal/
├── PLAN.md
├── README.md
├── tetris.py          # Main entry point — game loop, rendering, input
├── pieces.py          # Tetromino definitions, rotation matrices
├── board.py           # Board state, collision detection, line clearing
└── scores.json        # High scores (created at runtime)
```

## Features

### Core Gameplay
- 10x20 board (standard Tetris dimensions)
- All 7 tetrominoes: I, O, T, S, Z, J, L
- Wall kicks on rotation (basic — try offset if rotation collides)
- Soft drop (down arrow), hard drop (space)
- Left/right movement, rotation (up arrow or 'z'/'x')
- Ghost piece showing where current piece will land
- Line clearing with score multiplier (1=100, 2=300, 3=500, 4=800)
- Increasing speed per level (level up every 10 lines)

### Display
- Colored pieces using curses color pairs (each tetromino has unique color)
- Next piece preview panel
- Score, level, lines cleared display
- Game over screen with final score
- Start/title screen

### Controls
- Left/Right arrows: move piece
- Up arrow: rotate clockwise
- Down arrow: soft drop (1 cell)
- Space: hard drop (instant)
- 'p': pause/unpause
- 'q': quit

### High Scores
- Top 5 scores saved to `scores.json` in same directory
- Displayed on game over screen

## Implementation Notes

### pieces.py
```python
# Each piece is a list of 4 rotation states
# Each rotation state is a list of (row, col) offsets from pivot
PIECES = {
    'I': [[(0,0),(0,1),(0,2),(0,3)], [(0,0),(1,0),(2,0),(3,0)], ...],
    'O': [[(0,0),(0,1),(1,0),(1,1)], ...],  # Only 1 rotation
    'T': [[(0,0),(0,1),(0,2),(1,1)], ...],
    'S': [[(0,1),(0,2),(1,0),(1,1)], ...],
    'Z': [[(0,0),(0,1),(1,1),(1,2)], ...],
    'J': [[(0,0),(0,1),(0,2),(1,2)], ...],
    'L': [[(0,0),(0,1),(0,2),(1,0)], ...],
}
COLORS = {'I': 1, 'O': 2, 'T': 3, 'S': 4, 'Z': 5, 'J': 6, 'L': 7}
```

### board.py
```python
class Board:
    WIDTH = 10
    HEIGHT = 20
    
    def __init__(self):
        self.grid = [[0]*self.WIDTH for _ in range(self.HEIGHT)]
    
    def is_valid_position(self, piece_cells: list[tuple[int,int]]) -> bool:
        """Check if all cells are in bounds and unoccupied."""
    
    def lock_piece(self, piece_cells: list[tuple[int,int]], color: int):
        """Place piece on board permanently."""
    
    def clear_lines(self) -> int:
        """Remove full lines, return count cleared."""
    
    def is_game_over(self) -> bool:
        """Check if any cell in top row is occupied."""
```

### tetris.py (main entry point)
```python
class Game:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.board = Board()
        self.current_piece = None
        self.next_piece = None
        self.piece_x = 0
        self.piece_y = 0
        self.rotation = 0
        self.score = 0
        self.level = 1
        self.lines = 0
        self.paused = False
        self.game_over = False
    
    def run(self):
        """Main game loop with timing-based gravity."""
    
    def draw(self):
        """Render board, current piece, ghost, next piece, stats."""
    
    def handle_input(self, key: int):
        """Process keyboard input."""
    
    def drop_piece(self):
        """Move piece down one row or lock if at bottom."""
    
    def get_ghost_y(self) -> int:
        """Calculate where piece would land for ghost display."""

def main():
    curses.wrapper(game_main)
```

## Constraints
- No external dependencies (pip install nothing)
- Single `python3 tetris.py` to run
- Must work in standard 80x24 terminal (game board + side panel fits)
- Graceful terminal restore on quit/crash (curses.wrapper handles this)
- No async — simple blocking loop with curses.halfdelay() for timing
