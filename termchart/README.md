# termchart

Terminal chart renderer — CLI tool that reads data from CSV/JSON/stdin and renders bar charts, line charts, scatter plots, and sparklines directly in the terminal using Unicode block characters and ANSI colors.

## Requirements

- Python 3.9+
- No external dependencies (stdlib only)
- Terminal with Unicode support

## Installation

No installation needed. Clone and run directly:

```bash
git clone <repo-url>
cd termchart
```

## Usage

```
python3 termchart.py {bar,hbar,line,scatter,spark} [options]
```

### Options

| Flag | Description |
|------|-------------|
| `-f, --file FILE` | Input file (CSV or JSON) |
| `-x COL` | X-axis column name |
| `-y COL` | Y-axis column name (repeatable for multi-series) |
| `-W, --width INT` | Chart width in columns (default: terminal width) |
| `-H, --height INT` | Chart height in rows (default: 20) |
| `-c, --color SCHEME` | Color scheme: rainbow, heat, cool, mono, pastel |
| `-t, --title TEXT` | Chart title |
| `-s, --sort` | Sort data by value (descending) |
| `--no-color` | Disable colors |

### Examples

```bash
# Horizontal bar chart from CSV
python3 termchart.py hbar -f examples/sales.csv -x product -y revenue

# Vertical bar chart (sorted)
python3 termchart.py bar -f examples/sales.csv -x product -y revenue -s

# Sparkline from stdin
echo "3 1 4 1 5 9 2 6 5" | python3 termchart.py spark

# Line chart from JSON
python3 termchart.py line -f examples/temperatures.json

# Scatter plot
python3 termchart.py scatter -f data.csv -x weight -y height

# Custom color scheme and title
python3 termchart.py hbar -f examples/sales.csv -x product -y revenue -c heat -t "Q4 Revenue"
```

## Chart Types

- **hbar** — Horizontal bar chart with sub-character precision (▏▎▍▌▋▊▉█)
- **bar** — Vertical bar chart using height blocks (▁▂▃▄▅▆▇█)
- **line** — Line chart rendered on a Braille dot matrix canvas
- **scatter** — 2D scatter plot using Braille characters
- **spark** — Single-line inline sparkline

## Data Formats

### CSV
```csv
product,revenue
Widgets,12500
Gadgets,8300
```

### JSON (array of objects)
```json
[{"month": "Jan", "high": 32, "low": 18}]
```

### JSON (labels + values)
```json
{"labels": ["Jan", "Feb", "Mar"], "values": [2, 5, 11]}
```

### Stdin (plain numbers)
```bash
echo "1 2 3 4 5" | python3 termchart.py spark
```

## Color Schemes

- **rainbow** — Full spectrum
- **heat** — Black → red → yellow → white
- **cool** — Dark blue → cyan → white
- **mono** — Grayscale
- **pastel** — Soft muted tones
