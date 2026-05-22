# ChartCraft

Web-based interactive chart builder. Paste CSV or JSON data, pick a chart type, customize colors and labels, then export as PNG or share via link.

## Requirements

- Python 3.7+
- Flask (`pip install flask`)

No other dependencies required.

## Quick Start

```bash
pip install flask
python app.py
```

Open http://localhost:5000 in your browser.

To use a custom port:

```bash
PORT=8080 python app.py
```

To enable debug mode:

```bash
FLASK_DEBUG=1 python app.py
```

## Usage

1. Paste CSV or JSON data into the editor
2. Click "Parse" to extract columns
3. Select chart type, axes, colors, and options
4. Preview updates live as you adjust settings
5. Export as PNG or save to share via link

## Supported Chart Types

- Bar
- Line
- Pie
- Doughnut
- Radar
- Polar Area
- Scatter

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Chart editor |
| GET | /gallery | Saved charts gallery |
| GET | /chart/:id | View a shared chart |
| POST | /api/charts | Save a chart |
| GET | /api/charts | List all saved charts |
| DELETE | /api/charts/:id | Delete a chart |

## Data Storage

Charts are persisted in a local SQLite database (`chartcraft.db`), created automatically on first run.
