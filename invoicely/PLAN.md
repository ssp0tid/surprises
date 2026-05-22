# Invoicely — Web-Based Invoice Generator

One-line: A self-hosted web app for creating, managing, and exporting professional PDF invoices with client management and payment tracking.

## Tech Stack

- **Backend:** Python 3 Flask
- **Database:** SQLite (via sqlite3 stdlib)
- **PDF Generation:** WeasyPrint (HTML-to-PDF)
- **Frontend:** Vanilla JS + TailwindCSS CDN + HTML templates (Jinja2)
- **No external API keys required**

## File Structure

```
invoicely/
├── PLAN.md
├── README.md
├── app.py                  # Main Flask application (entry point)
├── database.py             # SQLite schema + CRUD helpers
├── pdf_generator.py        # HTML-to-PDF invoice rendering
├── templates/
│   ├── base.html           # Layout with nav, TailwindCSS CDN
│   ├── dashboard.html      # Overview: recent invoices, totals, stats
│   ├── invoices.html       # Invoice list with filters (status, date, client)
│   ├── invoice_form.html   # Create/edit invoice form
│   ├── invoice_view.html   # Single invoice detail view
│   ├── invoice_pdf.html    # PDF-optimized template (no nav, print styles)
│   ├── clients.html        # Client list
│   └── client_form.html    # Create/edit client form
├── static/
│   └── app.js              # Frontend interactivity (line item add/remove, calculations)
└── requirements.txt        # flask, weasyprint
```

## Features

### 1. Client Management
- **CRUD clients** — name, email, address, phone, company, tax_id
- `database.py`: `create_client(data: dict) -> int`, `get_clients() -> list`, `get_client(id: int) -> dict`, `update_client(id: int, data: dict)`, `delete_client(id: int)`
- Clients page shows list with search filter

### 2. Invoice Creation & Editing
- **Invoice fields:** invoice_number (auto-generated INV-YYYYMMDD-NNN), client_id, issue_date, due_date, status (draft/sent/paid/overdue), notes, tax_rate (%)
- **Line items:** description, quantity, unit_price — stored in `line_items` table with invoice_id FK
- `database.py`: `create_invoice(data: dict, items: list) -> int`, `get_invoices(filters: dict) -> list`, `get_invoice(id: int) -> dict`, `update_invoice(id: int, data: dict, items: list)`, `delete_invoice(id: int)`
- Auto-calculate subtotal, tax, total on frontend (app.js) and verify on backend

### 3. Invoice Status Tracking
- Status badges: Draft (gray), Sent (blue), Paid (green), Overdue (red)
- Mark as sent/paid buttons on invoice view
- Dashboard shows counts per status

### 4. PDF Export
- `pdf_generator.py`: `generate_pdf(invoice: dict) -> bytes`
- Uses `invoice_pdf.html` template — clean layout with company logo placeholder, client address block, itemized table, totals, payment terms
- Route: `GET /invoices/<id>/pdf` — returns PDF as attachment
- Fallback: if WeasyPrint unavailable, serve the HTML template as printable page

### 5. Dashboard
- Total revenue (sum of paid invoices)
- Outstanding amount (sum of sent/overdue)
- Invoice count by status
- Recent 5 invoices quick list

### 6. Filtering & Search
- Invoice list: filter by status, client, date range
- Client list: search by name/company

## Database Schema (SQLite)

```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    company TEXT,
    address TEXT,
    phone TEXT,
    tax_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE NOT NULL,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    notes TEXT,
    tax_rate REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity REAL NOT NULL DEFAULT 1,
    unit_price REAL NOT NULL DEFAULT 0
);
```

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | / | Dashboard |
| GET | /clients | Client list |
| GET/POST | /clients/new | Create client |
| GET/POST | /clients/<id>/edit | Edit client |
| POST | /clients/<id>/delete | Delete client |
| GET | /invoices | Invoice list (with query params for filters) |
| GET/POST | /invoices/new | Create invoice |
| GET | /invoices/<id> | View invoice |
| GET/POST | /invoices/<id>/edit | Edit invoice |
| POST | /invoices/<id>/delete | Delete invoice |
| POST | /invoices/<id>/status | Update status (JSON: {status: "paid"}) |
| GET | /invoices/<id>/pdf | Download PDF |

## Constraints

- Single `app.py` entry point — run with `python3 app.py` (port 5000)
- No external API keys
- SQLite file: `invoicely.db` in project root
- WeasyPrint is optional — graceful fallback to HTML print view
- All monetary values stored as REAL (float), displayed with 2 decimal places
- Invoice numbers auto-increment per day: INV-20260522-001, INV-20260522-002, etc.
- TailwindCSS via CDN (no build step)
- Mobile-responsive layout
