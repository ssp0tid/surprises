#!/usr/bin/env python3
"""
KanboardX - Self-hosted Kanban Board Application
A zero-external-dependency task management system with drag-and-drop,
markdown support, and a gorgeous dark theme UI.
"""

import os
import sys
import json
import uuid
import csv
import re
import fcntl
import time
import argparse
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any
from functools import wraps

from flask import Flask, request, jsonify, Response, send_file
from werkzeug.serving import WSGIRequestHandler

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_PORT = 5000
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
EXPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# ============================================================================
# Helper Functions
# ============================================================================


def generate_uuid() -> str:
    """Generate a unique UUID."""
    return str(uuid.uuid4())


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_date(date_str: str) -> Optional[date]:
    """Parse date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def format_date(d: date) -> str:
    """Format date object to string."""
    if d is None:
        return ""
    return d.isoformat()


# ============================================================================
# JSON File Storage with Locking
# ============================================================================


class JSONStore:
    """Simple JSON file storage with file locking."""

    LOCK_TIMEOUT = 30

    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        self._cleanup_stale_locks()
        self._ensure_files()

    def _cleanup_stale_locks(self):
        for fname in os.listdir(self.data_dir):
            if fname.endswith(".lock"):
                lock_path = os.path.join(self.data_dir, fname)
                try:
                    if os.path.exists(lock_path):
                        mtime = os.path.getmtime(lock_path)
                        if time.time() - mtime > self.LOCK_TIMEOUT:
                            os.remove(lock_path)
                except OSError:
                    pass

    def _ensure_files(self):
        files = ["boards.json", "cards.json", "labels.json", "config.json"]
        for fname in files:
            fpath = os.path.join(self.data_dir, fname)
            if not os.path.exists(fpath):
                with open(fpath, "w") as f:
                    if fname == "boards.json":
                        json.dump([], f)
                    elif fname == "cards.json":
                        json.dump([], f)
                    elif fname == "labels.json":
                        json.dump([], f)
                    elif fname == "config.json":
                        json.dump({"version": "1.0"}, f)

    def _read_json(self, filename: str) -> Any:
        """Read JSON from file with locking."""
        fpath = os.path.join(self.data_dir, filename)
        lock_path = fpath + ".lock"
        backup_path = fpath + ".backup"
        default = [] if "cards" in filename or "boards" in filename else {}

        for attempt in range(3):
            try:
                lock_file = open(lock_path, "w")
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                break
            except IOError:
                if attempt == 2:
                    raise
                time.sleep(0.1 * (2**attempt))

        try:
            with open(fpath, "r") as f:
                content = f.read()
                if not content.strip():
                    return default
                return json.loads(content)
        except json.JSONDecodeError:
            if os.path.exists(backup_path):
                try:
                    with open(backup_path, "r") as f:
                        content = f.read()
                        if content.strip():
                            data = json.loads(content)
                            with open(fpath, "w") as dst:
                                dst.write(content)
                            return data
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
            return default
        except FileNotFoundError:
            return default
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    def _write_json(self, filename: str, data: Any):
        """Write JSON to file with locking."""
        fpath = os.path.join(self.data_dir, filename)
        lock_path = fpath + ".lock"

        # Acquire lock
        for attempt in range(3):
            try:
                lock_file = open(lock_path, "w")
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                break
            except IOError:
                if attempt == 2:
                    raise
                time.sleep(0.1 * (2**attempt))

        try:
            # Backup before writing
            if os.path.exists(fpath):
                backup_path = fpath + ".backup"
                with open(fpath, "r") as src:
                    with open(backup_path, "w") as dst:
                        dst.write(src.read())

            with open(fpath, "w") as f:
                json.dump(data, f, indent=2)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    # Boards
    def get_boards(self) -> List[Dict]:
        """Get all boards."""
        return self._read_json("boards.json")

    def get_board(self, board_id: str) -> Optional[Dict]:
        """Get a single board by ID."""
        boards = self.get_boards()
        for board in boards:
            if board.get("id") == board_id:
                return board
        return None

    def create_board(
        self, name: str, description: str = "", columns: List[Dict] = None
    ) -> Dict:
        """Create a new board."""
        board_id = generate_uuid()
        now = get_timestamp()

        if not columns:
            columns = [
                {"id": generate_uuid(), "name": "To Do", "order": 0},
                {"id": generate_uuid(), "name": "In Progress", "order": 1},
                {"id": generate_uuid(), "name": "Done", "order": 2},
            ]

        board = {
            "id": board_id,
            "name": name,
            "description": description,
            "columns": columns,
            "created_at": now,
            "updated_at": now,
        }

        boards = self.get_boards()
        boards.append(board)
        self._write_json("boards.json", boards)
        return board

    def update_board(self, board_id: str, updates: Dict) -> Optional[Dict]:
        """Update a board."""
        boards = self.get_boards()
        for i, board in enumerate(boards):
            if board.get("id") == board_id:
                boards[i].update(updates)
                boards[i]["updated_at"] = get_timestamp()
                self._write_json("boards.json", boards)
                return boards[i]
        return None

    def delete_board(self, board_id: str) -> bool:
        """Delete a board and its cards."""
        boards = self.get_boards()
        boards = [b for b in boards if b.get("id") != board_id]
        self._write_json("boards.json", boards)

        # Delete all cards in this board
        cards = self.get_cards()
        cards = [c for c in cards if c.get("board_id") != board_id]
        self._write_json("cards.json", cards)
        return True

    # Cards
    def get_cards(self, board_id: str = None) -> List[Dict]:
        """Get all cards, optionally filtered by board."""
        cards = self._read_json("cards.json")
        if board_id:
            cards = [c for c in cards if c.get("board_id") == board_id]
        return cards

    def get_card(self, card_id: str) -> Optional[Dict]:
        """Get a single card by ID."""
        cards = self.get_cards()
        for card in cards:
            if card.get("id") == card_id:
                return card
        return None

    def create_card(
        self,
        board_id: str,
        column_id: str,
        title: str,
        description: str = "",
        priority: str = "low",
        label_ids: List[str] = None,
        due_date: str = None,
    ) -> Dict:
        """Create a new card."""
        card_id = generate_uuid()
        now = get_timestamp()

        # Get position (next in column)
        cards = self.get_cards()
        column_cards = [c for c in cards if c.get("column_id") == column_id]
        position = len(column_cards)

        card = {
            "id": card_id,
            "board_id": board_id,
            "column_id": column_id,
            "title": title,
            "description": description,
            "position": position,
            "priority": priority,
            "labels": label_ids or [],
            "due_date": due_date,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }

        cards.append(card)
        self._write_json("cards.json", cards)
        return card

    def update_card(self, card_id: str, updates: Dict) -> Optional[Dict]:
        """Update a card."""
        cards = self.get_cards()
        for i, card in enumerate(cards):
            if card.get("id") == card_id:
                cards[i].update(updates)
                cards[i]["updated_at"] = get_timestamp()

                # Set completed_at if moved to Done column
                if "column_id" in updates:
                    board = self.get_board(cards[i].get("board_id"))
                    if board:
                        done_col = next(
                            (
                                c
                                for c in board.get("columns", [])
                                if c.get("name", "").lower() == "done"
                            ),
                            None,
                        )
                        if done_col and updates.get("column_id") == done_col.get("id"):
                            cards[i]["completed_at"] = get_timestamp()

                self._write_json("cards.json", cards)
                return cards[i]
        return None

    def delete_card(self, card_id: str) -> bool:
        """Delete a card."""
        cards = self.get_cards()
        cards = [c for c in cards if c.get("id") != card_id]
        self._write_json("cards.json", cards)
        return True

    def reorder_cards(self, column_id: str, card_ids: List[str]):
        """Reorder cards in a column."""
        cards = self.get_cards()
        updated_cards = []
        for card in cards:
            if card.get("column_id") == column_id:
                if card.get("id") in card_ids:
                    card["position"] = card_ids.index(card["id"])
            updated_cards.append(card)
        self._write_json("cards.json", updated_cards)

    # Labels
    def get_labels(self) -> List[Dict]:
        """Get all labels."""
        return self._read_json("labels.json")

    def create_label(self, name: str, color: str = "#e94560") -> Dict:
        """Create a new label."""
        label_id = generate_uuid()
        label = {"id": label_id, "name": name, "color": color}

        labels = self.get_labels()
        labels.append(label)
        self._write_json("labels.json", labels)
        return label

    def delete_label(self, label_id: str) -> bool:
        """Delete a label."""
        labels = self.get_labels()
        labels = [l for l in labels if l.get("id") != label_id]
        self._write_json("labels.json", labels)

        # Remove label from all cards
        cards = self.get_cards()
        for card in cards:
            if label_id in card.get("labels", []):
                card["labels"].remove(label_id)
        self._write_json("cards.json", cards)
        return True

    # Stats
    def get_stats(self, board_id: str) -> Dict:
        """Get board statistics."""
        cards = self.get_cards(board_id)
        board = self.get_board(board_id)

        if not board:
            return {}

        columns = {c["id"]: c for c in board.get("columns", [])}
        column_names = {c["id"]: c["name"] for c in board.get("columns", [])}

        stats = {
            "total_cards": len(cards),
            "by_column": {},
            "by_priority": {"low": 0, "medium": 0, "high": 0, "urgent": 0},
            "overdue": 0,
            "completed": 0,
            "completion_rate": 0,
        }

        today = date.today()

        for col_id, col_name in column_names.items():
            col_cards = [c for c in cards if c.get("column_id") == col_id]
            stats["by_column"][col_name] = len(col_cards)

        for card in cards:
            p = card.get("priority", "low")
            if p in stats["by_priority"]:
                stats["by_priority"][p] += 1

            due = card.get("due_date")
            if due:
                try:
                    due_date = parse_date(due)
                    if due_date and due_date < today and not card.get("completed_at"):
                        stats["overdue"] += 1
                except:
                    pass

        if cards:
            done_col = next(
                (
                    c
                    for c in board.get("columns", [])
                    if c.get("name", "").lower() == "done"
                ),
                None,
            )
            if done_col:
                done_cards = [c for c in cards if c.get("column_id") == done_col["id"]]
                stats["by_column"]["Done"] = len(done_cards)
                stats["completed"] = len(done_cards)
                stats["completion_rate"] = round(
                    (len(done_cards) / len(cards)) * 100, 1
                )

        return stats

    # CSV Export
    def export_csv(self, board_id: str) -> str:
        """Export board to CSV file."""
        board = self.get_board(board_id)
        cards = self.get_cards(board_id)
        labels = {l["id"]: l for l in self.get_labels()}

        if not board:
            return ""

        columns = {c["id"]: c["name"] for c in board.get("columns", [])}

        # Create CSV
        csv_path = os.path.join(EXPORTS_DIR, f"board_{board_id}_{int(time.time())}.csv")

        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            # Header
            writer.writerow(
                [
                    "Title",
                    "Description",
                    "Column",
                    "Priority",
                    "Labels",
                    "Due Date",
                    "Created",
                    "Completed",
                ]
            )

            # Data
            for card in cards:
                card_labels = [
                    labels.get(l, {}).get("name", "")
                    for l in card.get("labels", [])
                    if l in labels
                ]
                description = card.get("description", "")
                description = (
                    description.replace("\r\n", " ")
                    .replace("\n", " ")
                    .replace("\r", " ")
                )
                writer.writerow(
                    [
                        card.get("title", ""),
                        description,
                        columns.get(card.get("column_id"), ""),
                        card.get("priority", ""),
                        ", ".join(card_labels),
                        card.get("due_date", ""),
                        card.get("created_at", ""),
                        card.get("completed_at", ""),
                    ]
                )

        return csv_path


# ============================================================================
# XSS Prevention
# ============================================================================


def escape_html(text: str) -> str:
    """Escape HTML entities to prevent XSS."""
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")
    return text


# ============================================================================
# Custom Markdown Parser (Regex-based, NO dependencies)
# ============================================================================


def parse_markdown(text: str) -> str:
    """
    Parse markdown to HTML using regex.
    Supports: headings, bold, italic, code, code blocks, links, lists.
    XSS-safe: escapes HTML first.
    """
    if not text:
        return ""

    # Escape HTML first for security
    text = escape_html(text)

    # Line-by-line processing
    lines = text.split("\n")
    result = []
    in_code_block = False
    code_buffer = []

    for line in lines:
        # Code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                # End code block
                code_content = "\n".join(code_buffer)
                result.append(f"<pre><code>{code_content}</code></pre>")
                code_buffer = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # Headings
        if line.strip().startswith("### "):
            result.append(f"<h4>{line[4:]}</h4>")
        elif line.strip().startswith("## "):
            result.append(f"<h3>{line[3:]}</h3>")
        elif line.strip().startswith("# "):
            result.append(f"<h2>{line[2:]}</h2>")
        # List items
        elif line.strip().startswith("- "):
            result.append(f"<li>{line[2:]}</li>")
        # Regular text
        else:
            processed = process_inline_markdown(line)
            if processed:
                result.append(f"<p>{processed}</p>")

    # Close any open code block
    if in_code_block:
        code_content = "\n".join(code_buffer)
        result.append(f"<pre><code>{code_content}</code></pre>")

    return "\n".join(result)


def process_inline_markdown(text: str) -> str:
    """Process inline markdown elements."""
    if not text:
        return text

    # Code (inline) - must be before bold/italic
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    # Italic
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)

    # Links [text](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )

    return text


# ============================================================================
# Flask Application
# ============================================================================

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# Add CSP header
@app.after_request
def add_csp(response):
    """Add Content Security Policy header."""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
    )
    return response


# Initialize store
store = JSONStore()


# ============================================================================
# API Routes
# ============================================================================


@app.route("/api/v1/boards", methods=["GET"])
def list_boards():
    """List all boards."""
    boards = store.get_boards()
    return jsonify(boards)


@app.route("/api/v1/board", methods=["POST"])
def create_board():
    """Create a new board."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify(
            {
                "error": "Validation error",
                "message": "Board name is required",
                "code": 400,
            }
        ), 400

    description = data.get("description", "")
    columns = data.get("columns")

    board = store.create_board(name, description, columns)
    return jsonify(board), 201


