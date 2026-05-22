# FlashForge

CLI spaced repetition flashcard system with Leitner box algorithm, multiple decks, import/export, and progress statistics.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python flashforge.py [command]
```

### Deck Management

```bash
python flashforge.py deck create "Python Basics"
python flashforge.py deck list
python flashforge.py deck rename "Python Basics" "Python"
python flashforge.py deck delete "Python"
```

### Card Management

```bash
python flashforge.py card add "Python" --front "What is a list?" --back "An ordered mutable collection"
python flashforge.py card list "Python"
python flashforge.py card edit 1 --front "What is a Python list?"
python flashforge.py card delete 1
```

### Study Session

```bash
python flashforge.py study "Python"
```

Cards are shown one at a time. Press Enter to reveal the answer, then rate:
- [1] Again — back to box 1
- [2] Hard — stay in current box
- [3] Good — advance one box
- [4] Easy — skip one box

Press `q` at any time to quit.

### Import/Export

```bash
# CSV (must have front,back columns with header row)
python flashforge.py import csv "Python" cards.csv
python flashforge.py export "Python" output.csv

# Markdown (## Question / Answer format)
python flashforge.py import markdown "Python" cards.md
```

### Statistics

```bash
python flashforge.py stats "Python"
python flashforge.py stats --all
```

## Leitner Box System

Cards move through 5 boxes with increasing review intervals:

| Box | Interval |
|-----|----------|
| 1   | 1 day    |
| 2   | 3 days   |
| 3   | 7 days   |
| 4   | 14 days  |
| 5   | 30 days  |

## Data Storage

Database is stored at `~/.flashforge/flashforge.db` (created on first run).
