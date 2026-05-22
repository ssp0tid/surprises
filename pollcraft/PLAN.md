# Pollcraft

**Real-time poll and survey builder with live results visualization.**

A web-based SaaS app where users create polls/surveys, share them via unique links, collect votes, and see results update in real-time via Server-Sent Events (SSE). No login required — polls are identified by unique slugs.

## Tech Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite (via sqlite3 stdlib)
- **Real-time:** Server-Sent Events (SSE) for live result updates
- **Frontend:** Vanilla HTML/CSS/JS + Chart.js for visualizations
- **CSS:** TailwindCSS via CDN
- **No external Python deps beyond Flask**

## File Structure

```
pollcraft/
├── PLAN.md
├── README.md
├── app.py              # Main Flask application (entry point)
├── database.py         # SQLite schema, connection, queries
├── templates/
│   ├── base.html       # Base template with nav, TailwindCSS CDN
│   ├── index.html      # Landing page — create new poll
│   ├── create.html     # Poll creation form
│   ├── vote.html       # Voting page (public link)
│   ├── results.html    # Live results with Chart.js
│   └── manage.html     # Poll management (close/delete with admin token)
└── static/
    └── app.js          # Client-side JS (SSE listener, chart rendering, form validation)
```

## Database Schema

```sql
CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,          -- 8-char random slug for public URL
    admin_token TEXT NOT NULL,          -- 16-char token for management
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    poll_type TEXT NOT NULL DEFAULT 'single',  -- 'single' or 'multiple'
    created_at TEXT DEFAULT (datetime('now')),
    closed_at TEXT DEFAULT NULL,
    allow_comments INTEGER DEFAULT 0
);

CREATE TABLE options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
);

CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    voter_ip TEXT NOT NULL,
    voted_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE,
    FOREIGN KEY (option_id) REFERENCES options(id) ON DELETE CASCADE
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    author TEXT DEFAULT 'Anonymous',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
);
```

## Features

### 1. Poll Creation (`POST /api/polls`)
- Title (required, max 200 chars)
- Description (optional, max 1000 chars)
- Options (2-20 items, each max 200 chars)
- Type: single-choice or multiple-choice
- Allow comments toggle
- Returns: `{ slug, admin_token, vote_url, results_url }`

### 2. Voting (`POST /api/polls/<slug>/vote`)
- IP-based duplicate detection (one vote per IP per poll)
- Validates poll is not closed
- Validates option IDs belong to poll
- For multiple-choice: accepts array of option_ids

### 3. Live Results (`GET /api/polls/<slug>/stream`)
- SSE endpoint that pushes updated vote counts whenever a new vote arrives
- Data format: `{ options: [{id, text, votes}], total_votes, poll_type }`
- Client renders as bar chart (Chart.js) + percentage labels

### 4. Poll Management (`POST /api/polls/<slug>/close`, `DELETE /api/polls/<slug>`)
- Requires admin_token in request header
- Close: sets closed_at, stops accepting votes
- Delete: removes poll and all associated data

### 5. Comments (`GET/POST /api/polls/<slug>/comments`)
- Optional per-poll (allow_comments flag)
- Anonymous or named
- Displayed below results

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | / | Landing page |
| GET | /create | Poll creation form |
| POST | /api/polls | Create poll |
| GET | /p/<slug> | Vote page |
| POST | /api/polls/<slug>/vote | Submit vote |
| GET | /r/<slug> | Results page |
| GET | /api/polls/<slug>/stream | SSE results stream |
| GET | /api/polls/<slug>/results | JSON results |
| POST | /api/polls/<slug>/close | Close poll (admin) |
| DELETE | /api/polls/<slug> | Delete poll (admin) |
| GET | /api/polls/<slug>/comments | Get comments |
| POST | /api/polls/<slug>/comments | Add comment |
| GET | /manage/<slug>?token=<admin_token> | Management page |

## Key Implementation Notes

### app.py
- `generate_slug()`: uses `secrets.token_urlsafe(6)` → 8 chars
- `generate_admin_token()`: uses `secrets.token_urlsafe(12)` → 16 chars
- SSE uses Flask's `Response` with `mimetype='text/event-stream'` and generator
- IP detection: `request.headers.get('X-Forwarded-For', request.remote_addr)`
- All API endpoints return JSON with appropriate status codes
- Error handler for 404, 400, 500

### database.py
- `init_db()`: creates tables if not exist
- `get_db()`: returns connection with row_factory = sqlite3.Row
- `create_poll(title, description, options, poll_type, allow_comments)` → (slug, admin_token)
- `get_poll(slug)` → poll dict or None
- `get_options(poll_id)` → list of options with vote counts
- `cast_vote(poll_id, option_ids, voter_ip)` → bool (False if already voted)
- `close_poll(slug, admin_token)` → bool
- `delete_poll(slug, admin_token)` → bool
- `add_comment(poll_id, text, author)` → comment dict
- `get_comments(poll_id)` → list

### static/app.js
- `initSSE(slug)`: connects to SSE endpoint, updates chart on message
- `renderChart(data)`: Chart.js horizontal bar chart with vote counts
- `validateForm()`: ensures 2+ options, title not empty
- `addOption()` / `removeOption()`: dynamic form fields
- `submitVote(slug)`: AJAX POST, shows thank-you or error

### Templates
- base.html: TailwindCSS CDN, Chart.js CDN, nav with "Pollcraft" branding
- create.html: dynamic form with add/remove option buttons
- vote.html: radio buttons (single) or checkboxes (multiple), submit button
- results.html: Chart.js canvas + SSE connection + comment section
- manage.html: shows admin controls (close poll, delete poll, share links)

## Constraints

- No external Python packages beyond Flask (use stdlib sqlite3, secrets, json, datetime)
- No authentication system — admin access via token in URL
- SQLite only — no migrations, schema created on first run
- Single-file backend (app.py) imports from database.py
- All templates use Jinja2
- Chart.js and TailwindCSS loaded from CDN (no build step)
- Runs on port 5000 by default: `python3 app.py`
