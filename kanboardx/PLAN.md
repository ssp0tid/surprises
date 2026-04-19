# KanboardX Implementation Plan

## Project Overview

**Project Name:** KanboardX  
**Type:** Self-hosted Kanban board web application  
**Core Functionality:** Zero-external-dependency task management with drag-and-drop columns, markdown support, and dark theme UI  
**Target Users:** Individuals, small teams wanting local, private project management

---

## Technical Stack

- **Backend:** Python Flask (built-in, no pip dependencies required for core)
- **Storage:** Local JSON files
- **Frontend:** Embedded HTML/CSS/JS (single-file deployment)
- **Zero External Dependencies:** Python stdlib + Flask only

---

## File Structure

```
kanboardx/
├── kanboardx.py          # Main application (Flask server + frontend)
├── data/                 # JSON storage directory
│   ├── boards.json       # Board metadata
│   ├── cards.json       # All cards data
│   ├── labels.json       # Label definitions
│   └── config.json       # App configuration
├── logs/                 # Application logs
├── exports/              # CSV export outputs
└── README.md            # Documentation
```

---

## API Design

### Base URL: `/api/v1/`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/boards` | List all boards |
| GET | `/api/v1/board/<id>` | Get single board with columns |
| POST | `/api/v1/board` | Create new board |
| PUT | `/api/v1/board/<id>` | Update board |
| DELETE | `/api/v1/board/<id>` | Delete board |
| GET | `/api/v1/cards` | List all cards (with filters) |
| GET | `/api/v1/card/<id>` | Get single card |
| POST | `/api/v1/card` | Create new card |
| PUT | `/api/v1/card/<id>` | Update card (move, edit) |
| DELETE | `/api/v1/card/<id>` | Delete card |
| GET | `/api/v1/labels` | List all labels |
| POST | `/api/v1/labels` | Create label |
| DELETE | `/api/v1/labels/<id>` | Delete label |
| GET | `/api/v1/stats/<board_id>` | Get board statistics |
| GET | `/api/v1/export/<board_id>` | Export board to CSV |

### Data Models

#### Board
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "columns": [
    {"id": "uuid", "name": "To Do", "order": 0},
    {"id": "uuid", "name": "In Progress", "order": 1},
    {"id": "uuid", "name": "Done", "order": 2}
  ],
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

#### Card
```json
{
  "id": "uuid",
  "board_id": "uuid",
  "column_id": "uuid",
  "title": "string",
  "description": "string (markdown)",
  "position": 0,
  "priority": "low|medium|high|urgent",
  "labels": ["uuid"],
  "due_date": "YYYY-MM-DD or null",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "completed_at": "ISO8601 or null"
}
```

#### Label
```json
{
  "id": "uuid",
  "name": "string",
  "color": "#hexcode"
}
```

---

## Features & Implementation Details

### 1. Drag-and-Drop Task Management

**Frontend:**
- HTML5 Drag and Drop API
- Visual feedback: card opacity, drop zone highlighting
- Touch support via pointer events

**Backend:**
- PUT `/api/v1/card/<id>` with `column_id` and `position`
- Reorder all cards in column on drop
- Optimistic UI update with rollback on failure

**Edge Cases:**
- Drop on same position: no-op
- Drop on deleted column: return 400 error
- Rapid drags: debounce API calls (300ms)

### 2. Markdown Support

**Libraries:** None (zero dependencies)
- Parse markdown using regex-based custom parser
- Support: headings, bold, italic, code blocks, links, lists

**Display:**
- Render on card view/modal
- Raw text on card preview (truncated)
- XSS prevention: sanitize HTML output

**Security:**
- Escape HTML entities in user input
- No iframe, script, or event handler rendering
- Content Security Policy header

### 3. Dark Theme Responsive UI

**CSS Variables:**
```css
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-card: #0f3460;
  --text-primary: #e8e8e8;
  --text-secondary: #a0a0a0;
  --accent: #e94560;
  --success: #4ecca3;
  --warning: #f39c12;
  --danger: #e74c3c;
  --low: #95a5a6;
  --medium: #3498db;
  --high: #e67e22;
  --urgent: #e74c3c;
}
```

**Responsive Breakpoints:**
- Mobile: < 640px (single column view)
- Tablet: 640px - 1024px (horizontal scroll)
- Desktop: > 1024px (full grid)

### 4. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `N` | New card (focuses input) |
| `F` | Focus search |
| `Esc` | Close modal/clear search |
| `E` | Edit selected card |
| `D` | Delete selected card |
| `←/→` | Navigate columns |
| `↑/↓` | Navigate cards |
| `Enter` | Open card detail |
| `Ctrl+S` | Save (in edit mode) |

