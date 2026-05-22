# Typing Dojo 🥋

> Terminal typing speed trainer with WPM tracking, accuracy stats, multiple difficulty modes, and persistent high scores.

## Tech Stack
- Python 3 (stdlib only — curses, json, time, random, os, pathlib)
- No external dependencies

## Constraints
- Single entry point: `typing_dojo.py`
- Data stored in `~/.typing-dojo/` (scores.json)
- Must work in standard 80x24 terminal minimum
- No pip installs required

## File Structure
```
typing-dojo/
├── PLAN.md
├── README.md
├── typing_dojo.py          # Entry point — main menu, game loop, curses UI
├── words.py                # Word lists by difficulty (easy/medium/hard/code)
├── stats.py                # WPM calculation, accuracy tracking, score persistence
└── texts.py                # Paragraph/sentence prompts for longer typing tests
```

## Features

### 1. Main Menu (curses)
- ASCII art title "TYPING DOJO"
- Options: [1] Quick Test, [2] Timed Test, [3] Code Mode, [4] High Scores, [5] Quit
- Arrow key or number key navigation

### 2. Quick Test Mode
- Display 10-20 random words from selected difficulty
- User types words separated by spaces
- Real-time character-by-character feedback:
  - Correct chars: green
  - Incorrect chars: red with underline
  - Current position: highlighted/cursor
- On completion: show WPM, accuracy %, time taken

### 3. Timed Test Mode
- Choose duration: 15s, 30s, 60s, 120s
- Continuous word stream — new words appear as previous ones are completed
- Countdown timer displayed in top-right corner
- Results screen with: WPM, raw WPM, accuracy, correct/incorrect words count

### 4. Code Mode
- Typing prompts are code snippets (Python, JS, Go one-liners)
- Tests special characters: {}, [], (), =>, ->, ::, !=, ===
- Measures "code WPM" (characters per minute / 5)

### 5. High Scores
- Persist top 10 scores per mode to ~/.typing-dojo/scores.json
- Display: rank, WPM, accuracy, date, mode
- JSON format:
```json
{
  "quick": [{"wpm": 85, "accuracy": 97.2, "date": "2026-05-22", "difficulty": "medium"}],
  "timed": [{"wpm": 72, "accuracy": 94.1, "date": "2026-05-22", "duration": 60}],
  "code": [{"wpm": 45, "accuracy": 88.5, "date": "2026-05-22"}]
}
```

### 6. Stats Calculation (stats.py)
```python
def calculate_wpm(chars_typed: int, seconds_elapsed: float) -> float:
    """WPM = (chars_typed / 5) / (seconds / 60)"""

def calculate_accuracy(correct_chars: int, total_chars: int) -> float:
    """accuracy = (correct / total) * 100"""

def save_score(mode: str, score: dict) -> None:
    """Append score to ~/.typing-dojo/scores.json, keep top 10 per mode"""

def load_scores() -> dict:
    """Load scores from JSON file, return empty structure if not found"""
```

### 7. Word Lists (words.py)
```python
EASY_WORDS: list[str]    # 100 common 3-5 letter words
MEDIUM_WORDS: list[str]  # 100 common 5-8 letter words  
HARD_WORDS: list[str]    # 100 uncommon 8+ letter words
```

### 8. Code Snippets (texts.py)
```python
CODE_SNIPPETS: list[str]  # 30+ one-liner code snippets
PARAGRAPHS: list[str]     # 10+ multi-sentence paragraphs for variety
```

## UI Layout (80x24 minimum)
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  TYPING DOJO 🥋                                          WPM: 72  Time: 45s │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  the quick brown fox jumps over the lazy dog while the cat sleeps            │
│  ███████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░           │
│                         ^ cursor                                             │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  Accuracy: 96.4%  |  Words: 5/12  |  Errors: 2                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Entry Point Behavior
```
$ python3 typing_dojo.py          # Launch interactive TUI
$ python3 typing_dojo.py --help   # Show usage info and exit
$ python3 typing_dojo.py --quick  # Jump straight to quick test
$ python3 typing_dojo.py --timed 60  # Jump to 60s timed test
```

Use argparse for CLI flags, curses for the interactive UI.
