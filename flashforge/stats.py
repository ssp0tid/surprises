from datetime import datetime, timedelta, timezone

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.bar import Bar

from db import get_db

console = Console()


def get_deck_stats(deck_id: int) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)

    total = db.execute("SELECT COUNT(*) as c FROM cards WHERE deck_id = ?", (deck_id,)).fetchone()["c"]

    box_counts = {}
    for i in range(1, 6):
        row = db.execute(
            "SELECT COUNT(*) as c FROM cards WHERE deck_id = ? AND box = ?", (deck_id, i)
        ).fetchone()
        box_counts[i] = row["c"]

    due_today = db.execute(
        "SELECT COUNT(*) as c FROM cards WHERE deck_id = ? AND next_review <= ?",
        (deck_id, now.isoformat()),
    ).fetchone()["c"]

    seven_days_ago = (now - timedelta(days=7)).isoformat()
    reviews_7d = db.execute(
        "SELECT response FROM reviews r JOIN cards c ON r.card_id = c.id "
        "WHERE c.deck_id = ? AND r.reviewed_at >= ?",
        (deck_id, seven_days_ago),
    ).fetchall()

    total_reviews_7d = len(reviews_7d)
    correct_7d = sum(1 for r in reviews_7d if r["response"] in ("good", "easy"))
    accuracy = (correct_7d / total_reviews_7d * 100) if total_reviews_7d > 0 else 0.0

    mastered = box_counts.get(4, 0) + box_counts.get(5, 0)
    mastery_rate = (mastered / total * 100) if total > 0 else 0.0

    streak = _calculate_streak(deck_id)

    return {
        "total_cards": total,
        "box_counts": box_counts,
        "due_today": due_today,
        "streak": streak,
        "accuracy_7d": accuracy,
        "mastery_rate": mastery_rate,
    }


def get_global_stats() -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)

    total = db.execute("SELECT COUNT(*) as c FROM cards").fetchone()["c"]

    box_counts = {}
    for i in range(1, 6):
        row = db.execute("SELECT COUNT(*) as c FROM cards WHERE box = ?", (i,)).fetchone()
        box_counts[i] = row["c"]

    due_today = db.execute(
        "SELECT COUNT(*) as c FROM cards WHERE next_review <= ?", (now.isoformat(),)
    ).fetchone()["c"]

    seven_days_ago = (now - timedelta(days=7)).isoformat()
    reviews_7d = db.execute(
        "SELECT response FROM reviews WHERE reviewed_at >= ?", (seven_days_ago,)
    ).fetchall()

    total_reviews_7d = len(reviews_7d)
    correct_7d = sum(1 for r in reviews_7d if r["response"] in ("good", "easy"))
    accuracy = (correct_7d / total_reviews_7d * 100) if total_reviews_7d > 0 else 0.0

    mastered = box_counts.get(4, 0) + box_counts.get(5, 0)
    mastery_rate = (mastered / total * 100) if total > 0 else 0.0

    streak = _calculate_global_streak()

    deck_count = db.execute("SELECT COUNT(*) as c FROM decks").fetchone()["c"]

    return {
        "total_cards": total,
        "deck_count": deck_count,
        "box_counts": box_counts,
        "due_today": due_today,
        "streak": streak,
        "accuracy_7d": accuracy,
        "mastery_rate": mastery_rate,
    }


def render_stats(stats: dict) -> None:
    table = Table(title="Cards per Box", show_header=True)
    table.add_column("Box", style="cyan", width=6)
    table.add_column("Cards", style="green", width=8)
    table.add_column("Bar", width=30)

    max_count = max(stats["box_counts"].values()) if stats["box_counts"] else 1
    intervals = ["1 day", "3 days", "7 days", "14 days", "30 days"]

    for i in range(1, 6):
        count = stats["box_counts"].get(i, 0)
        bar_width = int((count / max_count) * 20) if max_count > 0 else 0
        bar_str = "█" * bar_width
        table.add_row(f"{i} ({intervals[i-1]})", str(count), f"[green]{bar_str}[/green]")

    console.print(table)
    console.print()

    info_lines = [
        f"[bold]Total Cards:[/bold] {stats['total_cards']}",
        f"[bold]Due Today:[/bold] {stats['due_today']}",
        f"[bold]Study Streak:[/bold] {stats['streak']} day{'s' if stats['streak'] != 1 else ''}",
        f"[bold]Accuracy (7d):[/bold] {stats['accuracy_7d']:.1f}%",
        f"[bold]Mastery Rate:[/bold] {stats['mastery_rate']:.1f}% (cards in box 4+)",
    ]

    if "deck_count" in stats:
        info_lines.insert(0, f"[bold]Total Decks:[/bold] {stats['deck_count']}")

    console.print(Panel("\n".join(info_lines), title="Statistics", border_style="blue"))


def _calculate_streak(deck_id: int) -> int:
    db = get_db()
    rows = db.execute(
        "SELECT DISTINCT date(r.reviewed_at) as d FROM reviews r "
        "JOIN cards c ON r.card_id = c.id WHERE c.deck_id = ? "
        "ORDER BY d DESC",
        (deck_id,),
    ).fetchall()
    return _streak_from_dates([row["d"] for row in rows])


def _calculate_global_streak() -> int:
    db = get_db()
    rows = db.execute(
        "SELECT DISTINCT date(reviewed_at) as d FROM reviews ORDER BY d DESC"
    ).fetchall()
    return _streak_from_dates([row["d"] for row in rows])


def _streak_from_dates(dates: list[str]) -> int:
    if not dates:
        return 0

    today = datetime.now(timezone.utc).date()
    streak = 0

    for i, date_str in enumerate(dates):
        try:
            review_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            break
        expected = today - timedelta(days=i)
        if review_date == expected:
            streak += 1
        else:
            break

    return streak
