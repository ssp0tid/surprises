# Color Palette Studio

Web-based color palette generator with harmony rules, contrast checking, and multi-format export.

## Requirements

- Python 3.10+
- Flask

## Setup

```bash
pip install flask
```

## Run

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Features

- **Color Harmony Generator** — complementary, analogous, triadic, split-complementary, tetradic, monochromatic
- **WCAG Contrast Checker** — calculates contrast ratio and rates AA/AAA compliance
- **Export** — CSS custom properties, SCSS variables, Tailwind config
- **Save Palettes** — persist palettes to local SQLite database
- **Click-to-Copy** — click any swatch to copy its hex value

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/harmony?base=<hex>&rule=<rule>` | Generate palette |
| GET | `/api/contrast?color1=<hex>&color2=<hex>` | Check WCAG contrast |
| GET | `/api/random` | Random base color |
| POST | `/api/palette/save` | Save palette (JSON: `{name, colors[]}`) |
| GET | `/api/palette/list` | List saved palettes |
| DELETE | `/api/palette/<id>` | Delete palette |
| GET | `/api/export?colors=<csv>&format=<fmt>` | Export (css/scss/tailwind) |

## File Structure

```
color-palette-studio/
├── app.py              # Flask app — routes, API, entry point
├── color_engine.py     # Color math: conversions, harmony, contrast
├── database.py         # SQLite palette storage
├── templates/
│   ├── index.html      # Main workspace
│   └── saved.html      # Saved palettes gallery
└── static/
    ├── style.css       # UI styling
    └── app.js          # Client-side interactivity
```
