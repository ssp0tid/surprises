# ReqBench

**One-line:** Self-hosted web-based HTTP request builder and API tester — build requests, inspect responses, save collections, view history.

## Tech Stack

- Python 3 + Flask
- SQLite (via sqlite3 stdlib)
- Vanilla JavaScript (no frameworks)
- TailwindCSS (CDN)
- No external Python dependencies beyond Flask and requests

## File Structure

```
reqbench/
├── PLAN.md
├── README.md
├── requirements.txt
├── app.py                  # Flask application entry point
├── database.py             # SQLite schema and helpers
├── static/
│   ├── app.js              # Frontend logic
│   └── style.css           # Custom styles (minimal, Tailwind handles most)
└── templates/
    └── index.html          # Single-page app template
```

## Features

### 1. Request Builder (Core)
- Method selector: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
- URL input with protocol prefix
- Headers editor: key-value pairs, add/remove rows dynamically
- Body editor: raw JSON, form-data (key-value), or plain text
- Query params editor: key-value pairs auto-appended to URL
- Content-Type auto-set based on body type selection

### 2. Response Viewer
- Status code with color coding (2xx green, 3xx blue, 4xx yellow, 5xx red)
- Response headers displayed as table
- Response body with JSON pretty-printing and syntax highlighting (basic)
- Response time in milliseconds
- Response size in bytes

### 3. Collections
- Save requests to named collections (e.g., "My API", "Auth Endpoints")
- Each saved request stores: name, method, url, headers, body, params
- Load saved request back into builder
- Delete saved requests
- SQLite table: `collections(id, collection_name, request_name, method, url, headers_json, body, body_type, params_json, created_at)`

### 4. History
- Auto-save last 100 requests with responses
- Show timestamp, method, url, status code, duration
- Click to reload request into builder
- Clear history button
- SQLite table: `history(id, method, url, headers_json, body, body_type, params_json, status_code, response_headers_json, response_body, duration_ms, response_size, created_at)`

### 5. Environment Variables
- Define variables like `{{base_url}}`, `{{token}}`
- Variables interpolated in URL, headers, and body before sending
- SQLite table: `environments(id, name, variables_json, created_at)`
- Active environment selector in UI

## API Endpoints (Flask)

```python
# Request execution
POST /api/send          # Execute HTTP request, return response
  Body: { method, url, headers, body, body_type, params }
  Returns: { status_code, headers, body, duration_ms, size_bytes }

# Collections
GET    /api/collections              # List all collections and their requests
POST   /api/collections              # Save request to collection
DELETE /api/collections/<id>         # Delete saved request

# History
GET    /api/history                  # Get last 100 history entries
DELETE /api/history                  # Clear all history

# Environments
GET    /api/environments             # List environments
POST   /api/environments             # Create/update environment
DELETE /api/environments/<id>        # Delete environment
```

## Implementation Notes

### app.py
- Flask app with JSON API routes
- `send_request()` uses `requests` library to proxy the HTTP call
- Timeout of 30s on outgoing requests
- Catches connection errors, timeouts — returns structured error
- CORS not needed (same-origin)
- Runs on port 5111

### database.py
- `init_db()` creates tables if not exist
- `get_db()` returns connection with row_factory = sqlite3.Row
- History auto-prunes to 100 entries on insert
- All JSON fields stored as TEXT (json.dumps/loads)

### static/app.js
- Single-page app logic
- `sendRequest()` — collects form data, POSTs to /api/send, renders response
- `addHeaderRow()` / `addParamRow()` — dynamic key-value pair management
- `saveToCollection()` / `loadFromCollection()` — collection CRUD
- `loadHistory()` — fetch and render history sidebar
- `interpolateVariables(text)` — replace `{{var}}` with active env values
- Tab switching: Builder | History | Collections | Environments

### templates/index.html
- TailwindCSS via CDN
- Layout: left sidebar (history/collections), main area (request builder + response)
- Tabs for switching body type (JSON/Form/Text)
- Response panel below request builder

## Constraints

- No external API keys required
- Single `pip install flask requests` for dependencies
- SQLite database stored as `reqbench.db` in project directory
- No authentication (local tool)
- Max response body stored: 1MB (truncate larger responses in history)
