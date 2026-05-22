import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reqbench.db')
MAX_HISTORY = 100
MAX_RESPONSE_BODY = 1_000_000  # 1MB


def get_db():
    """Get a database connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT NOT NULL,
                request_name TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers_json TEXT DEFAULT '[]',
                body TEXT DEFAULT '',
                body_type TEXT DEFAULT 'json',
                params_json TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                headers_json TEXT DEFAULT '[]',
                body TEXT DEFAULT '',
                body_type TEXT DEFAULT 'json',
                params_json TEXT DEFAULT '[]',
                status_code INTEGER,
                response_headers_json TEXT DEFAULT '{}',
                response_body TEXT DEFAULT '',
                duration_ms REAL,
                response_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS environments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                variables_json TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    finally:
        conn.close()


def prune_history(conn):
    """Keep only the last MAX_HISTORY entries."""
    conn.execute("""
        DELETE FROM history WHERE id NOT IN (
            SELECT id FROM history ORDER BY created_at DESC LIMIT ?
        )
    """, (MAX_HISTORY,))


def truncate_response_body(body):
    """Truncate response body to MAX_RESPONSE_BODY bytes."""
    if body and len(body) > MAX_RESPONSE_BODY:
        return body[:MAX_RESPONSE_BODY] + "\n... [truncated]"
    return body


# --- Collections ---

def get_collections():
    """Get all collections grouped by collection_name."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM collections ORDER BY collection_name, created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_to_collection(data):
    """Save a request to a collection."""
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO collections
               (collection_name, request_name, method, url, headers_json, body, body_type, params_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data['collection_name'],
                data['request_name'],
                data['method'],
                data['url'],
                json.dumps(data.get('headers', [])),
                data.get('body', ''),
                data.get('body_type', 'json'),
                json.dumps(data.get('params', [])),
            )
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()


def delete_collection_item(item_id):
    """Delete a saved request from collections."""
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM collections WHERE id = ?", (item_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# --- History ---

def get_history():
    """Get last MAX_HISTORY history entries."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM history ORDER BY created_at DESC LIMIT ?",
            (MAX_HISTORY,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def add_history(request_data, response_data):
    """Add a history entry and prune old entries."""
    conn = get_db()
    try:
        response_body = truncate_response_body(response_data.get('body', ''))
        conn.execute(
            """INSERT INTO history
               (method, url, headers_json, body, body_type, params_json,
                status_code, response_headers_json, response_body, duration_ms, response_size)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request_data['method'],
                request_data['url'],
                json.dumps(request_data.get('headers', [])),
                request_data.get('body', ''),
                request_data.get('body_type', 'json'),
                json.dumps(request_data.get('params', [])),
                response_data.get('status_code'),
                json.dumps(response_data.get('headers', {})),
                response_body,
                response_data.get('duration_ms'),
                response_data.get('size_bytes'),
            )
        )
        prune_history(conn)
        conn.commit()
    finally:
        conn.close()


def clear_history():
    """Delete all history entries."""
    conn = get_db()
    try:
        conn.execute("DELETE FROM history")
        conn.commit()
    finally:
        conn.close()


# --- Environments ---

def get_environments():
    """Get all environments."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM environments ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_environment(data):
    """Create or update an environment."""
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO environments (name, variables_json)
               VALUES (?, ?)
               ON CONFLICT(name) DO UPDATE SET variables_json = excluded.variables_json""",
            (data['name'], json.dumps(data.get('variables', {})))
        )
        conn.commit()
        return True
    finally:
        conn.close()


def delete_environment(env_id):
    """Delete an environment."""
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM environments WHERE id = ?", (env_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
