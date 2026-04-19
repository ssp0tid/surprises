# KanboardX

A self-hosted Kanban board application built with Flask. Zero external frontend dependencies, beautiful dark theme, and full drag-and-drop task management.

## Requirements

- Python 3.8+
- Flask >= 2.3.0

## Installation

```bash
pip install -r requirements.txt
```

## Running the App

```bash
python kanboardx.py
```

The app will start on `http://localhost:5000` by default.

### Command Line Options

```bash
python kanboardx.py --port 8080      # Run on custom port
python kanboardx.py --host 127.0.0.1  # Bind to specific host
python kanboardx.py --data /path/to/data  # Custom data directory
```

## Features

### Boards & Columns
- Create multiple boards with default columns
- Default columns: To Do, In Progress, Done
- Default columns are created automatically when creating a board

### Cards
- Drag-and-drop between columns
- Priority levels: Low, Medium, High, Urgent
- Due dates with visual indicators (overdue, today, future)
- Custom labels with colors
- Markdown descriptions (headings, bold, italic, code, links, lists)

### Search & Filter
- Real-time search across titles and descriptions
- Filter by priority, label, due date
- Debounced search (300ms)

### Export
- CSV export with UTF-8 BOM for Excel compatibility
- All card data included

### Statistics
- Total cards count
- Cards by column
- Completion rate
- Priority distribution
- Overdue count

### Keyboard Shortcuts

| Key | Action |
|-----|-------|
| `N` | New card |
| `F` | Focus search |
| `Esc` | Close modal / Clear search |
| `Enter` | Open selected card |
| `E` | Edit selected card |
| `D` | Delete selected card |
| `Ctrl+S` | Save (in edit mode) |

## API Documentation

### Boards

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/boards` | List all boards |
| GET | `/api/v1/board/<id>` | Get single board |
| POST | `/api/v1/board` | Create board |
| PUT | `/api/v1/board/<id>` | Update board |
| DELETE | `/api/v1/board/<id>` | Delete board |

### Cards

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/cards` | List cards (filters: board_id, column_id, priority, label, due, q) |
| GET | `/api/v1/card/<id>` | Get single card |
| POST | `/api/v1/card` | Create card |
| PUT | `/api/v1/card/<id>` | Update card |
| DELETE | `/api/v1/card/<id>` | Delete card |

### Labels

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/labels` | List all labels |
| POST | `/api/v1/labels` | Create label |
| DELETE | `/api/v1/labels/<id>` | Delete label |

### Other

| Method | Endpoint | Description |
|--------|----------|------------|
| GET | `/api/v1/stats/<board_id>` | Get board statistics |
| GET | `/api/v1/export/<board_id>` | Export board to CSV |

## Data Storage

Data is stored in JSON files in the `data/` directory:
- `boards.json` - Board metadata
- `cards.json` - All cards
- `labels.json` - Label definitions
- `config.json` - App configuration

## Security

- Content Security Policy headers
- XSS prevention (HTML escaping)
- File locking for concurrent access

## Tech Stack

- Backend: Python Flask
- Storage: JSON files
- Frontend: Vanilla HTML/CSS/JS (no dependencies)
- Markdown: Custom regex parser

## License

MIT