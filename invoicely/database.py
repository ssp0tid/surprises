import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invoicely.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            company TEXT,
            address TEXT,
            phone TEXT,
            tax_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS invoices (
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

        CREATE TABLE IF NOT EXISTS line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()


# --- Client CRUD ---

def create_client(data):
    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO clients (name, email, company, address, phone, tax_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data.get('name'), data.get('email'), data.get('company'),
             data.get('address'), data.get('phone'), data.get('tax_id'))
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_clients(search=None):
    conn = get_db()
    try:
        if search:
            rows = conn.execute(
                """SELECT * FROM clients
                   WHERE name LIKE ? OR company LIKE ?
                   ORDER BY name""",
                (f'%{search}%', f'%{search}%')
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_client(client_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_client(client_id, data):
    conn = get_db()
    try:
        conn.execute(
            """UPDATE clients SET name=?, email=?, company=?, address=?, phone=?, tax_id=?
               WHERE id=?""",
            (data.get('name'), data.get('email'), data.get('company'),
             data.get('address'), data.get('phone'), data.get('tax_id'), client_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_client(client_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
    finally:
        conn.close()


def client_has_invoices(client_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as count FROM invoices WHERE client_id = ?", (client_id,)
        ).fetchone()
        return row['count'] > 0
    finally:
        conn.close()


# --- Invoice CRUD ---

def _generate_invoice_number(conn):
    today = datetime.now().strftime('%Y%m%d')
    prefix = f'INV-{today}-'
    row = conn.execute(
        "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ? ORDER BY invoice_number DESC LIMIT 1",
        (f'{prefix}%',)
    ).fetchone()
    if row:
        last_seq = int(row['invoice_number'].split('-')[-1])
        seq = last_seq + 1
    else:
        seq = 1
    return f'{prefix}{seq:03d}'


def create_invoice(data, items):
    conn = get_db()
    try:
        invoice_number = _generate_invoice_number(conn)
        cursor = conn.execute(
            """INSERT INTO invoices (invoice_number, client_id, issue_date, due_date, status, notes, tax_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (invoice_number, data.get('client_id'), data.get('issue_date'),
             data.get('due_date'), data.get('status', 'draft'),
             data.get('notes'), data.get('tax_rate', 0.0))
        )
        invoice_id = cursor.lastrowid
        for item in items:
            conn.execute(
                """INSERT INTO line_items (invoice_id, description, quantity, unit_price)
                   VALUES (?, ?, ?, ?)""",
                (invoice_id, item.get('description'), item.get('quantity', 1),
                 item.get('unit_price', 0))
            )
        conn.commit()
        return invoice_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_invoices(filters=None):
    conn = get_db()
    try:
        query = """
            SELECT i.*, c.name as client_name, c.company as client_company
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            WHERE 1=1
        """
        params = []
        if filters:
            if filters.get('status'):
                query += " AND i.status = ?"
                params.append(filters['status'])
            if filters.get('client_id'):
                query += " AND i.client_id = ?"
                params.append(filters['client_id'])
            if filters.get('date_from'):
                query += " AND i.issue_date >= ?"
                params.append(filters['date_from'])
            if filters.get('date_to'):
                query += " AND i.issue_date <= ?"
                params.append(filters['date_to'])
        query += " ORDER BY i.created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_invoice(invoice_id):
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT i.*, c.name as client_name, c.company as client_company,
                      c.email as client_email, c.address as client_address,
                      c.phone as client_phone, c.tax_id as client_tax_id
               FROM invoices i
               JOIN clients c ON i.client_id = c.id
               WHERE i.id = ?""",
            (invoice_id,)
        ).fetchone()
        if not row:
            return None
        invoice = dict(row)
        items = conn.execute(
            "SELECT * FROM line_items WHERE invoice_id = ? ORDER BY id",
            (invoice_id,)
        ).fetchall()
        invoice['items'] = [dict(item) for item in items]
        # Calculate totals
        subtotal = sum(item['quantity'] * item['unit_price'] for item in invoice['items'])
        tax = subtotal * (invoice['tax_rate'] / 100)
        invoice['subtotal'] = round(subtotal, 2)
        invoice['tax_amount'] = round(tax, 2)
        invoice['total'] = round(subtotal + tax, 2)
        return invoice
    finally:
        conn.close()


def update_invoice(invoice_id, data, items):
    conn = get_db()
    try:
        conn.execute(
            """UPDATE invoices SET client_id=?, issue_date=?, due_date=?, status=?, notes=?, tax_rate=?
               WHERE id=?""",
            (data.get('client_id'), data.get('issue_date'), data.get('due_date'),
             data.get('status', 'draft'), data.get('notes'),
             data.get('tax_rate', 0.0), invoice_id)
        )
        conn.execute("DELETE FROM line_items WHERE invoice_id = ?", (invoice_id,))
        for item in items:
            conn.execute(
                """INSERT INTO line_items (invoice_id, description, quantity, unit_price)
                   VALUES (?, ?, ?, ?)""",
                (invoice_id, item.get('description'), item.get('quantity', 1),
                 item.get('unit_price', 0))
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_invoice_status(invoice_id, status):
    conn = get_db()
    try:
        conn.execute("UPDATE invoices SET status = ? WHERE id = ?", (status, invoice_id))
        conn.commit()
    finally:
        conn.close()


def delete_invoice(invoice_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        conn.commit()
    finally:
        conn.close()


# --- Dashboard Stats ---

def get_dashboard_stats():
    conn = get_db()
    try:
        stats = {}
        # Counts by status
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM invoices GROUP BY status"
        ).fetchall()
        stats['status_counts'] = {row['status']: row['count'] for row in rows}

        # Total revenue (paid)
        row = conn.execute("""
            SELECT COALESCE(SUM(li.quantity * li.unit_price * (1 + i.tax_rate/100)), 0) as total
            FROM invoices i
            JOIN line_items li ON li.invoice_id = i.id
            WHERE i.status = 'paid'
        """).fetchone()
        stats['total_revenue'] = round(row['total'], 2)

        # Outstanding (sent + overdue)
        row = conn.execute("""
            SELECT COALESCE(SUM(li.quantity * li.unit_price * (1 + i.tax_rate/100)), 0) as total
            FROM invoices i
            JOIN line_items li ON li.invoice_id = i.id
            WHERE i.status IN ('sent', 'overdue')
        """).fetchone()
        stats['outstanding'] = round(row['total'], 2)

        # Recent invoices
        rows = conn.execute("""
            SELECT i.*, c.name as client_name
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            ORDER BY i.created_at DESC LIMIT 5
        """).fetchall()
        stats['recent_invoices'] = [dict(r) for r in rows]

        return stats
    finally:
        conn.close()
