# SubTrak — Subscription Expense Tracker

**One-line:** Web-based SaaS for tracking recurring subscriptions, visualizing monthly/yearly spend, and alerting on upcoming renewals.

## Tech Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite (via sqlite3 stdlib)
- **Frontend:** Embedded HTML/CSS/JS (Jinja2 templates, Chart.js CDN, TailwindCSS CDN)
- **No external Python deps beyond Flask** (use venv)

## File Structure

```
subtrak/
├── PLAN.md
├── README.md
├── requirements.txt          # flask only
├── app.py                    # Entry point — Flask app, routes, DB init
├── templates/
│   ├── base.html             # Layout with nav, TailwindCSS CDN
│   ├── dashboard.html        # Overview: total spend, charts, upcoming renewals
│   ├── subscriptions.html    # List all subscriptions with CRUD
│   ├── add.html              # Add/edit subscription form
│   └── analytics.html        # Spending breakdown charts
├── static/
│   └── app.js                # Client-side JS (chart rendering, delete confirm)
└── subtrak.db                # Created at runtime
```

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                    -- e.g. "Netflix"
    category TEXT NOT NULL DEFAULT 'other', -- entertainment, productivity, dev-tools, cloud, music, other
    amount REAL NOT NULL,                  -- per-cycle cost
    currency TEXT NOT NULL DEFAULT 'USD',  -- USD, EUR, GBP
    billing_cycle TEXT NOT NULL DEFAULT 'monthly', -- monthly, yearly, weekly
    next_renewal DATE NOT NULL,            -- YYYY-MM-DD
    url TEXT DEFAULT '',                   -- service URL
    notes TEXT DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1,     -- 1=active, 0=paused
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Features

### 1. Dashboard (GET /)
- Total monthly spend (normalize yearly/weekly to monthly equivalent)
- Count of active subscriptions
- Next 5 upcoming renewals (sorted by next_renewal date)
- Doughnut chart: spend by category
- Line chart: projected 12-month cumulative spend

### 2. Subscription List (GET /subscriptions)
- Table with columns: Name, Category, Amount, Cycle, Next Renewal, Status, Actions
- Filter by category (dropdown)
- Sort by amount or renewal date
- Toggle active/paused status (POST /subscriptions/<id>/toggle)
- Delete with confirmation (DELETE /subscriptions/<id>)

### 3. Add/Edit Subscription (GET/POST /subscriptions/add, GET/POST /subscriptions/<id>/edit)
- Form fields: name, category (select), amount, currency (select), billing_cycle (select), next_renewal (date picker), url, notes
- Server-side validation: name required, amount > 0, valid date
- On save, redirect to /subscriptions with flash message

### 4. Analytics (GET /analytics)
- Bar chart: monthly spend by category
- Pie chart: subscription count by category
- Summary stats: avg cost per subscription, most expensive, cheapest
- Year-over-year projection

### 5. API Endpoints (JSON)
- GET /api/stats — returns {total_monthly, total_yearly, count, by_category: {...}}
- GET /api/upcoming?days=30 — subscriptions renewing within N days

## Implementation Notes

### app.py structure:
```python
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = 'subtrak-dev-key'
DATABASE = 'subtrak.db'

def get_db():
    """Get database connection with row factory."""

def init_db():
    """Create tables if not exist."""

def normalize_to_monthly(amount, cycle):
    """Convert any billing cycle to monthly equivalent."""
    # weekly * 4.33, yearly / 12, monthly * 1

@app.route('/')
def dashboard(): ...

@app.route('/subscriptions')
def list_subscriptions(): ...

@app.route('/subscriptions/add', methods=['GET', 'POST'])
def add_subscription(): ...

@app.route('/subscriptions/<int:id>/edit', methods=['GET', 'POST'])
def edit_subscription(id): ...

@app.route('/subscriptions/<int:id>/delete', methods=['POST'])
def delete_subscription(id): ...

@app.route('/subscriptions/<int:id>/toggle', methods=['POST'])
def toggle_subscription(id): ...

@app.route('/api/stats')
def api_stats(): ...

@app.route('/api/upcoming')
def api_upcoming(): ...

@app.route('/analytics')
def analytics(): ...

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
```

### Chart.js usage in templates:
- Load from CDN: https://cdn.jsdelivr.net/npm/chart.js
- Render data via Jinja2 into JS variables: `const chartData = {{ data | tojson }};`

### Normalization logic:
- weekly → monthly: amount * (52/12)
- monthly → monthly: amount * 1
- yearly → monthly: amount / 12

## Constraints

- Single `app.py` entry point (all routes in one file)
- No external API keys required
- No heavy dependencies — Flask only in requirements.txt
- Must work with `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python3 app.py`
- All CSS via TailwindCSS CDN (no build step)
- All charts via Chart.js CDN
- SQLite file created in project directory (not /tmp)
- Responsive design (mobile-friendly)
