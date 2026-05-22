# Color Palette Studio

> Web-based color palette generator with harmony rules, contrast checking, and multi-format export.

## Tech Stack

- Python 3 + Flask (single-file backend)
- SQLite for saving palettes
- Vanilla HTML/CSS/JS frontend (embedded in templates)
- No external API keys required

## Constraints

- Single `app.py` entry point
- All templates inline using Flask's `render_template_string` or in `templates/` dir
- No npm/node build step — pure browser JS
- Use python3 stdlib `colorsys` for color math (no external color libs needed)
- Virtual env not required (Flask only dependency, install with `pip3 install --user flask` or use system)

## File Structure

```
color-palette-studio/
├── PLAN.md
├── README.md
├── app.py                  # Flask app — routes, API, color logic
├── color_engine.py         # Color math: conversions, harmony, contrast
├── database.py             # SQLite palette storage
├── templates/
│   ├── index.html          # Main palette workspace
│   └── saved.html          # Saved palettes gallery
└── static/
    ├── style.css           # UI styling
    └── app.js              # Client-side interactivity
```

## Features

### 1. Color Harmony Generator (`color_engine.py`)

Functions:
- `hex_to_hsl(hex_color: str) -> tuple[float, float, float]`
- `hsl_to_hex(h: float, s: float, l: float) -> str`
- `hex_to_rgb(hex_color: str) -> tuple[int, int, int]`
- `rgb_to_hex(r: int, g: int, b: int) -> str`
- `generate_harmony(base_hex: str, rule: str) -> list[str]`
  - Rules: complementary, analogous, triadic, split-complementary, tetradic, monochromatic
- `relative_luminance(hex_color: str) -> float`
- `contrast_ratio(color1: str, color2: str) -> float`
- `wcag_rating(ratio: float) -> str` — returns "AAA", "AA", "AA Large", or "Fail"
- `random_color() -> str`

### 2. Web Interface (`app.py` + templates)

Routes:
- `GET /` — main workspace page
- `GET /api/harmony?base=<hex>&rule=<rule>` — generate palette via harmony rule
- `GET /api/contrast?color1=<hex>&color2=<hex>` — check WCAG contrast
- `GET /api/random` — random base color
- `POST /api/palette/save` — save palette to SQLite (JSON body: {name, colors[]})
- `GET /api/palette/list` — list saved palettes
- `DELETE /api/palette/<id>` — delete saved palette
- `GET /saved` — saved palettes gallery page
- `GET /api/export?colors=<csv>&format=<fmt>` — export palette as CSS/SCSS/Tailwind

### 3. Client-Side Features (`static/app.js`)

- Color picker (HTML5 `<input type="color">`) as base color selector
- Dropdown for harmony rule selection
- Live preview: colored swatches with hex/RGB/HSL labels
- Click-to-copy hex values
- Contrast checker: pick any two colors from palette, shows ratio + WCAG rating
- Export buttons: CSS custom properties, SCSS variables, Tailwind config snippet
- Save palette with custom name
- Responsive grid layout

### 4. Database (`database.py`)

```python
def init_db() -> None:
    """Create palettes table if not exists."""

def save_palette(name: str, colors: list[str]) -> int:
    """Save palette, return ID. Colors stored as JSON array."""

def list_palettes() -> list[dict]:
    """Return all palettes as [{id, name, colors, created_at}]."""

def delete_palette(palette_id: int) -> bool:
    """Delete palette by ID. Return True if deleted."""
```

Schema:
```sql
CREATE TABLE IF NOT EXISTS palettes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    colors TEXT NOT NULL,  -- JSON array of hex strings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Export Formats (`GET /api/export`)

- **CSS**: `--color-1: #hex; --color-2: #hex; ...`
- **SCSS**: `$color-1: #hex; $color-2: #hex; ...`
- **Tailwind**: `colors: { palette: { 100: '#hex', 200: '#hex', ... } }`

## UI Design Notes

- Dark background (#1a1a2e) with light text for color accuracy
- Swatches displayed as large rounded rectangles (120x120px)
- Hover shows RGB/HSL values
- Contrast checker section below palette with visual pass/fail indicators
- Mobile-friendly: swatches wrap on small screens

## Error Handling

- Invalid hex input → 400 with descriptive message
- Missing query params → 400 with usage hint
- Database errors → 500 with generic message (no leak)
- All API responses are JSON with `{success: bool, data/error: ...}` envelope
