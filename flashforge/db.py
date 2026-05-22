"""Database layer for FlashForge - SQLite connection and schema management."""

import os
import sqlite3
from pathlib import Path

DB_DIR = Path.home() / ".flashforge"
DB_PATH = DB_DIR / "flashforge.db"

_connection = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    box INTEGER DEFAULT 1,
    next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    response TEXT NOT NULL,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_box INTEGER NOT NULL,
    new_box INTEGER NOT NULL
);
"""


def init_db() -> sqlite3.Connection:
    """Initialize the database, creating directory and tables if needed."""
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Cannot create database directory {DB_DIR}: {e}") from e

    try:
        conn = sqlite3.connect(str(DB_PATH))
    except sqlite3.Error as e:
        raise RuntimeError(f"Cannot connect to database {DB_PATH}: {e}") from e

    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def get_db() -> sqlite3.Connection:
    """Get or create a singleton database connection."""
    global _connection
    if _connection is None:
        _connection = init_db()
    return _connection


def close_db() -> None:
    """Close the database connection."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