@app.route("/api/v1/board/<board_id>", methods=["GET"])
def get_board(board_id):
    """Get a single board with columns."""
    board = store.get_board(board_id)
    if not board:
        return jsonify(
            {"error": "Not found", "message": "Board not found", "code": 404}
        ), 404
    return jsonify(board)


@app.route("/api/v1/board/<board_id>", methods=["PUT"])
def update_board(board_id):
    """Update a board."""
    data = request.get_json() or {}
    board = store.update_board(board_id, data)
    if not board:
        return jsonify(
            {"error": "Not found", "message": "Board not found", "code": 404}
        ), 404
    return jsonify(board)


@app.route("/api/v1/board/<board_id>", methods=["DELETE"])
def delete_board(board_id):
    """Delete a board."""
    board = store.get_board(board_id)
    if not board:
        return jsonify(
            {"error": "Not found", "message": "Board not found", "code": 404}
        ), 404
    store.delete_board(board_id)
    return jsonify({"message": "Board deleted"})


@app.route("/api/v1/cards", methods=["GET"])
def list_cards():
    """List cards with optional filters."""
    board_id = request.args.get("board_id")
    column_id = request.args.get("column_id")
    priority = request.args.get("priority")
    label = request.args.get("label")
    due = request.args.get("due")
    q = request.args.get("q", "").lower()

    cards = store.get_cards(board_id)

    # Filter by column
    if column_id:
        cards = [c for c in cards if c.get("column_id") == column_id]

    # Filter by priority
    if priority:
        cards = [c for c in cards if c.get("priority") == priority]

    # Filter by label
    if label:
        cards = [c for c in cards if label in c.get("labels", [])]

    # Filter by due date
    if due:
        today = date.today()
        if due == "overdue":
            cards = [
                c
                for c in cards
                if c.get("due_date")
                and parse_date(c["due_date"]) < today
                and not c.get("completed_at")
            ]
        elif due == "today":
            cards = [
                c
                for c in cards
                if c.get("due_date") and parse_date(c["due_date"]) == today
            ]
        elif due == "this-week":
            from datetime import timedelta

            week_end = today + timedelta(days=7)
            cards = [
                c
                for c in cards
                if c.get("due_date") and today <= parse_date(c["due_date"]) <= week_end
            ]

    # Text search
    if q:
        cards = [
            c
            for c in cards
            if q in c.get("title", "").lower() or q in c.get("description", "").lower()
        ]

    return jsonify(cards)


