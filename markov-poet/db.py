"""SQLite persistence layer for Markov Poet."""

import json
import os
import sqlite3



DEFAULT_DB_DIR = os.path.expanduser("~/.markov-poet")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "markov.db")


def init_db(path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create tables if they don't exist and return a connection."""
    db_dir = os.path.dirname(path)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create database directory '{db_dir}': {e}") from e

    try:
        conn = sqlite3.connect(path)
    except sqlite3.OperationalError as e:
        raise OSError(f"Cannot open database '{path}': {e}") from e

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS texts (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            word_count INTEGER NOT NULL,
            added_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chains (
            id INTEGER PRIMARY KEY,
            text_id INTEGER NOT NULL,
            order_n INTEGER NOT NULL,
            state TEXT NOT NULL,
            next_word TEXT NOT NULL,
            count INTEGER NOT NULL,
            FOREIGN KEY (text_id) REFERENCES texts(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_chains_state ON chains(order_n, state);
        CREATE INDEX IF NOT EXISTS idx_chains_text ON chains(text_id);
    """)
    conn.commit()
    return conn


def save_chain(conn: sqlite3.Connection, text_id: int, order: int, chain: dict) -> None:
    """Bulk insert chain data for a given text and order.

    Args:
        conn: Database connection.
        text_id: ID of the source text.
        order: Markov chain order.
        chain: Dict of {state_tuple_as_json: {next_word: count}}.
    """
    conn.execute(
        "DELETE FROM chains WHERE text_id = ? AND order_n = ?",
        (text_id, order),
    )

    rows = []
    for state, transitions in chain.items():
        state_json = json.dumps(state) if isinstance(state, (list, tuple)) else state
        for next_word, count in transitions.items():
            rows.append((text_id, order, state_json, next_word, count))

    conn.executemany(
        "INSERT INTO chains (text_id, order_n, state, next_word, count) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def load_chain(conn: sqlite3.Connection, text_id: int | None, order: int) -> dict:
    """Load chain from database.

    Args:
        conn: Database connection.
        text_id: Specific text ID, or None to load chains from all texts.
        order: Markov chain order.

    Returns:
        Dict of {state_tuple: {next_word: count}}.
    """
    if text_id is not None:
        cursor = conn.execute(
            "SELECT state, next_word, count FROM chains WHERE text_id = ? AND order_n = ?",
            (text_id, order),
        )
    else:
        cursor = conn.execute(
            "SELECT state, next_word, count FROM chains WHERE order_n = ?",
            (order,),
        )

    chain: dict = {}
    for row in cursor:
        try:
            state = tuple(json.loads(row["state"]))
        except (json.JSONDecodeError, TypeError):
            continue  # skip corrupted entries

        next_word = row["next_word"]
        count = row["count"]

        if state not in chain:
            chain[state] = {}
        chain[state][next_word] = chain[state].get(next_word, 0) + count

    return chain
