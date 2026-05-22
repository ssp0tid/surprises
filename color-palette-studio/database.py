"""SQLite palette storage."""

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "palettes.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS palettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                colors TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_palette(name: str, colors: list[str]) -> int:
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO palettes (name, colors) VALUES (?, ?)",
            (name, json.dumps(colors)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def list_palettes() -> list[dict]:
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, colors, created_at FROM palettes ORDER BY created_at DESC"
        ).fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "colors": json.loads(row["colors"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def delete_palette(palette_id: int) -> bool:
    conn = _get_connection()
    try:
        cursor = conn.execute("DELETE FROM palettes WHERE id = ?", (palette_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