@app.route("/api/v1/card", methods=["POST"])
def create_card():
    """Create a new card."""
    data = request.get_json() or {}
    board_id = data.get("board_id", "").strip()
    column_id = data.get("column_id", "").strip()
    title = data.get("title", "").strip()

    if not board_id or not column_id or not title:
        return jsonify(
            {
                "error": "Validation error",
                "message": "board_id, column_id, and title are required",
                "code": 400,
            }
        ), 400

    # Verify board and column exist
    board = store.get_board(board_id)
    if not board:
        return jsonify(
            {"error": "Not found", "message": "Board not found", "code": 404}
        ), 404

    valid_col = any(c["id"] == column_id for c in board.get("columns", []))
    if not valid_col:
        return jsonify(
            {"error": "Not found", "message": "Column not found", "code": 404}
        ), 404

    card = store.create_card(
        board_id=board_id,
        column_id=column_id,
        title=title,
        description=data.get("description", ""),
        priority=data.get("priority", "low"),
        label_ids=data.get("labels", []),
        due_date=data.get("due_date"),
    )
    return jsonify(card), 201


@app.route("/api/v1/card/<card_id>", methods=["GET"])
def get_card(card_id):
    """Get a single card."""
    card = store.get_card(card_id)
    if not card:
        return jsonify(
            {"error": "Not found", "message": "Card not found", "code": 404}
        ), 404
    return jsonify(card)


@app.route("/api/v1/card/<card_id>", methods=["PUT"])
def update_card(card_id):
    """Update a card."""
    data = request.get_json() or {}

    if "card_ids" in data:
        column_id = data.get("column_id")
        card_ids = data.get("card_ids", [])
        if column_id and card_ids:
            store.reorder_cards(column_id, card_ids)
            return jsonify({"message": "Cards reordered"})

    if "column_id" in data and "position" in data:
        new_column_id = data.get("column_id")
        new_position = data.get("position", 0)
        card = store.get_card(card_id)
        if not card:
            return jsonify(
                {"error": "Not found", "message": "Card not found", "code": 404}
            ), 404
        cards = store.get_cards()
        col_cards = [
            c
            for c in cards
            if c.get("column_id") == new_column_id and c.get("id") != card_id
        ]
        col_cards.sort(key=lambda c: c.get("position", 0))
        col_cards.insert(new_position, card)
        card_ids = [c.get("id") for c in col_cards]
        store.reorder_cards(new_column_id, card_ids)
        if card.get("column_id") != new_column_id:
            store.update_card(card_id, {"column_id": new_column_id})
        return jsonify({"message": "Card moved"})

    card = store.update_card(card_id, data)
    if not card:
        return jsonify(
            {"error": "Not found", "message": "Card not found", "code": 404}
        ), 404
    return jsonify(card)


@app.route("/api/v1/card/<card_id>", methods=["DELETE"])
def delete_card(card_id):
    """Delete a card."""
    card = store.get_card(card_id)
    if not card:
        return jsonify(
            {"error": "Not found", "message": "Card not found", "code": 404}
        ), 404
    store.delete_card(card_id)
    return jsonify({"message": "Card deleted"})


@app.route("/api/v1/labels", methods=["GET"])
def list_labels():
    """List all labels."""
    labels = store.get_labels()
    return jsonify(labels)


