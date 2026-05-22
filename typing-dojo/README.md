# Typing Dojo

Terminal typing speed trainer with WPM tracking, accuracy stats, multiple difficulty modes, and persistent high scores.

## Requirements

- Python 3.10+
- No external dependencies (stdlib only: curses, json, time, random, pathlib, argparse)

## Usage

```bash
python3 typing_dojo.py            # Launch interactive TUI
python3 typing_dojo.py --help     # Show usage info
python3 typing_dojo.py --quick    # Jump straight to quick test
python3 typing_dojo.py --timed 60 # Jump to 60s timed test
```

## Modes

**Quick Test** — Type 10-20 random words from a chosen difficulty (easy/medium/hard). Real-time character feedback with color coding.

**Timed Test** — Continuous word stream with a countdown timer. Choose 15s, 30s, 60s, or 120s.

**Code Mode** — Type code snippets with special characters (`{}`, `[]`, `=>`, `->`, `!=`). Measures code WPM.

**High Scores** — Top 10 scores per mode, persisted to `~/.typing-dojo/scores.json`.

## Controls

- Arrow keys or number keys to navigate menus
- Type characters to match the prompt
- Backspace to correct mistakes
- ESC to return to menu

## Terminal

Minimum 80x24 terminal size recommended.
