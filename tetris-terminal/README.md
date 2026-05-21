# Tetris Terminal

A fully-featured Tetris game for the terminal, built with Python 3 and curses. No external dependencies.

## Run

```bash
python3 tetris.py
```

Requires Python 3.6+ and a terminal that supports colors (most do).

## Controls

| Key | Action |
|-----|--------|
| ← → | Move piece |
| ↑ / Z | Rotate clockwise |
| X | Rotate counter-clockwise |
| ↓ | Soft drop (+1 point per cell) |
| Space | Hard drop (+2 points per cell) |
| P | Pause |
| Q | Quit |

## Features

- All 7 standard tetrominoes with color
- Ghost piece showing landing position
- Wall kicks on rotation
- Next piece preview
- Scoring with line clear multipliers (1=100, 2=300, 3=500, 4=800)
- Increasing speed per level (level up every 10 lines)
- Top 5 high scores saved to `scores.json`

## Terminal Requirements

Works in any 80x24 terminal. Uses `curses.wrapper` for clean terminal restore on exit or crash.
