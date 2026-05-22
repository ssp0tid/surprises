"""SQLite database layer for PixelForge project persistence."""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "pixelforge.db"


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Get a database connection with row factory."""
    path = db_path or str(DB_PATH)
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    except sqlite3.OperationalError as e:
        raise RuntimeError(f"Cannot open database at {path}: {e}") from e


def init_db(db_path: str | None = None) -> None:
    """Create projects table if not exists."""
    conn = get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def create_project(name: str, width: int, height: int) -> int:
    """Create a new project with empty initial data. Returns project ID."""
    initial_data = json.dumps({
        "layers": [{
            "id": 0,
            "name": "Layer 1",
            "opacity": 100,
            "visible": True,
            "pixels": None
        }],
        "frames": [{"id": 0, "duration": 100, "layerData": None}],
        "palette": [],
        "activeFrame": 0,
        "activeLayer": 0
    })
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO projects (name, width, height, data) VALUES (?, ?, ?, ?)",
            (name, width, height, initial_data)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_project(project_id: int) -> dict | None:
    """Get a project by ID. Returns dict or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, width, height, data, created_at, updated_at FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "width": row["width"],
            "height": row["height"],
            "data": json.loads(row["data"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    finally:
        conn.close()


def list_projects() -> list[dict]:
    """List all projects (metadata only, no pixel data)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, name, width, height, created_at, updated_at FROM projects ORDER BY updated_at DESC"
        ).fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "width": row["width"],
                "height": row["height"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            for row in rows
        ]
    finally:
        conn.close()


def update_project(project_id: int, data: str, name: str | None = None) -> bool:
    """Update project data (and optionally name). Returns True if project existed."""
    conn = get_connection()
    try:
        if name is not None:
            cursor = conn.execute(
                "UPDATE projects SET data = ?, name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (data, name, project_id)
            )
        else:
            cursor = conn.execute(
                "UPDATE projects SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (data, project_id)
            )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_project(project_id: int) -> bool:
    """Delete a project. Returns True if project existed."""
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