**Implementation:**
- Global event listener on document
- Visual shortcut hints in UI
- Customizable (future: store in config)

### 5. CSV Export

**Format:**
```
Title,Description,Column,Priority,Labels,Due Date,Created,Completed
```

**Implementation:**
- Server generates CSV on request
- Proper CSV escaping (quotes, newlines)
- UTF-8 with BOM for Excel compatibility

**Endpoint:** `GET /api/v1/export/<board_id>`

### 6. Card Search/Filter

**Search Parameters:**
- `q`: Text search in title/description
- `priority`: Filter by priority
- `label`: Filter by label
- `due`: Filter by due date (overdue, today, this-week)
- `column`: Filter by column

**Implementation:**
- Server-side filtering (JSON query)
- Debounced search (300ms)
- Highlight matching text in results

### 7. Priority Tags

| Priority | Color | Icon |
|----------|-------|------|
| Low | #95a5a6 | ○ |
| Medium | #3498db | ◐ |
| High | #e67e22 | ● |
| Urgent | #e74c3c | ⚠ |

**Display:**
- Color-coded badge on card
- Sort by priority option
- Filter by priority

### 8. Due Dates

**Features:**
- Date picker (native `<input type="date">`)
- Visual indicators: overdue (red), today (yellow), future (default)
- Due date on card preview

**Validation:**
- Prevent past dates on create (warning only, allow override)
- Timezone: store as UTC, display in local

### 9. Card Labels/Tags

**Features:**
- Create custom labels with colors
- Multiple labels per card
- Filter by label
- Label management UI

### 10. Board Statistics Sidebar

**Stats Displayed:**
- Total cards
- Cards per column
- Overdue cards count
- Cards by priority (pie/bar)
- Completion rate (% cards in Done)
- Average time in "In Progress"

**Implementation:**
- Computed from cards.json
- Real-time update on card changes

---

## Error Handling

### HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (invalid data) |
| 404 | Not found |
| 409 | Conflict (duplicate) |
| 500 | Server error |

### Error Response Format

```json
{
  "error": "error_type",
  "message": "human readable message",
  "code": 400
}
```

### Common Errors

- **File lock:** Retry with exponential backoff (3 attempts)
- **Corrupt JSON:** Backup and recreate, log error
- **Disk full:** Return 507 Insufficient Storage
- **Concurrent edit:** Last-write-wins with timestamp check

---

## Edge Cases

1. **Empty board:** Show "Add your first column" prompt
2. **No columns:** Prevent card creation, require column first
3. **Long titles:** Truncate with ellipsis (max 100 chars display)
4. **Large descriptions:** Truncate in preview, full in modal
5. **Special characters:** Proper escaping in JSON and HTML
6. **Offline/Slow network:** Show loading states, timeout after 10s
7. **Browser refresh:** Restore state from server on load
8. **Multiple tabs:** Sync via polling (every 5s) or localStorage events
9. **Data migration:** Version field in JSON, migration functions on load

---

## Testing Strategy

### Unit Tests (Python)

```python
# test_kanboardx.py
- test_card_crud_operations
- test_board_crud_operations
- test_json_file_locking
- test_markdown_parser
- test_csv_export
- test_search_filter
- test_priority_sorting
- test_date_validation
```

### Frontend Tests

- Manual browser testing matrix:
  - Chrome, Firefox, Safari, Edge
  - Mobile (iOS Safari, Chrome Android)
- Keyboard shortcut testing
- Drag-and-drop testing

### Integration Tests

- Full API workflow: create board → add column → add card → move → export
- Error scenarios: network failure, invalid JSON, disk full

### Test Data

```json
{
  "boards": [{"name": "Test Board"}],
  "cards": [
    {"title": "Urgent Task", "priority": "urgent"},
    {"title": "Low Priority", "priority": "low"},
    {"title": "With Due Date", "due_date": "2024-01-01"}
  ]
}
```

---

## Security Considerations

1. **XSS Prevention:** Sanitize all user input and output
2. **CSRF:** Flask-WTF tokens for forms
3. **Rate Limiting:** 60 requests/minute per IP
4. **Data Isolation:** Each board accessible only to local users
5. **File Permissions:** Data directory readable only by server user
6. **No external requests:** Entirely offline capable

---

## Deployment

### Requirements
- Python 3.8+ (standard library + Flask)
- No system dependencies

### Running

```bash
# Direct
python kanboardx.py

# With custom port
python kanboardx.py --port 8080

# With custom data directory
python kanboardx.py --data /path/to/data
```

### Access

```
http://localhost:5000
```

---

## Future Enhancements (Out of Scope)

- User authentication/multi-user
- Real-time WebSocket sync
- Card comments
- File attachments
- Multiple boards view
- Board templates
- Print/printable views
- Keyboard shortcut customization