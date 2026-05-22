# PixelForge

Browser-based pixel art editor with layers, tools, animation frames, and PNG/GIF export.

## Features

- Configurable canvas sizes (8×8 to 128×128) with zoom and pan
- Drawing tools: pencil, eraser, bucket fill, line, rectangle, circle, eyedropper, selection
- Up to 8 layers per frame with opacity, visibility, reorder, merge, and flatten
- HSL color picker, hex input, 16 preset colors, recent colors history
- Animation: up to 64 frames, onion skinning, per-frame duration, playback preview
- Export: PNG (scaled), spritesheet, animated GIF (server-side via Pillow)
- Save/load projects to SQLite database
- Keyboard shortcuts for all tools and common actions

## Requirements

- Python 3.10+
- pip

## Setup

```bash
cd pixelforge
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| B | Pencil |
| E | Eraser |
| G | Bucket Fill |
| L | Line |
| R | Rectangle |
| C | Circle |
| I | Eyedropper |
| M | Selection |
| X | Swap foreground/background |
| +/- | Zoom in/out |
| Space+drag | Pan |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+S | Save project |
| Delete | Delete selection |
| Shift+drag | Filled rectangle/circle (with R or C tool) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List saved projects |
| POST | `/api/projects` | Create new project |
| GET | `/api/projects/<id>` | Load project |
| PUT | `/api/projects/<id>` | Save project state |
| DELETE | `/api/projects/<id>` | Delete project |
| POST | `/api/export/gif` | Export animated GIF |
