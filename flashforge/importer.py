import csv
from pathlib import Path

from db import get_db
from leitner import calculate_next_review


def import_csv(deck_id: int, filepath: str) -> int:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    db = get_db()
    count = 0

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV file is empty (no header row)")

        normalized_header = [col.strip().lower() for col in header]
        if "front" not in normalized_header or "back" not in normalized_header:
            raise ValueError(
                f"CSV must have 'front' and 'back' columns in header. "
                f"Found: {header}"
            )

        front_idx = normalized_header.index("front")
        back_idx = normalized_header.index("back")

        for row in reader:
            if len(row) <= max(front_idx, back_idx):
                continue
            front, back = row[front_idx].strip(), row[back_idx].strip()
            if not front or not back:
                continue
            next_review = calculate_next_review(1).isoformat()
            db.execute(
                "INSERT INTO cards (deck_id, front, back, box, next_review) VALUES (?, ?, ?, 1, ?)",
                (deck_id, front, back, next_review),
            )
            count += 1

    db.commit()
    return count


def import_markdown(deck_id: int, filepath: str) -> int:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    db = get_db()
    count = 0
    current_front = None
    answer_lines = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            line_stripped = line.strip()
            if line_stripped.startswith("## "):
                if current_front and answer_lines:
                    back = "\n".join(answer_lines).strip()
                    if back:
                        next_review = calculate_next_review(1).isoformat()
                        db.execute(
                            "INSERT INTO cards (deck_id, front, back, box, next_review) VALUES (?, ?, ?, 1, ?)",
                            (deck_id, current_front, back, next_review),
                        )
                        count += 1
                current_front = line_stripped[3:].strip()
                answer_lines = []
            elif current_front is not None:
                answer_lines.append(line_stripped)

    if current_front and answer_lines:
        back = "\n".join(answer_lines).strip()
        if back:
            next_review = calculate_next_review(1).isoformat()
            db.execute(
                "INSERT INTO cards (deck_id, front, back, box, next_review) VALUES (?, ?, ?, 1, ?)",
                (deck_id, current_front, back, next_review),
            )
            count += 1

    db.commit()
    return count


def export_csv(deck_id: int, filepath: str) -> int:
    db = get_db()
    rows = db.execute(
        "SELECT front, back FROM cards WHERE deck_id = ? ORDER BY id",
        (deck_id,),
    ).fetchall()

    path = Path(filepath)
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["front", "back"])
            for row in rows:
                writer.writerow([row["front"], row["back"]])
    except OSError as e:
        raise OSError(f"Cannot write to '{filepath}': {e}") from e

    return len(rows)
