# ReqBench

Self-hosted web-based HTTP request builder and API tester. Build requests, inspect responses, save collections, view history.

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5111 in your browser.

## Features

- **Request Builder** — GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS with headers, query params, and body (JSON/Form/Text)
- **Response Viewer** — Status codes, headers, body with JSON pretty-printing, timing, and size
- **Collections** — Save and organize requests into named groups
- **History** — Auto-saved last 100 requests with one-click reload
- **Environment Variables** — Define `{{variable}}` placeholders interpolated across URL, headers, and body

## Tech Stack

- Python 3 + Flask
- SQLite (stdlib)
- Vanilla JavaScript
- TailwindCSS (CDN)

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/send` | POST | Execute HTTP request |
| `/api/collections` | GET | List saved requests |
| `/api/collections` | POST | Save request to collection |
| `/api/collections/<id>` | DELETE | Delete saved request |
| `/api/history` | GET | Get last 100 history entries |
| `/api/history` | DELETE | Clear all history |
| `/api/environments` | GET | List environments |
| `/api/environments` | POST | Create/update environment |
| `/api/environments/<id>` | DELETE | Delete environment |

## Data

SQLite database stored as `reqbench.db` in the project directory. No authentication — intended as a local development tool.
