# Pollcraft

Real-time poll and survey builder with live results visualization.

## Quick Start

```bash
pip install flask
python3 app.py
```

Open http://localhost:5000 in your browser.

## Features

- Create single-choice or multiple-choice polls
- Share polls via unique links (no login required)
- Live results with Chart.js bar charts updated via Server-Sent Events
- IP-based duplicate vote detection
- Optional comments on polls
- Admin management via secret token (close/delete polls)

## Tech Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite (stdlib `sqlite3`)
- **Real-time:** Server-Sent Events (SSE)
- **Frontend:** Vanilla HTML/CSS/JS + Chart.js + TailwindCSS (CDN)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/polls | Create poll |
| POST | /api/polls/\<slug\>/vote | Submit vote |
| GET | /api/polls/\<slug\>/results | Get results JSON |
| GET | /api/polls/\<slug\>/stream | SSE live stream |
| POST | /api/polls/\<slug\>/close | Close poll (admin) |
| DELETE | /api/polls/\<slug\> | Delete poll (admin) |
| GET | /api/polls/\<slug\>/comments | Get comments |
| POST | /api/polls/\<slug\>/comments | Add comment |

## Admin Access

When you create a poll, you receive an `admin_token`. Use it to:
- Close the poll: `POST /api/polls/<slug>/close` with `X-Admin-Token` header
- Delete the poll: `DELETE /api/polls/<slug>` with `X-Admin-Token` header
- Or visit the management page: `/manage/<slug>?token=<admin_token>`

## Configuration

Runs on port 5000 by default. The SQLite database (`pollcraft.db`) is created automatically on first run.
