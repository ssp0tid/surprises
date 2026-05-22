import sqlite3
import secrets
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pollcraft.db')


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.isolation_level = None
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            admin_token TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            poll_type TEXT NOT NULL DEFAULT 'single',
            created_at TEXT DEFAULT (datetime('now')),
            closed_at TEXT DEFAULT NULL,
            allow_comments INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_id INTEGER NOT NULL,
            voter_ip TEXT NOT NULL,
            voted_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE,
            FOREIGN KEY (option_id) REFERENCES options(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            author TEXT DEFAULT 'Anonymous',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
        );
    """)
    conn.close()


def generate_slug(conn):
    for _ in range(10):
        slug = secrets.token_urlsafe(6)[:8]
        existing = conn.execute("SELECT 1 FROM polls WHERE slug = ?", (slug,)).fetchone()
        if not existing:
            return slug
    raise RuntimeError("Failed to generate unique slug after 10 attempts")


def generate_admin_token():
    return secrets.token_urlsafe(12)[:16]


def create_poll(title, description, options, poll_type, allow_comments):
    admin_token = generate_admin_token()
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        slug = generate_slug(conn)
        cursor = conn.execute(
            "INSERT INTO polls (slug, admin_token, title, description, poll_type, allow_comments) VALUES (?, ?, ?, ?, ?, ?)",
            (slug, admin_token, title, description, poll_type, 1 if allow_comments else 0)
        )
        poll_id = cursor.lastrowid
        for i, option_text in enumerate(options):
            conn.execute(
                "INSERT INTO options (poll_id, text, position) VALUES (?, ?, ?)",
                (poll_id, option_text, i)
            )
        conn.commit()
        return slug, admin_token
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_poll(slug):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM polls WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def get_options(poll_id):
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT o.id, o.text, o.position, COUNT(v.id) as votes
            FROM options o
            LEFT JOIN votes v ON v.option_id = o.id
            WHERE o.poll_id = ?
            GROUP BY o.id
            ORDER BY o.position
        """, (poll_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def cast_vote(poll_id, option_ids, voter_ip):
    conn = get_db()
    try:
        # Use BEGIN IMMEDIATE to acquire a write lock upfront, preventing
        # race conditions where two requests pass the duplicate check simultaneously.
        conn.execute("BEGIN IMMEDIATE")

        existing = conn.execute(
            "SELECT id FROM votes WHERE poll_id = ? AND voter_ip = ?",
            (poll_id, voter_ip)
        ).fetchone()
        if existing:
            conn.rollback()
            return False

        valid_options = conn.execute(
            "SELECT id FROM options WHERE poll_id = ?", (poll_id,)
        ).fetchall()
        valid_ids = {r['id'] for r in valid_options}

        for option_id in option_ids:
            if option_id not in valid_ids:
                conn.rollback()
                return False

        for option_id in option_ids:
            conn.execute(
                "INSERT INTO votes (poll_id, option_id, voter_ip) VALUES (?, ?, ?)",
                (poll_id, option_id, voter_ip)
            )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def close_poll(slug, admin_token):
    conn = get_db()
    try:
        conn.execute("BEGIN")
        row = conn.execute(
            "SELECT id, admin_token FROM polls WHERE slug = ?", (slug,)
        ).fetchone()
        if row is None or row['admin_token'] != admin_token:
            conn.rollback()
            return False
        conn.execute(
            "UPDATE polls SET closed_at = datetime('now') WHERE slug = ?", (slug,)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_poll(slug, admin_token):
    conn = get_db()
    try:
        conn.execute("BEGIN")
        row = conn.execute(
            "SELECT id, admin_token FROM polls WHERE slug = ?", (slug,)
        ).fetchone()
        if row is None or row['admin_token'] != admin_token:
            conn.rollback()
            return False
        conn.execute("DELETE FROM polls WHERE slug = ?", (slug,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_comment(poll_id, text, author):
    conn = get_db()
    try:
        conn.execute("BEGIN")
        cursor = conn.execute(
            "INSERT INTO comments (poll_id, text, author) VALUES (?, ?, ?)",
            (poll_id, text, author or 'Anonymous')
        )
        conn.commit()
        comment = conn.execute(
            "SELECT * FROM comments WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return dict(comment)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_comments(poll_id):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM comments WHERE poll_id = ? ORDER BY created_at DESC",
            (poll_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
