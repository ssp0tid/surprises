# PixelForge

**One-line:** Browser-based pixel art editor with layers, tools, animation frames, and PNG/GIF export.

## Tech Stack

- Python 3 + Flask (backend — serves app, handles save/load/export)
- SQLite (project persistence — save/load pixel art projects)
- Vanilla JavaScript + HTML5 Canvas (frontend — all drawing logic)
- TailwindCSS CDN (styling)
- No external npm build step — single-page app served by Flask

## Constraints

- No external API keys required
- All drawing happens client-side on Canvas
- SQLite for project storage (save/load)
- Python virtual environment for Flask dependency
- Entry point: `app.py`

## File Structure

```
pixelforge/
├── PLAN.md
├── README.md
├── requirements.txt
├── app.py                  # Flask server — routes, API endpoints
├── database.py             # SQLite schema + CRUD operations
├── pixelforge.db           # (created at runtime)
├── static/
│   ├── css/
│   │   └── style.css       # Custom styles beyond Tailwind
│   ├── js/
│   │   ├── app.js          # Main app initialization, event wiring
│   │   ├── canvas.js       # Canvas rendering, pixel grid, zoom/pan
│   │   ├── tools.js        # Drawing tools (pencil, eraser, fill, line, rect, circle, eyedropper)
│   │   ├── layers.js       # Layer management (add, remove, reorder, opacity, visibility)
│   │   ├── palette.js      # Color palette management, recent colors
│   │   ├── animation.js    # Frame management, onion skinning, playback
│   │   └── export.js       # PNG export (single frame), GIF export (animation)
│   └── img/
│       └── favicon.png     # 16x16 pixel art icon
└── templates/
    └── index.html          # Main SPA template
```

## Features

### 1. Canvas & Grid
- Configurable canvas size: 8x8, 16x16, 32x32, 64x64, 128x128
- Pixel grid overlay (toggleable)
- Zoom (mouse wheel) from 1x to 32x
- Pan (middle mouse or spacebar + drag)
- Cursor preview shows current tool shape

### 2. Drawing Tools
Each tool is a class in `tools.js` with `onMouseDown`, `onMouseMove`, `onMouseUp` methods:

- **Pencil** — draw single pixels, hold shift for straight lines
- **Eraser** — set pixels to transparent
- **Bucket Fill** — flood fill using BFS algorithm (4-connected)
- **Line** — click-drag to draw pixel-perfect line (Bresenham's algorithm)
- **Rectangle** — click-drag for outlined or filled rectangle
- **Circle** — click-drag for outlined or filled circle (midpoint algorithm)
- **Eyedropper** — pick color from canvas
- **Selection** — rectangular selection, move/copy/delete

### 3. Layers
- Up to 8 layers per project
- Each layer: `{ id, name, pixels: Uint8ClampedArray, opacity: 0-100, visible: bool }`
- Reorder via drag-and-drop in layer panel
- Merge down, duplicate, flatten all
- Composite rendering: bottom-to-top with alpha blending

### 4. Color Palette
- HSL color picker (hue wheel + saturation/lightness square)
- Hex input field
- 16 preset colors (standard pixel art palette)
- Recent colors (last 16 used)
- Swap foreground/background with X key

### 5. Animation
- Multiple frames (up to 64)
- Onion skinning (show previous/next frame as ghost)
- Frame duration (ms per frame, configurable per-frame)
- Playback preview in a popup canvas
- Duplicate/delete frames

### 6. Export
- **PNG** — export current frame at 1x or scaled (2x, 4x, 8x, 16x)
- **Spritesheet** — all frames in a horizontal strip PNG
- **GIF** — animated GIF from all frames (server-side using Pillow)

### 7. Save/Load (API)
- `POST /api/projects` — create new project (returns project_id)
- `GET /api/projects` — list saved projects
- `GET /api/projects/<id>` — load project (all layers, frames, settings)
- `PUT /api/projects/<id>` — save project state
- `DELETE /api/projects/<id>` — delete project
- Project data stored as JSON blob in SQLite

### 8. Keyboard Shortcuts
- B: Pencil, E: Eraser, G: Fill, L: Line, R: Rectangle, C: Circle, I: Eyedropper
- Ctrl+Z: Undo, Ctrl+Y: Redo (history stack, max 50 states)
- Ctrl+S: Save project
- +/-: Zoom in/out
- Space+drag: Pan

## Database Schema (database.py)

```python
def init_db(db_path: str):
    """Create projects table if not exists."""
    # Table: projects
    # - id INTEGER PRIMARY KEY AUTOINCREMENT
    # - name TEXT NOT NULL
    # - width INTEGER NOT NULL
    # - height INTEGER NOT NULL
    # - data TEXT NOT NULL (JSON: {layers: [...], frames: [...], palette: [...]})
    # - created_at TEXT DEFAULT CURRENT_TIMESTAMP
    # - updated_at TEXT DEFAULT CURRENT_TIMESTAMP

def create_project(name: str, width: int, height: int) -> int: ...
def get_project(project_id: int) -> dict | None: ...
def list_projects() -> list[dict]: ...
def update_project(project_id: int, data: str) -> bool: ...
def delete_project(project_id: int) -> bool: ...
```

## API Routes (app.py)

```python
@app.route('/')  # Serve index.html
@app.route('/api/projects', methods=['GET', 'POST'])
@app.route('/api/projects/<int:pid>', methods=['GET', 'PUT', 'DELETE'])
@app.route('/api/export/gif', methods=['POST'])  # Receive frames JSON, return GIF binary
```

## Implementation Notes

- Canvas uses `OffscreenCanvas` or regular Canvas with `getImageData`/`putImageData` for pixel manipulation
- Each layer's pixel data is a flat RGBA array: `new Uint8ClampedArray(width * height * 4)`
- Undo/redo stores full layer snapshots (simple but memory-safe for small canvases)
- GIF export on server uses Pillow: receive base64 frame PNGs, compose GIF with frame durations
- All state lives in a global `AppState` object in `app.js`
- Tools register via `ToolManager.register(name, toolInstance)`
- Responsive layout: tools panel left, canvas center, layers/colors right
