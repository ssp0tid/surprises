"""Corpus management - add, list, and remove texts."""

import sqlite3
from datetime import datetime, timezone

from db import init_db
from tokenizer import tokenize
from chain import build_chain


def add_text(db_path: str, name: str, filepath: str) -> int:
    """Read a file, tokenize it, build chains (orders 1-3), and store everything."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")
    except PermissionError:
        raise PermissionError(f"Cannot read file: {filepath}")

    if not content.strip():
        raise ValueError(f"File is empty: {filepath}")

    tokens = tokenize(content)
    word_count = len(tokens)
    now = datetime.now(timezone.utc).isoformat()

    conn = init_db(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO texts (name, content, word_count, added_at) VALUES (?, ?, ?, ?)",
            (name, content, word_count, now),
        )
        text_id = cursor.lastrowid

        for order in range(1, 6):
            chain = build_chain(tokens, order)
            if chain:
                from db import save_chain
                save_chain(conn, text_id, order, chain)

        conn.commit()
        return text_id
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError(f"A text named '{name}' already exists")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def list_texts(db_path: str) -> list[dict]:
    """Return [{id, name, word_count, added_at}] for all texts."""
    conn = init_db(db_path)
    try:
        rows = conn.execute(
            "SELECT id, name, word_count, added_at FROM texts ORDER BY added_at"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def remove_text(db_path: str, name: str) -> bool:
    """Remove a text and its associated chains. Returns True if found and removed."""
    conn = init_db(db_path)
    try:
        cursor = conn.execute("DELETE FROM texts WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
