# ChartCraft

**One-line:** Web-based interactive chart builder — paste CSV/JSON data, pick chart types, customize colors/labels, and export as PNG or share via link.

## Tech Stack

- Python 3 + Flask (backend)
- SQLite (chart persistence/sharing)
- Chart.js 4.x via CDN (rendering)
- TailwindCSS CDN (styling)
- Vanilla JavaScript (frontend logic)
- No external pip dependencies beyond Flask

## File Structure

```
chartcraft/
├── PLAN.md
├── README.md
├── app.py              # Flask application (entry point)
├── schema.sql          # SQLite schema
├── static/
│   └── js/
│       └── chartcraft.js   # Frontend chart logic
└── templates/
    ├── base.html       # Base template with nav
    ├── index.html      # Main editor page
    ├── gallery.html    # Saved charts gallery
    └── view.html       # Single chart view (shared link)
```

## Features

### 1. Data Input (frontend)
- Textarea for pasting CSV data (auto-detect delimiter: comma, tab, semicolon)
- Textarea for pasting JSON array data
- Parse button that extracts headers and rows
- Display parsed data as preview table (first 10 rows)
- Function: `parseCSV(text)` → `{headers: string[], rows: any[][]}`
- Function: `parseJSON(text)` → `{headers: string[], rows: any[][]}`

### 2. Chart Configuration (frontend)
- Chart type selector: bar, line, pie, doughnut, radar, polarArea, scatter
- X-axis column picker (dropdown from parsed headers)
- Y-axis column picker (multi-select for multiple series)
- Chart title input
- Color scheme selector: 5 preset palettes (vibrant, pastel, earth, ocean, monochrome)
- Toggle: show legend, show grid, show data labels
- Function: `buildChartConfig(data, options)` → Chart.js config object

### 3. Live Preview (frontend)
- Canvas element renders chart in real-time as options change
- Debounced re-render (300ms) on any config change
- Responsive sizing within container
- Function: `renderChart(config)` — destroys old instance, creates new Chart()

### 4. Export (frontend + backend)
- Export as PNG: `chart.toBase64Image()` → download link
- Save to server: POST /api/charts with {title, data, config, thumbnail_base64}
- Returns share URL: /chart/<uuid>

### 5. Chart Gallery (backend)
- GET /api/charts — list all saved charts (title, thumbnail, created_at)
- GET /chart/<uuid> — view single chart with full interactivity
- DELETE /api/charts/<uuid> — remove a chart

### 6. Sharing
- Each saved chart gets a UUID-based URL
- View page renders the chart from stored config
- No auth required (local tool)

## Database Schema (schema.sql)

```sql
CREATE TABLE IF NOT EXISTS charts (
    id TEXT PRIMARY KEY,          -- UUID
    title TEXT NOT NULL,
    raw_data TEXT NOT NULL,       -- original CSV/JSON input
    chart_config TEXT NOT NULL,   -- JSON Chart.js config
    thumbnail TEXT,               -- base64 PNG thumbnail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints (app.py)

```python
# Pages
GET  /                  → render index.html (editor)
GET  /gallery           → render gallery.html
GET  /chart/<uuid>      → render view.html

# API
POST   /api/charts      → save chart, return {id, url}
GET    /api/charts      → list charts [{id, title, thumbnail, created_at}]
DELETE /api/charts/<id>  → delete chart
```

## Color Palettes (in chartcraft.js)

```javascript
const PALETTES = {
    vibrant:    ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'],
    pastel:     ['#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#E8BAFF', '#FFD9BA'],
    earth:      ['#8B4513', '#D2691E', '#DAA520', '#556B2F', '#2E8B57', '#4682B4'],
    ocean:      ['#001f3f', '#0074D9', '#7FDBFF', '#39CCCC', '#3D9970', '#2ECC40'],
    monochrome: ['#111111', '#333333', '#555555', '#777777', '#999999', '#BBBBBB']
};
```

## Constraints

- Single `app.py` file for all backend logic (no blueprints)
- No pip dependencies beyond Flask (use stdlib uuid, json, sqlite3)
- All frontend via CDN (Chart.js, TailwindCSS) — no npm/build step
- SQLite database stored as `chartcraft.db` in project directory
- Port 5000 default, configurable via PORT env var
- No authentication — local use only
- Max data size: 1MB per chart
