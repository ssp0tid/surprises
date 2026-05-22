# Invoicely — Web-Based Invoice Generator

A self-hosted web app for creating, managing, and exporting professional PDF invoices with client management and payment tracking.

## Tech Stack

- **Backend:** Python 3 / Flask
- **Database:** SQLite (stdlib `sqlite3`)
- **PDF Generation:** WeasyPrint (optional — falls back to printable HTML)
- **Frontend:** Vanilla JS + TailwindCSS (CDN) + Jinja2 templates

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python3 app.py
```

The app starts on [http://localhost:5000](http://localhost:5000).

The SQLite database (`invoicely.db`) is created automatically on first run.

## Features

- **Client Management** — Create, edit, delete clients with full contact details
- **Invoice Creation** — Auto-numbered invoices (INV-YYYYMMDD-NNN) with line items
- **Status Tracking** — Draft → Sent → Paid / Overdue with color-coded badges
- **PDF Export** — Download invoices as PDF (requires WeasyPrint) or print-friendly HTML
- **Dashboard** — Revenue totals, outstanding amounts, status counts, recent invoices
- **Filtering** — Filter invoices by status, client, and date range; search clients by name/company

## PDF Export

PDF generation requires WeasyPrint and its system dependencies. If WeasyPrint is not installed or unavailable, the app serves a print-optimized HTML page instead.

Install WeasyPrint system dependencies (Debian/Ubuntu):

```bash
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

## Project Structure

```
invoicely/
├── app.py              # Flask application entry point
├── database.py         # SQLite schema and CRUD operations
├── pdf_generator.py    # HTML-to-PDF rendering
├── requirements.txt    # Python dependencies
├── templates/          # Jinja2 HTML templates
├── static/app.js       # Frontend interactivity (line items, calculations)
└── invoicely.db        # SQLite database (auto-created on first run)
```

## Configuration

- **Port:** 5000 (default)
- **Database:** `invoicely.db` in project root
- **No external API keys required**
