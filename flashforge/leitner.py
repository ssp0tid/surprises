from datetime import datetime, timedelta, timezone

from db import get_db

BOX_INTERVALS = {
    1: timedelta(days=1),
    2: timedelta(days=3),
    3: timedelta(days=7),
    4: timedelta(days=14),
    5: timedelta(days=30),
}


def calculate_next_review(box: int) -> datetime:
    now = datetime.now(timezone.utc)
    interval = BOX_INTERVALS.get(box, timedelta(days=1))
    return now + interval


def get_due_cards(deck_id: int) -> list[dict]:
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    rows = db.execute(
        "SELECT id, front, back, box, next_review FROM cards "
        "WHERE deck_id = ? AND next_review <= ? "
        "ORDER BY box ASC, next_review ASC",
        (deck_id, now),
    ).fetchall()
    return [dict(row) for row in rows]


def update_card_box(card_id: int, response: str) -> None:
    db = get_db()
    row = db.execute("SELECT box FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        raise ValueError(f"Card {card_id} not found")

    old_box = row["box"]

    if response == "again":
        new_box = 1
    elif response == "hard":
        new_box = old_box
    elif response == "good":
        new_box = min(old_box + 1, 5)
    elif response == "easy":
        new_box = min(old_box + 2, 5)
    else:
        raise ValueError(f"Invalid response: {response}")

    next_review = calculate_next_review(new_box)

    db.execute(
        "UPDATE cards SET box = ?, next_review = ?, last_reviewed = ? WHERE id = ?",
        (new_box, next_review.isoformat(), datetime.now(timezone.utc).isoformat(), card_id),
    )
    db.execute(
        "INSERT INTO reviews (card_id, response, old_box, new_box) VALUES (?, ?, ?, ?)",
        (card_id, response, old_box, new_box),
    )
    db.commit()
