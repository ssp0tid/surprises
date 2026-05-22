import json
import logging
import sqlite3
from datetime import datetime, timezone

from flask import Flask, g, jsonify, render_template, request

from nonogram import generate_puzzle, validate_solution

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

DIFFICULTIES = {
    "easy": {"rows": 5, "cols": 5, "density": 0.4},
    "medium": {"rows": 10, "cols": 10, "density": 0.5},
    "hard": {"rows": 15, "cols": 15, "density": 0.55},
}

DATABASE = "nonogram.db"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS puzzles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            difficulty TEXT NOT NULL,
            row_clues TEXT NOT NULL,
            col_clues TEXT NOT NULL,
            solution TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            puzzle_id INTEGER NOT NULL,
            player_grid TEXT NOT NULL,
            elapsed_seconds INTEGER NOT NULL DEFAULT 0,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (puzzle_id) REFERENCES puzzles(id)
        );
    """)
    db.commit()


with app.app_context():
    init_db()


@app.errorhandler(500)
def internal_error(exc):
    app.logger.exception("Unhandled error")
    return jsonify({"error": "Internal server error"}), 500


@app.route("/")
def index():
    db = get_db()
    saves = db.execute(
        """SELECT s.id, s.puzzle_id, s.elapsed_seconds, s.completed, s.updated_at, p.difficulty
           FROM saves s JOIN puzzles p ON s.puzzle_id = p.id
           ORDER BY s.updated_at DESC"""
    ).fetchall()
    return render_template("index.html", saves=saves)


@app.route("/api/new-game", methods=["POST"])
def new_game():
    data = request.get_json()
    if not data or "difficulty" not in data:
        return jsonify({"error": "Missing difficulty"}), 400

    difficulty = data["difficulty"]
    if difficulty not in DIFFICULTIES:
        return jsonify({"error": "Invalid difficulty"}), 400

    params = DIFFICULTIES[difficulty]
    puzzle = generate_puzzle(params["rows"], params["cols"], params["density"])
    now = datetime.now(timezone.utc).isoformat()

    db = get_db()
    cursor = db.execute(
        "INSERT INTO puzzles (difficulty, row_clues, col_clues, solution, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            difficulty,
            json.dumps(puzzle["row_clues"]),
            json.dumps(puzzle["col_clues"]),
            json.dumps(puzzle["solution"]),
            now,
        ),
    )
    puzzle_id = cursor.lastrowid

    empty_grid = [[0] * params["cols"] for _ in range(params["rows"])]
    db.execute(
        "INSERT INTO saves (puzzle_id, player_grid, elapsed_seconds, completed, created_at, updated_at) VALUES (?, ?, 0, 0, ?, ?)",
        (puzzle_id, json.dumps(empty_grid), now, now),
    )
    db.commit()

    return jsonify({"puzzle_id": puzzle_id, "row_clues": puzzle["row_clues"], "col_clues": puzzle["col_clues"]})


@app.route("/api/game/<int:game_id>")
def get_game(game_id):
    db = get_db()
    save = db.execute(
        "SELECT s.*, p.row_clues, p.col_clues, p.difficulty FROM saves s JOIN puzzles p ON s.puzzle_id = p.id WHERE s.puzzle_id = ?",
        (game_id,),
    ).fetchone()

    if not save:
        return jsonify({"error": "Game not found"}), 404

    return jsonify({
        "puzzle_id": save["puzzle_id"],
        "difficulty": save["difficulty"],
        "row_clues": json.loads(save["row_clues"]),
        "col_clues": json.loads(save["col_clues"]),
        "player_grid": json.loads(save["player_grid"]),
        "elapsed_seconds": save["elapsed_seconds"],
        "completed": bool(save["completed"]),
    })


@app.route("/api/save", methods=["POST"])
def save_game():
    data = request.get_json()
    if not data or "puzzle_id" not in data or "player_grid" not in data:
        return jsonify({"error": "Missing puzzle_id or player_grid"}), 400

    player_grid = data["player_grid"]
    if not isinstance(player_grid, list) or not player_grid:
        return jsonify({"error": "player_grid must be a non-empty list"}), 400
    if not all(isinstance(row, list) for row in player_grid):
        return jsonify({"error": "player_grid rows must be lists"}), 400
    expected_cols = len(player_grid[0])
    if any(len(row) != expected_cols for row in player_grid):
        return jsonify({"error": "player_grid rows must have consistent length"}), 400
    if not all(cell in (0, 1, 2) for row in player_grid for cell in row):
        return jsonify({"error": "player_grid cells must be 0, 1, or 2"}), 400

    now = datetime.now(timezone.utc).isoformat()
    db = get_db()

    existing = db.execute("SELECT id FROM saves WHERE puzzle_id = ?", (data["puzzle_id"],)).fetchone()
    if not existing:
        return jsonify({"error": "No save found for this puzzle"}), 404

    db.execute(
        "UPDATE saves SET player_grid = ?, elapsed_seconds = ?, updated_at = ? WHERE puzzle_id = ?",
        (json.dumps(player_grid), data.get("elapsed_seconds", 0), now, data["puzzle_id"]),
    )
    db.commit()
    return jsonify({"status": "saved"})


@app.route("/api/check", methods=["POST"])
def check_solution():
    data = request.get_json()
    if not data or "puzzle_id" not in data or "player_grid" not in data:
        return jsonify({"error": "Missing puzzle_id or player_grid"}), 400

    player_grid = data["player_grid"]
    if not isinstance(player_grid, list) or not player_grid:
        return jsonify({"error": "player_grid must be a non-empty list"}), 400
    if not all(isinstance(row, list) for row in player_grid):
        return jsonify({"error": "player_grid rows must be lists"}), 400

    db = get_db()
    puzzle = db.execute("SELECT row_clues, col_clues FROM puzzles WHERE id = ?", (data["puzzle_id"],)).fetchone()
    if not puzzle:
        return jsonify({"error": "Puzzle not found"}), 404

    row_clues = json.loads(puzzle["row_clues"])
    col_clues = json.loads(puzzle["col_clues"])

    correct = validate_solution(player_grid, row_clues, col_clues)

    if correct:
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "UPDATE saves SET completed = 1, player_grid = ?, elapsed_seconds = ?, updated_at = ? WHERE puzzle_id = ?",
            (json.dumps(player_grid), data.get("elapsed_seconds", 0), now, data["puzzle_id"]),
        )
        db.commit()

    return jsonify({"correct": correct})


@app.route("/play/<int:game_id>")
def play(game_id):
    db = get_db()
    save = db.execute(
        "SELECT s.*, p.row_clues, p.col_clues, p.difficulty FROM saves s JOIN puzzles p ON s.puzzle_id = p.id WHERE s.puzzle_id = ?",
        (game_id,),
    ).fetchone()
    if not save:
        return "Game not found", 404
    return render_template("play.html", game_id=game_id)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
