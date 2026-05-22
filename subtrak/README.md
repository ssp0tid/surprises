# SubTrak — Subscription Expense Tracker

A web-based tool for tracking recurring subscriptions, visualizing monthly/yearly spend, and monitoring upcoming renewals.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open http://localhost:5000 in your browser.

## Features

- **Dashboard** — Total monthly/yearly spend, upcoming renewals, category breakdown chart, 12-month projection
- **Subscription Management** — Add, edit, delete, pause/activate subscriptions with filtering and sorting
- **Analytics** — Spend by category (bar chart), subscription count by category (pie chart), summary stats
- **API Endpoints** — JSON endpoints for stats and upcoming renewals

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Total monthly/yearly spend, count, breakdown by category |
| `/api/upcoming?days=30` | GET | Subscriptions renewing within N days |

## Tech Stack

- Python 3 + Flask
- SQLite (stdlib)
- TailwindCSS (CDN)
- Chart.js (CDN)

## File Structure

```
subtrak/
├── app.py                 # Flask app, routes, DB init
├── requirements.txt       # flask only
├── templates/
│   ├── base.html          # Layout with nav
│   ├── dashboard.html     # Overview + charts
│   ├── subscriptions.html # List with CRUD
│   ├── add.html           # Add/edit form
│   └── analytics.html     # Spending charts
└── static/
    └── app.js             # Chart rendering, delete confirmation
```
