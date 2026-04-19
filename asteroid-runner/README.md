# Asteroid Runner

A Terminal ASCII Roguelike Space Shooter built with Python and Textual TUI Framework.

![Game Preview](placeholder)

## Features

- **Real-time Gameplay**: Smooth 60 FPS rendering in your terminal
- **Procedural Content**: Endless waves of asteroids and enemies
- **Roguelike Elements**: Increasing difficulty, combo scoring, high score persistence
- **ASCII Art Graphics**: Beautiful character-based visuals
- **Multiple Input Modes**: WASD, Arrow Keys, Vim-style (HJKL), or IJKL

## Installation

### Requirements

- Python 3.11 or later
- Terminal with ANSI/VT100 support
- Minimum 80x24 terminal size (recommended 120x40)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/asteroid-runner.git
cd asteroid-runner

# Install dependencies
pip install -r requirements.txt

# Run the game
python -m src.main
```

Or install as a package:

```bash
pip install .
asteroid-runner
```

## Controls

| Action | Keys |
|--------|------|
| Move Up | W, Up Arrow, I |
| Move Down | S, Down Arrow, K |
| Move Left | A, Left Arrow, J |
| Move Right | D, Right Arrow, L |
| Shoot | Space, Z |
| Pause | Escape, P |
| Menu Navigate | W/S, Up/Down Arrows |
| Select | Enter |

## Gameplay

### Objective

Survive as long as possible while destroying asteroids and enemy ships to rack up points.

### Scoring

| Target | Points |
|--------|--------|
| Small Asteroid | 10 |
| Medium Asteroid | 25 |
| Large Asteroid | 50 |
| Basic Enemy | 20 |
| Advanced Enemy | 50 |
| Boss | 500 |

### Combo System

- Consecutive kills increase your score multiplier (+0.1x per kill)
- Maximum combo multiplier: 2.0x
- Taking damage resets your combo

### Difficulty Progression

- Difficulty increases every level
- Boss levels occur every 5 levels
- Enemies get faster and tougher
- More advanced enemy types appear at higher levels

## Project Structure

```
asteroid-runner/
├── src/
│   ├── main.py              # Entry point
│   ├── app.py               # Textual App
│   ├── game/
│   │   ├── engine.py        # Game loop
│   │   ├── state.py         # State machine
│   │   ├── config.py        # Configuration
│   │   ├── entities/        # Entity system
│   │   └── systems/         # Game systems
│   ├── ui/                  # UI screens
│   ├── input/               # Input handling
│   ├── persistence/         # Save/load
│   └── utils/              # Utilities
├── tests/                   # Test suite
└── assets/                  # Data files
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy src/
```

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/) TUI Framework
- Inspired by classic arcade shooters like Asteroids and Space Invaders
