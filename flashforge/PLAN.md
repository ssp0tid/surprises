# FlashForge

**One-line:** CLI spaced repetition flashcard system with Leitner box algorithm, multiple decks, import/export, and progress statistics.

## Tech Stack

- Python 3 + Click (CLI framework) + Rich (terminal UI/tables) + SQLite (storage)
- No external API keys required
- Single venv, no system-level deps beyond python3

## Constraints

- All code in a single directory
- Use `.venv` for dependencies (pip externally-managed workaround)
- Entry point: `flashforge.py`
- Database: `~/.flashforge/flashforge.db` (created on first run)

## File Structure

```
flashforge/
├── PLAN.md
├── README.md
├── requirements.txt
├── flashforge.py          # Entry point + CLI commands
├── db.py                  # Database layer (SQLite)
├── leitner.py             # Leitner box scheduling algorithm
├── importer.py            # CSV/Markdown import/export
└── stats.py               # Progress statistics and reporting
```

## Feature List

### 1. Deck Management (`flashforge.py`)
- `flashforge deck create <name>` — create a new deck
- `flashforge deck list` — list all decks with card counts
- `flashforge deck delete <name>` — delete deck and its cards
- `flashforge deck rename <old> <new>` — rename a deck

### 2. Card Management (`flashforge.py`)
- `flashforge card add <deck> --front "Q" --back "A"` — add a card
- `flashforge card list <deck>` — list all cards in a deck (rich table)
- `flashforge card delete <card_id>` — delete a card by ID
- `flashforge card edit <card_id> --front "Q" --back "A"` — edit a card

### 3. Study Session (`flashforge.py` + `leitner.py`)
- `flashforge study <deck>` — start interactive study session
- Shows front of card, waits for Enter, shows back
- Prompts: [1] Again  [2] Hard  [3] Good  [4] Easy
- Updates Leitner box based on response
- Session ends when no more due cards or user quits with 'q'
- Shows session summary (cards reviewed, accuracy)

### 4. Leitner Box Algorithm (`leitner.py`)
- 5 boxes with increasing intervals:
  - Box 1: review every 1 day
  - Box 2: review every 3 days
  - Box 3: review every 7 days
  - Box 4: review every 14 days
  - Box 5: review every 30 days
- Correct answer → move card to next box (max box 5)
- "Again" → move card back to box 1
- "Hard" → stay in current box, reset interval
- "Good" → move to next box
- "Easy" → skip one box (move +2, max box 5)
- Function: `get_due_cards(deck_id: int) -> list[dict]`
- Function: `update_card_box(card_id: int, response: str) -> None`
- Function: `calculate_next_review(box: int) -> datetime`

### 5. Import/Export (`importer.py`)
- `flashforge import csv <deck> <file.csv>` — import from CSV (front,back columns)
- `flashforge import markdown <deck> <file.md>` — import from markdown (## front / answer below)
- `flashforge export csv <deck> <output.csv>` — export deck to CSV
- CSV format: `front,back` (with header row)
- Markdown format:
  ```
  ## Question text
  Answer text

  ## Another question
  Another answer
  ```
- Function: `import_csv(deck_id: int, filepath: str) -> int` (returns count imported)
- Function: `import_markdown(deck_id: int, filepath: str) -> int`
- Function: `export_csv(deck_id: int, filepath: str) -> int`

### 6. Statistics (`stats.py`)
- `flashforge stats <deck>` — show deck statistics
- `flashforge stats --all` — show global statistics
- Displays:
  - Total cards, cards per box (bar chart with Rich)
  - Cards due today
  - Study streak (consecutive days with at least 1 session)
  - Average accuracy (% correct over last 7 days)
  - Mastery rate (% cards in box 4+)
- Function: `get_deck_stats(deck_id: int) -> dict`
- Function: `get_global_stats() -> dict`
- Function: `render_stats(stats: dict) -> None` (prints Rich panels)

### 7. Database Schema (`db.py`)

```sql
CREATE TABLE decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    box INTEGER DEFAULT 1,
    next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    response TEXT NOT NULL,  -- 'again', 'hard', 'good', 'easy'
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_box INTEGER NOT NULL,
    new_box INTEGER NOT NULL
);
```

- Function: `init_db() -> sqlite3.Connection`
- Function: `get_db() -> sqlite3.Connection` (singleton pattern with path `~/.flashforge/flashforge.db`)
- Creates `~/.flashforge/` directory if not exists

### 8. CLI Structure (`flashforge.py`)

```python
import click
from rich.console import Console
from rich.table import Table

@click.group()
def cli():
    """FlashForge - Spaced repetition flashcards in your terminal."""
    pass

@cli.group()
def deck():
    """Manage flashcard decks."""
    pass

@cli.group()
def card():
    """Manage individual cards."""
    pass

@cli.command()
@click.argument('deck_name')
def study(deck_name):
    """Start a study session."""
    pass

@cli.group(name='import')
def import_cmd():
    """Import cards from files."""
    pass

@cli.command(name='export')
def export_cmd():
    """Export deck to file."""
    pass

@cli.command()
def stats():
    """View study statistics."""
    pass
```

## Implementation Notes

- Use `click.echo()` for plain output, `Rich` Console for formatted tables/panels
- All datetime operations use UTC
- Handle empty decks gracefully (show helpful message)
- Validate deck exists before operations
- Use `click.confirm()` for destructive operations (delete)
- Study session uses `click.getchar()` for single-key input on responses
- Error handling: wrap DB operations in try/except, show user-friendly messages
