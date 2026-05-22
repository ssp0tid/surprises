# Nonogram Puzzler

A browser-based Nonogram (Picross) puzzle game. Solve logic puzzles by filling in cells on a grid based on numeric clues.

## Features

- Three difficulty levels: Easy (5×5), Medium (10×10), Hard (15×15)
- Timer tracking
- Auto-save every 30 seconds
- Resume in-progress games
- Server-side validation (no cheating via browser inspection)
- Responsive design (works on mobile)

## Setup

```bash
pip install -r requirements.txt
python3 app.py
```

Open http://localhost:5001 in your browser.

## How to Play

1. Select a difficulty level on the landing page
2. Left-click a cell to fill it (black)
3. Right-click a cell to mark it as empty (×)
4. Click a filled/marked cell again to clear it
5. Use the numeric clues along the edges to determine which cells to fill
6. Click "Check Solution" to validate your answer

## Tech Stack

- Python 3 / Flask
- SQLite (stdlib sqlite3)
- Vanilla HTML/CSS/JS