@app.route("/api/v1/labels", methods=["POST"])
def create_label():
    """Create a new label."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    color = data.get("color", "#e94560")

    if not name:
        return jsonify(
            {
                "error": "Validation error",
                "message": "Label name is required",
                "code": 400,
            }
        ), 400

    label = store.create_label(name, color)
    return jsonify(label), 201


@app.route("/api/v1/labels/<label_id>", methods=["DELETE"])
def delete_label(label_id):
    """Delete a label."""
    labels = store.get_labels()
    if not any(l.get("id") == label_id for l in labels):
        return jsonify(
            {"error": "Not found", "message": "Label not found", "code": 404}
        ), 404
    store.delete_label(label_id)
    return jsonify({"message": "Label deleted"})


@app.route("/api/v1/stats/<board_id>", methods=["GET"])
def get_stats(board_id):
    """Get board statistics."""
    stats = store.get_stats(board_id)
    if not stats:
        return jsonify(
            {"error": "Not found", "message": "Board not found", "code": 404}
        ), 404
    return jsonify(stats)


@app.route("/api/v1/export/<board_id>", methods=["GET"])
def export_board(board_id):
    """Export board to CSV."""
    csv_path = store.export_csv(board_id)
    if not csv_path or not os.path.exists(csv_path):
        return jsonify(
            {"error": "Not found", "message": "Board not found", "code": 404}
        ), 404

    return send_file(
        csv_path,
        mimetype="text/csv",
        as_attachment=True,
        download_name="board_export.csv",
    )


# ============================================================================
# Frontend Routes
# ============================================================================


@app.route("/")
def index():
    """Serve the main application."""
    return Response(HTML_TEMPLATE, mimetype="text/html")


# ============================================================================
# Embedded Frontend (HTML/CSS/JS)
# ============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KanboardX</title>
    <style>
        /* ============================================
           CSS Variables & Base Styles
           ============================================ */
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #0f3460;
            --bg-card-hover: #1a4a7a;
            --text-primary: #e8e8e8;
            --text-secondary: #a0a0a0;
            --accent: #e94560;
            --accent-hover: #ff6b8a;
            --success: #4ecca3;
            --warning: #f39c12;
            --danger: #e74c3c;
            --low: #95a5a6;
            --medium: #3498db;
            --high: #e67e22;
            --urgent: #e74c3c;
            --border: #2a2a4e;
            --shadow: rgba(0, 0, 0, 0.3);
            --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            --transition: all 0.2s ease;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--font-sans);
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ============================================
           Layout
           ============================================ */
        .app-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .header {
            background: var(--bg-secondary);
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
        }

        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
            letter-spacing: -0.5px;
        }

        .header-actions {
            display: flex;
            gap: 0.75rem;
            align-items: center;
        }

        .search-bar {
            display: flex;
            align-items: center;
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 0.5rem 1rem;
            width: 280px;
            transition: var(--transition);
        }

        .search-bar:focus-within {
            box-shadow: 0 0 0 2px var(--accent);
        }

        .search-bar input {
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 0.9rem;
            width: 100%;
            outline: none;
        }

        .search-bar input::placeholder {
            color: var(--text-secondary);
        }

        .main-content {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .board-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .board-header {
            padding: 1rem 1.5rem;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }

        .board-title {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .columns-container {
            display: flex;
            gap: 1rem;
            padding: 1.5rem;
            overflow-x: auto;
            flex: 1;
        }

        .column {
            background: var(--bg-secondary);
            border-radius: 12px;
            min-width: 300px;
            max-width: 300px;
            display: flex;
            flex-direction: column;
            max-height: calc(100vh - 200px);
        }

        .column-header {
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .column-title {
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary);
        }

        .column-count {
            background: var(--bg-card);
            padding: 0.2rem 0.5rem;
            border-radius: 12px;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        .column-cards {
            padding: 0.75rem;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            min-height: 100px;
        }

        .column-cards.drag-over {
            background: rgba(233, 69, 96, 0.1);
        }

        /* ============================================
           Cards
           ============================================ */
        .card {
            background: var(--bg-card);
            border-radius: 8px;
            padding: 1rem;
            cursor: grab;
            transition: var(--transition);
            box-shadow: 0 2px 8px var(--shadow);
        }

        .card:hover {
            background: var(--bg-card-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px var(--shadow);
        }

        .card.dragging {
            opacity: 0.5;
            cursor: grabbing;
        }

        .card-header {
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .card-title {
            flex: 1;
            font-weight: 500;
            line-height: 1.4;
            word-break: break-word;
        }

        .priority-badge {
            font-size: 0.7rem;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
            flex-shrink: 0;
        }

        .priority-low { background: var(--low); color: #1a1a2e; }
        .priority-medium { background: var(--medium); color: #fff; }
        .priority-high { background: var(--high); color: #fff; }
        .priority-urgent { background: var(--urgent); color: #fff; }

        .card-description {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .card-meta {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            align-items: center;
        }

        .card-labels {
            display: flex;
            gap: 0.25rem;
            flex-wrap: wrap;
        }

        .label-pill {
            font-size: 0.65rem;
            padding: 0.15rem 0.5rem;
            border-radius: 12px;
            color: #fff;
        }

        .due-date {
            font-size: 0.75rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }

        .due-date.overdue { color: var(--danger); }
        .due-date.today { color: var(--warning); }

        .add-card-btn {
            width: 100%;
            padding: 0.75rem;
            background: transparent;
            border: 2px dashed var(--border);
            border-radius: 8px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: var(--transition);
            font-size: 0.9rem;
        }

        .add-card-btn:hover {
            border-color: var(--accent);
            color: var(--accent);
        }

        /* ============================================
           Buttons
           ============================================ */
        .btn {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: var(--transition);
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: var(--accent);
            color: #fff;
        }

        .btn-primary:hover {
            background: var(--accent-hover);
        }

        .btn-secondary {
            background: var(--bg-card);
            color: var(--text-primary);
        }

        .btn-secondary:hover {
            background: var(--bg-card-hover);
        }

        .btn-danger {
            background: var(--danger);
            color: #fff;
        }

        .btn-icon {
            padding: 0.5rem;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            transition: var(--transition);
            border-radius: 4px;
        }

        .btn-icon:hover {
            background: var(--bg-card);
            color: var(--text-primary);
        }

        /* ============================================
           Forms
           ============================================ */
        .form-group {
            margin-bottom: 1rem;
        }

        .form-label {
            display: block;
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }

        .form-input, .form-textarea, .form-select {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 0.9rem;
            outline: none;
            transition: var(--transition);
        }

        .form-input:focus, .form-textarea:focus, .form-select:focus {
            border-color: var(--accent);
        }

        .form-textarea {
            min-height: 100px;
            resize: vertical;
            font-family: inherit;
        }

        /* ============================================
           Modal
           ============================================ */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: var(--transition);
        }

        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }

        .modal {
            background: var(--bg-secondary);
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
            transform: scale(0.9);
            transition: var(--transition);
        }

        .modal-overlay.active .modal {
            transform: scale(1);
        }

        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-title {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .modal-body {
            padding: 1.5rem;
        }

        .modal-footer {
            padding: 1.5rem;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: flex-end;
            gap: 0.75rem;
        }

        /* ============================================
           Sidebar (Stats)
           ============================================ */
        .sidebar {
            width: 280px;
            background: var(--bg-secondary);
            border-left: 1px solid var(--border);
            padding: 1.5rem;
            overflow-y: auto;
            flex-shrink: 0;
        }

        .sidebar-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-secondary);
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
        }

        .stat-label {
            color: var(--text-secondary);
        }

        .stat-value {
            font-weight: 600;
        }

        .priority-bars {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .priority-bar {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .priority-bar-label {
            font-size: 0.75rem;
            width: 60px;
            color: var(--text-secondary);
        }

        .priority-bar-track {
            flex: 1;
            height: 8px;
            background: var(--bg-primary);
            border-radius: 4px;
            overflow: hidden;
        }

        .priority-bar-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }

        .priority-bar-fill.low { background: var(--low); }
        .priority-bar-fill.medium { background: var(--medium); }
        .priority-bar-fill.high { background: var(--high); }
        .priority-bar-fill.urgent { background: var(--urgent); }

        /* ============================================
           Welcome Screen
           ============================================ */
        .welcome-screen {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            padding: 2rem;
            text-align: center;
        }

        .welcome-title {
            font-size: 2rem;
            font-weight: 700;
        }

        .welcome-subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            max-width: 400px;
        }

        /* ============================================
           Toast Notifications
           ============================================ */
        .toast-container {
            position: fixed;
            bottom: 1.5rem;
            right: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            z-index: 1100;
        }

        .toast {
            background: var(--bg-card);
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px var(--shadow);
            transform: translateX(120%);
            transition: var(--transition);
        }

        .toast.show {
            transform: translateX(0);
        }

        .toast.success { border-left: 4px solid var(--success); }
        .toast.error { border-left: 4px solid var(--danger); }

        /* ============================================
           Keyboard Shortcut Hints
           ============================================ */
        .shortcut-hint {
            position: fixed;
            bottom: 1rem;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.75rem;
            color: var(--text-secondary);
            display: flex;
            gap: 1.5rem;
        }

        .shortcut-hint kbd {
            background: var(--bg-card);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            margin-right: 0.25rem;
        }

        /* ============================================
           Loading State
           ============================================ */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .spinner {
            width: 32px;
            height: 32px;
            border: 3px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* ============================================
           Empty State
           ============================================ */
        .empty-state {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }

        /* ============================================
           Responsive
           ============================================ */
        @media (max-width: 1024px) {
            .sidebar {
                display: none;
            }
        }

        @media (max-width: 768px) {
            .header {
                padding: 0.75rem 1rem;
            }

            .search-bar {
                width: 100%;
                order: 3;
                margin-top: 0.5rem;
            }

            .header-actions {
                flex-wrap: wrap;
            }

            .column {
                min-width: 280px;
                max-width: 280px;
            }

            .board-header {
                flex-direction: column;
                gap: 0.75rem;
                align-items: stretch;
            }

            .shortcut-hint {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Header -->
        <header class="header">
            <div class="logo">KanboardX</div>
            <div class="header-actions">
                <div class="search-bar">
                    <span>🔍</span>
                    <input type="text" id="searchInput" placeholder="Search cards... (F)">
                </div>
                <button class="btn btn-primary" id="newBoardBtn">+ New Board</button>
            </div>
        </header>

        <!-- Main Content -->
        <main class="main-content">
            <!-- Board Area -->
            <div class="board-area">
                <!-- Welcome Screen (shown when no boards) -->
                <div class="welcome-screen" id="welcomeScreen">
                    <h1 class="welcome-title">Welcome to KanboardX</h1>
                    <p class="welcome-subtitle">A self-hosted Kanban board for managing your projects with style.</p>
                    <button class="btn btn-primary" id="createFirstBoard">Create Your First Board</button>
                </div>

                <!-- Board View -->
                <div id="boardView" style="display: none;">
                    <div class="board-header">
                        <h2 class="board-title" id="boardTitle">Board Name</h2>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-secondary" id="exportBtn">Export CSV</button>
                            <button class="btn btn-secondary" id="manageLabelsBtn">Labels</button>
                            <button class="btn btn-danger" id="deleteBoardBtn">Delete</button>
                        </div>
                    </div>
                    <div class="columns-container" id="columnsContainer">
                        <!-- Columns rendered here -->
                    </div>
                </div>
            </div>

            <!-- Sidebar (Stats) -->
            <aside class="sidebar" id="sidebar" style="display: none;">
                <h3 class="sidebar-title">Board Statistics</h3>
                <div class="stat-item">
                    <span class="stat-label">Total Cards</span>
                    <span class="stat-value" id="statTotal">0</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Completed</span>
                    <span class="stat-value" id="statCompleted">0</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Overdue</span>
                    <span class="stat-value" id="statOverdue">0</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Completion Rate</span>
                    <span class="stat-value" id="statRate">0%</span>
                </div>
                <div class="priority-bars">
                    <div class="priority-bar">
                        <span class="priority-bar-label">Low</span>
                        <div class="priority-bar-track">
                            <div class="priority-bar-fill low" id="barLow" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="priority-bar">
                        <span class="priority-bar-label">Medium</span>
                        <div class="priority-bar-track">
                            <div class="priority-bar-fill medium" id="barMedium" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="priority-bar">
                        <span class="priority-bar-label">High</span>
                        <div class="priority-bar-track">
                            <div class="priority-bar-fill high" id="barHigh" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="priority-bar">
                        <span class="priority-bar-label">Urgent</span>
                        <div class="priority-bar-track">
                            <div class="priority-bar-fill urgent" id="barUrgent" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
            </aside>
        </main>

        <!-- Keyboard Hints -->
        <div class="shortcut-hint" id="shortcutHint">
            <span><kbd>N</kbd> New Card</span>
            <span><kbd>F</kbd> Search</span>
            <span><kbd>Esc</kbd> Close</span>
            <span><kbd>Enter</kbd> Open</span>
        </div>

        <!-- Toast Container -->
        <div class="toast-container" id="toastContainer"></div>
    </div>

    <!-- Modals -->
    <!-- New Board Modal -->
    <div class="modal-overlay" id="newBoardModal">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Create New Board</h3>
                <button class="btn-icon close-modal">✕</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">Board Name</label>
                    <input type="text" class="form-input" id="boardNameInput" placeholder="My Project">
                </div>
                <div class="form-group">
                    <label class="form-label">Description (optional)</label>
                    <textarea class="form-textarea" id="boardDescInput" placeholder="What is this board for?"></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary close-modal">Cancel</button>
                <button class="btn btn-primary" id="createBoardBtn">Create Board</button>
            </div>
        </div>
    </div>

    <!-- Card Modal -->
    <div class="modal-overlay" id="cardModal">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title" id="cardModalTitle">New Card</h3>
                <button class="btn-icon close-modal">✕</button>
            </div>
            <div class="modal-body">
                <input type="hidden" id="cardIdInput">
                <input type="hidden" id="cardBoardIdInput">
                <div class="form-group">
                    <label class="form-label">Title</label>
                    <input type="text" class="form-input" id="cardTitleInput" placeholder="Card title">
                </div>
                <div class="form-group">
                    <label class="form-label">Description (Markdown supported)</label>
                    <textarea class="form-textarea" id="cardDescInput" placeholder="Write a description..." style="min-height: 150px;"></textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">Column</label>
                    <select class="form-select" id="cardColumnInput"></select>
                </div>
                <div class="form-group">
                    <label class="form-label">Priority</label>
                    <select class="form-select" id="cardPriorityInput">
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Due Date</label>
                    <input type="date" class="form-input" id="cardDueInput">
                </div>
                <div class="form-group">
                    <label class="form-label">Labels</label>
                    <div id="cardLabelsInput" style="display: flex; flex-wrap: wrap; gap: 0.5rem;"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-danger" id="deleteCardBtn" style="margin-right: auto;">Delete</button>
                <button class="btn btn-secondary close-modal">Cancel</button>
                <button class="btn btn-primary" id="saveCardBtn">Save</button>
            </div>
        </div>
    </div>

    <!-- Labels Modal -->
    <div class="modal-overlay" id="labelsModal">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Manage Labels</h3>
                <button class="btn-icon close-modal">✕</button>
            </div>
            <div class="modal-body">
                <div class="form-group" style="display: flex; gap: 0.5rem;">
                    <input type="text" class="form-input" id="newLabelName" placeholder="Label name">
                    <input type="color" id="newLabelColor" value="#e94560" style="width: 50px; height: 42px; padding: 2px;">
                    <button class="btn btn-primary" id="addLabelBtn">Add</button>
                </div>
                <div id="labelsList" style="margin-top: 1rem;"></div>
            </div>
        </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div class="modal-overlay" id="deleteConfirmModal">
        <div class="modal" style="max-width: 400px;">
            <div class="modal-header">
                <h3 class="modal-title">Confirm Delete</h3>
                <button class="btn-icon close-modal">✕</button>
            </div>
            <div class="modal-body">
                <p id="deleteConfirmText">Are you sure you want to delete this?</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary close-modal">Cancel</button>
                <button class="btn btn-danger" id="confirmDeleteBtn">Delete</button>
            </div>
        </div>
    </div>

    <script>
        // ============================================
        // Application State
        // ============================================
        const state = {
            boards: [],
            currentBoard: null,
            cards: [],
            labels: [],
            selectedCard: null,
            searchQuery: ''
        };

        let searchTimeout = null;
        let pendingDelete = null;

        // ============================================
        // Markdown Parser (Client-side regex)
        // ============================================
        function parseMarkdown(text) {
            if (!text) return '';

            const escapeHtml = (txt) => {
                if (!txt) return '';
                return txt.replace(/&/g, '&amp;')
                         .replace(/</g, '&lt;')
                         .replace(/>/g, '&gt;')
                         .replace(/"/g, '&quot;')
                         .replace(/'/g, '&#x27;');
            };

            text = escapeHtml(text);

            const lines = text.split('\n');
            let result = [];
            let inCodeBlock = false;
            let codeBuffer = [];

            for (let line of lines) {
                if (line.trim().startsWith('```')) {
                    if (inCodeBlock) {
                        result.push('<pre><code>' + codeBuffer.join('\n') + '</code></pre>');
                        codeBuffer = [];
                    }
                    inCodeBlock = !inCodeBlock;
                    continue;
                }

                if (inCodeBlock) {
                    codeBuffer.push(line);
                    continue;
                }

                if (line.trim().startsWith('### ')) {
                    result.push('<h4>' + line.substring(4) + '</h4>');
                } else if (line.trim().startsWith('## ')) {
                    result.push('<h3>' + line.substring(3) + '</h3>');
                } else if (line.trim().startsWith('# ')) {
                    result.push('<h2>' + line.substring(2) + '</h2>');
                } else if (line.trim().startsWith('- ')) {
                    result.push('<li>' + line.substring(2) + '</li>');
                } else if (line.trim()) {
                    let processed = line
                        .replace(/`([^`]+)`/g, '<code>$1</code>')
                        .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>')
                        .replace(/\\*([^*]+)\\*/g, '<em>$1</em>')
                        .replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
                    result.push('<p>' + processed + '</p>');
                }
            }

            if (inCodeBlock) {
                result.push('<pre><code>' + codeBuffer.join('\n') + '</code></pre>');
            }

            return result.join('\n');
        }

        function truncateMarkdown(text, maxLines = 2) {
            if (!text) return '';
            const lines = text.split('\n').filter(l => l.trim()).slice(0, maxLines);
            return lines.join(' ');
        }

        // ============================================
        // API Functions
        // ============================================
        async function apiCall(endpoint, options = {}) {
            const url = '/api/v1' + endpoint;
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'API Error');
            }

            return response.json();
        }

        // ============================================
        // Toast Notifications
        // ============================================
        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            container.appendChild(toast);

            setTimeout(() => toast.classList.add('show'), 10);
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        // ============================================
        // Render Functions
        // ============================================
        function renderBoardList() {
            const welcomeScreen = document.getElementById('welcomeScreen');
            const boardView = document.getElementById('boardView');
            const sidebar = document.getElementById('sidebar');

            if (state.boards.length === 0) {
                welcomeScreen.style.display = 'flex';
                boardView.style.display = 'none';
                sidebar.style.display = 'none';
                return;
            }

            // Auto-select first board if none selected
            if (!state.currentBoard) {
                state.currentBoard = state.boards[0];
            }

            if (state.currentBoard) {
                welcomeScreen.style.display = 'none';
                boardView.style.display = 'flex';
                renderBoard();
            } else {
                welcomeScreen.style.display = 'flex';
                boardView.style.display = 'none';
                sidebar.style.display = 'none';
            }
        }

        async function renderBoard() {
            if (!state.currentBoard) return;

            const board = state.currentBoard;
            document.getElementById('boardTitle').textContent = board.name;
            document.getElementById('sidebar').style.display = 'block';

            // Load cards for this board
            state.cards = await apiCall('/cards?board_id=' + board.id);
            state.labels = await apiCall('/labels');

            renderColumns();
            renderStats();
        }

        function renderColumns() {
            const container = document.getElementById('columnsContainer');
            container.innerHTML = '';

            if (!state.currentBoard) return;

            const columns = state.currentBoard.columns || [];
            const cards = state.cards;

            columns.sort((a, b) => a.order - b.order);

            for (const column of columns) {
                const columnCards = cards
                    .filter(c => c.column_id === column.id)
                    .sort((a, b) => a.position - b.position);

                const colDiv = document.createElement('div');
                colDiv.className = 'column';
                colDiv.dataset.columnId = column.id;

                colDiv.innerHTML = '
                    <div class="column-header">
                        <span class="column-title">' + column.name + '</span>
                        <span class="column-count">' + columnCards.length + '</span>
                    </div>
                    <div class="column-cards" data-column-id="' + column.id + '">
                        ' + columnCards.map(card => renderCard(card)).join('') + '
                        <button class="add-card-btn" data-column-id="' + column.id + '">+ Add Card</button>
                    </div>
                ';

                container.appendChild(colDiv);
            }

            // Bind drag events
            setupDragAndDrop();
        }

        function renderCard(card) {
            const labels = state.labels.filter(l => card.labels && card.labels.includes(l.id));
            const priorityClass = 'priority-' + (card.priority || 'low');

            let dueDateHtml = '';
            if (card.due_date) {
                const due = new Date(card.due_date);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                due.setHours(0, 0, 0, 0);

                let dueClass = '';
                if (due < today) dueClass = 'overdue';
                else if (due.getTime() === today.getTime()) dueClass = 'today';

                dueDateHtml = '<span class="due-date ' + dueClass + '">📅 ' + card.due_date + '</span>';
            }

            const desc = truncateMarkdown(card.description);
            const descHtml = desc ? '<div class="card-description">' + parseMarkdown(desc) + '</div>' : '';

            const labelHtml = labels.length > 0
                ? '<div class="card-labels">' + labels.map(l =>
                    '<span class="label-pill" style="background: ' + l.color + '">' + l.name + '</span>'
                  ).join('') + '</div>'
                : '';

            return '
                <div class="card" draggable="true" data-card-id="' + card.id + '">
                    <div class="card-header">
                        <span class="card-title">' + card.title + '</span>
                        <span class="priority-badge ' + priorityClass + '">' + (card.priority || 'low') + '</span>
                    </div>
                    ' + descHtml + '
                    <div class="card-meta">
                        ' + labelHtml + '
                        ' + dueDateHtml + '
                    </div>
                </div>
            ';
        }

        function renderStats() {
            updateStats();
        }

        async function updateStats() {
            if (!state.currentBoard) return;

            try {
                const stats = await apiCall('/stats/' + state.currentBoard.id);

                document.getElementById('statTotal').textContent = stats.total_cards || 0;
                document.getElementById('statCompleted').textContent = stats.completed || 0;
                document.getElementById('statOverdue').textContent = stats.overdue || 0;
                document.getElementById('statRate').textContent = (stats.completion_rate || 0) + '%';

                const byPriority = stats.by_priority || {};
                const total = stats.total_cards || 1;

                document.getElementById('barLow').style.width = ((byPriority.low || 0) / total * 100) + '%';
                document.getElementById('barMedium').style.width = ((byPriority.medium || 0) / total * 100) + '%';
                document.getElementById('barHigh').style.width = ((byPriority.high || 0) / total * 100) + '%';
                document.getElementById('barUrgent').style.width = ((byPriority.urgent || 0) / total * 100) + '%';
            } catch (e) {
                console.error('Failed to load stats:', e);
            }
        }

        function renderLabels() {
            const container = document.getElementById('labelsList');
            container.innerHTML = '';

            for (const label of state.labels) {
                const div = document.createElement('div');
                div.className = 'form-group';
                div.style.display = 'flex';
                div.style.alignItems = 'center';
                div.style.gap = '0.5rem';
                div.innerHTML = '
                    <span class="label-pill" style="background: ' + label.color + '">' + label.name + '</span>
                    <button class="btn-icon" data-delete-label="' + label.id + '">🗑️</button>
                ';
                container.appendChild(div);
            }

            // Bind delete label buttons
            container.querySelectorAll('[data-delete-label]').forEach(btn => {
                btn.addEventListener('click', async () => {
                    if (confirm('Delete this label?')) {
                        await apiCall('/labels/' + btn.dataset.deleteLabel, { method: 'DELETE' });
                        state.labels = await apiCall('/labels');
                        renderLabels();
                        showToast('Label deleted');
                    }
                });
            });
        }

        // ============================================
        // Drag and Drop
        // ============================================
        function setupDragAndDrop() {
            const cards = document.querySelectorAll('.card');
            const columns = document.querySelectorAll('.column-cards');

            cards.forEach(card => {
                card.addEventListener('dragstart', handleDragStart);
                card.addEventListener('dragend', handleDragEnd);
            });

            columns.forEach(col => {
                col.addEventListener('dragover', handleDragOver);
                col.addEventListener('dragleave', handleDragLeave);
                col.addEventListener('drop', handleDrop);
            });
        }

        let draggedCard = null;

        function handleDragStart(e) {
            draggedCard = e.target;
            e.target.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', e.target.dataset.cardId);
        }

        function handleDragEnd(e) {
            e.target.classList.remove('dragging');
            document.querySelectorAll('.column-cards').forEach(col => {
                col.classList.remove('drag-over');
            });
        }

        function handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            e.currentTarget.classList.add('drag-over');
        }

        function handleDragLeave(e) {
            e.currentTarget.classList.remove('drag-over');
        }

        async function handleDrop(e) {
            e.preventDefault();
            e.currentTarget.classList.remove('drag-over');

            const cardId = e.dataTransfer.getData('text/plain');
            const columnId = e.currentTarget.dataset.columnId;

            if (!cardId || !columnId) return;

            // Update card position
            const cardsInColumn = state.cards
                .filter(c => c.column_id === columnId)
                .sort((a, b) => a.position - b.position);

            // Find drop index (approximate based on target)
            let dropIndex = cardsInColumn.length;
            const targetCard = e.target.closest('.card');
            if (targetCard) {
                const targetId = targetCard.dataset.cardId;
                const targetIdx = cardsInColumn.findIndex(c => c.id === targetId);
                if (targetIdx >= 0) {
                    dropIndex = targetIdx;
                }
            }

            // Update card
            const card = state.cards.find(c => c.id === cardId);
            if (card && card.column_id !== columnId) {
                await apiCall('/card/' + cardId, {
                    method: 'PUT',
                    body: JSON.stringify({ column_id: columnId, position: dropIndex })
                });

                // Reload board
                await refreshBoard();
                showToast('Card moved');
            }
        }

        // ============================================
        // Modal Functions
        // ============================================
        function openModal(modalId) {
            document.getElementById(modalId).classList.add('active');
        }

        function closeModal(modalId) {
            document.getElementById(modalId).classList.remove('active');
        }

        function closeAllModals() {
            document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
        }

        // ============================================
        // Event Handlers
        // ============================================
        async function refreshBoard() {
            if (!state.currentBoard) return;
            state.currentBoard = await apiCall('/board/' + state.currentBoard.id);
            state.cards = await apiCall('/cards?board_id=' + state.currentBoard.id);
            state.labels = await apiCall('/labels');
            renderBoard();
        }

        // New Board
        document.getElementById('newBoardBtn').addEventListener('click', () => openModal('newBoardModal'));
        document.getElementById('createFirstBoard').addEventListener('click', () => openModal('newBoardModal'));

        document.getElementById('createBoardBtn').addEventListener('click', async () => {
            const name = document.getElementById('boardNameInput').value.trim();
            const description = document.getElementById('boardDescInput').value.trim();

            if (!name) {
                showToast('Board name is required', 'error');
                return;
            }

            try {
                const board = await apiCall('/board', {
                    method: 'POST',
                    body: JSON.stringify({ name, description })
                });

                state.boards = await apiCall('/boards');
                state.currentBoard = board;
                closeModal('newBoardModal');
                renderBoardList();
                showToast('Board created');

                document.getElementById('boardNameInput').value = '';
                document.getElementById('boardDescInput').value = '';
            } catch (e) {
                showToast(e.message, 'error');
            }
        });

        // Delete Board
        document.getElementById('deleteBoardBtn').addEventListener('click', () => {
            pendingDelete = { type: 'board' };
            document.getElementById('deleteConfirmText').textContent =
                'Are you sure you want to delete "' + state.currentBoard.name + '"? All cards will be deleted.';
            openModal('deleteConfirmModal');
        });

        // Export
        document.getElementById('exportBtn').addEventListener('click', async () => {
            if (!state.currentBoard) return;
            window.location.href = '/api/v1/export/' + state.currentBoard.id;
            showToast('Export started');
        });

        // Manage Labels
        document.getElementById('manageLabelsBtn').addEventListener('click', async () => {
            state.labels = await apiCall('/labels');
            renderLabels();
            openModal('labelsModal');
        });

        document.getElementById('addLabelBtn').addEventListener('click', async () => {
            const name = document.getElementById('newLabelName').value.trim();
            const color = document.getElementById('newLabelColor').value;

            if (!name) {
                showToast('Label name is required', 'error');
                return;
            }

            await apiCall('/labels', {
                method: 'POST',
                body: JSON.stringify({ name, color })
            });

            state.labels = await apiCall('/labels');
            renderLabels();
            document.getElementById('newLabelName').value = '';
            showToast('Label created');
        });

        // Search
        document.getElementById('searchInput').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(async () => {
                state.searchQuery = e.target.value.trim();
                if (state.searchQuery) {
                    state.cards = await apiCall('/cards?board_id=' + state.currentBoard.id + '&q=' + encodeURIComponent(state.searchQuery));
                    renderColumns();
                } else {
                    await refreshBoard();
                }
            }, 300);
        });

        // Add Card Button (in columns)
        document.addEventListener('click', async (e) => {
            if (e.target.classList.contains('add-card-btn')) {
                const columnId = e.target.dataset.columnId;
                state.selectedCard = null;

                // Populate column select
                const select = document.getElementById('cardColumnInput');
                select.innerHTML = '';
                for (const col of state.currentBoard.columns) {
                    const opt = document.createElement('option');
                    opt.value = col.id;
                    opt.textContent = col.name;
                    if (col.id === columnId) opt.selected = true;
                    select.appendChild(opt);
                }

                document.getElementById('cardModalTitle').textContent = 'New Card';
                document.getElementById('cardIdInput').value = '';
                document.getElementById('cardBoardIdInput').value = state.currentBoard.id;
                document.getElementById('cardTitleInput').value = '';
                document.getElementById('cardDescInput').value = '';
                document.getElementById('cardPriorityInput').value = 'low';
                document.getElementById('cardDueInput').value = '';
                document.getElementById('deleteCardBtn').style.display = 'none';

                // Render labels
                renderCardLabels();

                openModal('cardModal');
            }
        });

        // Card Click (view/edit)
        document.addEventListener('click', async (e) => {
            const cardEl = e.target.closest('.card');
            if (cardEl && !e.target.closest('a')) {
                const cardId = cardEl.dataset.cardId;
                const card = state.cards.find(c => c.id === cardId);

                if (card) {
                    state.selectedCard = card;

                    // Populate column select
                    const select = document.getElementById('cardColumnInput');
                    select.innerHTML = '';
                    for (const col of state.currentBoard.columns) {
                        const opt = document.createElement('option');
                        opt.value = col.id;
                        opt.textContent = col.name;
                        if (col.id === card.column_id) opt.selected = true;
                        select.appendChild(opt);
                    }

                    document.getElementById('cardModalTitle').textContent = 'Edit Card';
                    document.getElementById('cardIdInput').value = card.id;
                    document.getElementById('cardBoardIdInput').value = state.currentBoard.id;
                    document.getElementById('cardTitleInput').value = card.title;
                    document.getElementById('cardDescInput').value = card.description;
                    document.getElementById('cardPriorityInput').value = card.priority || 'low';
                    document.getElementById('cardDueInput').value = card.due_date || '';
                    document.getElementById('deleteCardBtn').style.display = 'block';

                    // Render labels
                    renderCardLabels(card.labels || []);

                    openModal('cardModal');
                }
            }
        });

        function renderCardLabels(selectedLabels = []) {
            const container = document.getElementById('cardLabelsInput');
            container.innerHTML = '';

            for (const label of state.labels) {
                const labelDiv = document.createElement('label');
                labelDiv.style.display = 'flex';
                labelDiv.style.alignItems = 'center';
                labelDiv.style.gap = '0.25rem';
                labelDiv.style.cursor = 'pointer';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = label.id;
                checkbox.checked = selectedLabels.includes(label.id);

                const pill = document.createElement('span');
                pill.className = 'label-pill';
                pill.style.background = label.color;
                pill.textContent = label.name;

                labelDiv.appendChild(checkbox);
                labelDiv.appendChild(pill);
                container.appendChild(labelDiv);
            }
        }

        // Save Card
        document.getElementById('saveCardBtn').addEventListener('click', async () => {
            const cardId = document.getElementById('cardIdInput').value;
            const title = document.getElementById('cardTitleInput').value.trim();
            const description = document.getElementById('cardDescInput').value.trim();
            const columnId = document.getElementById('cardColumnInput').value;
            const priority = document.getElementById('cardPriorityInput').value;
            const dueDate = document.getElementById('cardDueInput').value || null;

            // Get selected labels
            const labelCheckboxes = document.querySelectorAll('#cardLabelsInput input:checked');
            const labels = Array.from(labelCheckboxes).map(c => c.value);

            if (!title) {
                showToast('Card title is required', 'error');
                return;
            }

            try {
                if (cardId) {
                    // Update existing card
                    await apiCall('/card/' + cardId, {
                        method: 'PUT',
                        body: JSON.stringify({
                            title,
                            description,
                            column_id: columnId,
                            priority,
                            due_date: dueDate,
                            labels
                        })
                    });
                    showToast('Card updated');
                } else {
                    // Create new card
                    await apiCall('/card', {
                        method: 'POST',
                        body: JSON.stringify({
                            board_id: state.currentBoard.id,
                            column_id: columnId,
                            title,
                            description,
                            priority,
                            due_date: dueDate,
                            labels
                        })
                    });
                    showToast('Card created');
                }

                closeModal('cardModal');
                await refreshBoard();
            } catch (e) {
                showToast(e.message, 'error');
            }
        });

        // Delete Card
        document.getElementById('deleteCardBtn').addEventListener('click', async () => {
            pendingDelete = { type: 'card' };
            document.getElementById('deleteConfirmText').textContent = 'Are you sure you want to delete this card?';
            openModal('deleteConfirmModal');
        });

        // Confirm Delete
        document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
            if (!pendingDelete) return;

            try {
                if (pendingDelete.type === 'board') {
                    await apiCall('/board/' + state.currentBoard.id, { method: 'DELETE' });
                    state.boards = await apiCall('/boards');
                    state.currentBoard = state.boards[0] || null;
                    renderBoardList();
                    showToast('Board deleted');
                } else if (pendingDelete.type === 'card') {
                    const cardId = document.getElementById('cardIdInput').value;
                    await apiCall('/card/' + cardId, { method: 'DELETE' });
                    closeModal('cardModal');
                    await refreshBoard();
                    showToast('Card deleted');
                }
            } catch (e) {
                showToast(e.message, 'error');
            }

            pendingDelete = null;
            closeModal('deleteConfirmModal');
        });

        // Close Modal Buttons
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', closeAllModals);
        });

        // Close modals on overlay click
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    closeAllModals();
                }
            });
        });

        // ============================================
        // Keyboard Shortcuts
        // ============================================
        document.addEventListener('keydown', async (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                if (e.key === 'Escape') {
                    e.target.blur();
                    closeAllModals();
                } else if (e.ctrlKey && e.key === 's') {
                    e.preventDefault();
                    document.getElementById('saveCardBtn').click();
                }
                return;
            }

            if (e.ctrlKey || e.altKey) return;

            switch (e.key) {
                case 'n':
                case 'N':
                    // New card - open first column's add dialog
                    if (!e.ctrlKey && !e.altKey && state.currentBoard) {
                        const firstColumn = state.currentBoard.columns[0];
                        if (firstColumn) {
                            document.querySelector('[data-column-id="' + firstColumn.id + '"] .add-card-btn').click();
                        }
                    }
                    break;

                case 'f':
                case 'F':
                    document.getElementById('searchInput').focus();
                    break;

                case 'Escape':
                    closeAllModals();
                    document.getElementById('searchInput').blur();
                    document.getElementById('searchInput').value = '';
                    state.searchQuery = '';
                    refreshBoard();
                    break;

                case 'Enter':
                    // Open selected card
                    if (state.selectedCard) {
                        document.querySelector('[data-card-id="' + state.selectedCard.id + '"]').click();
                    }
                    break;

                case 'e':
                case 'E':
                    if (state.selectedCard) {
                        document.querySelector('[data-card-id="' + state.selectedCard.id + '"]').click();
                    }
                    break;

                case 'd':
                case 'D':
                    // Delete selected card
                    if (state.selectedCard) {
                        pendingDelete = { type: 'card' };
                        document.getElementById('deleteConfirmText').textContent = 'Delete this card?';
                        openModal('deleteConfirmModal');
                    }
                    break;

                case 'ArrowLeft':
                    // Navigate columns left
                    if (state.currentBoard) {
                        const cols = state.currentBoard.columns;
                        // Simple nav - could be enhanced
                    }
                    break;

                case 'ArrowRight':
                    // Navigate columns right
                    if (state.currentBoard) {
                        const cols = state.currentBoard.columns;
                        // Simple nav - could be enhanced
                    }
                    break;
            }
        });

        // ============================================
        // Initialization
        // ============================================
        async function init() {
            try {
                state.boards = await apiCall('/boards');
                state.labels = await apiCall('/labels');
                renderBoardList();
            } catch (e) {
                showToast('Failed to load boards', 'error');
            }
        }

        // Start the app
        init();
    </script>
</body>
</html>
"""


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KanboardX - Self-hosted Kanban Board")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Port to run the server on"
    )
    parser.add_argument(
        "--data", type=str, default=DATA_DIR, help="Data directory path"
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")

    args = parser.parse_args()

    # Override defaults if provided
    if args.data:
        DATA_DIR = args.data
        os.makedirs(DATA_DIR, exist_ok=True)

    print(f"Starting KanboardX on http://{args.host}:{args.port}")
    print(f"Data directory: {DATA_DIR}")

    app.run(host=args.host, port=args.port, debug=True)
