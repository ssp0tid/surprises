# termchart

**Terminal chart renderer** — CLI tool that reads data from CSV/JSON/stdin and renders bar charts, line charts, scatter plots, and sparklines directly in the terminal using Unicode block characters and ANSI colors.

## Tech Stack

- Python 3 (stdlib only — no external dependencies)
- `curses` for terminal size detection
- `csv` and `json` modules for data parsing
- `argparse` for CLI interface
- Unicode block characters (▁▂▃▄▅▆▇█) and Braille dots (⠀⡀⠄⠂⠁⢀⠠⠐⠈) for rendering

## File Structure

```
termchart/
├── PLAN.md
├── README.md
├── termchart.py          # Entry point + CLI argument parsing
├── charts/
│   ├── __init__.py       # Chart registry
│   ├── bar.py            # Horizontal and vertical bar charts
│   ├── line.py           # Line chart using Braille characters
│   ├── scatter.py        # Scatter plot using Braille characters
│   └── sparkline.py      # Inline sparkline renderer
├── data/
│   ├── __init__.py
│   └── parser.py         # CSV/JSON/stdin data ingestion
├── render/
│   ├── __init__.py
│   ├── canvas.py         # Braille canvas for pixel-level plotting
│   └── colors.py         # ANSI 256-color support + color schemes
└── examples/
    ├── sales.csv
    └── temperatures.json
```

## Features

### 1. Data Ingestion (`data/parser.py`)
- `parse_input(source: str | None, format: str | None) -> list[dict]`
  - Auto-detect format from extension or content
  - CSV: first row as headers, numeric columns auto-detected
  - JSON: array of objects or `{"labels": [...], "values": [...]}`
  - Stdin: one value per line (plain numbers) or CSV format
  - Returns list of dicts with `label` and `value` keys minimum

### 2. Bar Chart (`charts/bar.py`)
- `HBarChart` class — horizontal bars with labels left-aligned
  - `render(data: list[dict], width: int, color_scheme: str) -> str`
  - Features: value labels at end of bars, percentage mode, sorted/unsorted
  - Uses █ and partial blocks (▏▎▍▌▋▊▉) for sub-character precision
- `VBarChart` class — vertical bars
  - `render(data: list[dict], height: int, color_scheme: str) -> str`
  - Uses ▁▂▃▄▅▆▇█ for height levels
  - Labels below bars, values above

### 3. Line Chart (`charts/line.py`)
- `LineChart` class — line plot using Braille dot matrix
  - `render(data: list[dict], width: int, height: int) -> str`
  - Y-axis with auto-scaled labels
  - X-axis with evenly spaced labels
  - Multiple series support (different colors)
  - Interpolation between points

### 4. Scatter Plot (`charts/scatter.py`)
- `ScatterChart` class — 2D scatter using Braille canvas
  - `render(x: list[float], y: list[float], width: int, height: int) -> str`
  - Auto-scaled axes
  - Point density indication (brighter = more points)

### 5. Sparkline (`charts/sparkline.py`)
- `sparkline(values: list[float]) -> str`
  - Single-line inline chart using ▁▂▃▄▅▆▇█
  - Min/max markers optional
  - Color gradient (green→yellow→red) optional

### 6. Braille Canvas (`render/canvas.py`)
- `BrailleCanvas` class
  - `__init__(self, width: int, height: int)` — width/height in terminal chars
  - Each char cell = 2x4 dot grid (Braille U+2800-U+28FF)
  - `set_pixel(x: int, y: int) -> None`
  - `get_pixel(x: int, y: int) -> bool`
  - `draw_line(x0: int, y0: int, x1: int, y1: int) -> None` — Bresenham's
  - `render() -> str` — convert canvas to string of Braille characters

### 7. Colors (`render/colors.py`)
- ANSI escape sequences for 256-color terminal support
- Color schemes: `rainbow`, `heat`, `cool`, `mono`, `pastel`
- `colorize(text: str, color_index: int) -> str`
- `gradient(value: float, min_val: float, max_val: float, scheme: str) -> str`

### 8. CLI Interface (`termchart.py`)
```
usage: termchart.py [-h] {bar,hbar,line,scatter,spark} [options]

positional arguments:
  chart_type          Chart type to render

options:
  -f, --file FILE     Input file (CSV or JSON)
  -x COL             X-axis column name
  -y COL             Y-axis column name (repeatable for multi-series)
  -W, --width INT    Chart width in columns (default: terminal width)
  -H, --height INT   Chart height in rows (default: 20)
  -c, --color SCHEME Color scheme (rainbow|heat|cool|mono|pastel)
  -t, --title TEXT   Chart title
  -s, --sort         Sort data by value (descending)
  --no-color         Disable colors
  --help             Show help
```

### Example Usage
```bash
# Bar chart from CSV
python3 termchart.py bar -f sales.csv -x product -y revenue

# Sparkline from stdin
echo "3 1 4 1 5 9 2 6 5" | python3 termchart.py spark

# Line chart from JSON
python3 termchart.py line -f temperatures.json -x month -y high -y low

# Scatter plot
python3 termchart.py scatter -f data.csv -x weight -y height
```

## Constraints

- Zero external dependencies — stdlib only
- Works on any terminal with Unicode support
- Graceful fallback if terminal is too narrow (truncate labels)
- All output to stdout (pipeable)
- Python 3.9+ compatible
