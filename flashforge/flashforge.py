import sys

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from db import get_db
from leitner import get_due_cards, update_card_box
from importer import import_csv, import_markdown, export_csv
from stats import get_deck_stats, get_global_stats, render_stats

console = Console()


@click.group()
def cli():
    """FlashForge - Spaced repetition flashcards in your terminal."""
    pass


# --- Deck commands ---

@cli.group()
def deck():
    """Manage flashcard decks."""
    pass


@deck.command("create")
@click.argument("name")
def deck_create(name):
    """Create a new deck."""
    db = get_db()
    try:
        db.execute("INSERT INTO decks (name) VALUES (?)", (name,))
        db.commit()
        console.print(f"[green]Created deck:[/green] {name}")
    except Exception:
        console.print(f"[red]Error:[/red] Deck '{name}' already exists.")
        sys.exit(1)


@deck.command("list")
def deck_list():
    """List all decks with card counts."""
    db = get_db()
    rows = db.execute(
        "SELECT d.id, d.name, COUNT(c.id) as card_count "
        "FROM decks d LEFT JOIN cards c ON d.id = c.deck_id "
        "GROUP BY d.id ORDER BY d.name"
    ).fetchall()

    if not rows:
        console.print("[dim]No decks yet. Create one with:[/dim] flashforge deck create <name>")
        return

    table = Table(title="Decks")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Name", style="cyan")
    table.add_column("Cards", style="green", justify="right")

    for row in rows:
        table.add_row(str(row["id"]), row["name"], str(row["card_count"]))

    console.print(table)


@deck.command("delete")
@click.argument("name")
def deck_delete(name):
    """Delete a deck and all its cards."""
    db = get_db()
    row = db.execute("SELECT id FROM decks WHERE name = ?", (name,)).fetchone()
    if row is None:
        console.print(f"[red]Error:[/red] Deck '{name}' not found.")
        sys.exit(1)

    if not click.confirm(f"Delete deck '{name}' and all its cards?"):
        console.print("[dim]Cancelled.[/dim]")
        return

    db.execute("DELETE FROM decks WHERE id = ?", (row["id"],))
    db.commit()
    console.print(f"[green]Deleted deck:[/green] {name}")


@deck.command("rename")
@click.argument("old")
@click.argument("new")
def deck_rename(old, new):
    """Rename a deck."""
    db = get_db()
    row = db.execute("SELECT id FROM decks WHERE name = ?", (old,)).fetchone()
    if row is None:
        console.print(f"[red]Error:[/red] Deck '{old}' not found.")
        sys.exit(1)

    try:
        db.execute("UPDATE decks SET name = ? WHERE id = ?", (new, row["id"]))
        db.commit()
        console.print(f"[green]Renamed:[/green] {old} → {new}")
    except Exception:
        console.print(f"[red]Error:[/red] Deck '{new}' already exists.")
        sys.exit(1)


# --- Card commands ---

@cli.group()
def card():
    """Manage individual cards."""
    pass


@card.command("add")
@click.argument("deck_name")
@click.option("--front", "-f", required=True, help="Front of the card (question)")
@click.option("--back", "-b", required=True, help="Back of the card (answer)")
def card_add(deck_name, front, back):
    """Add a card to a deck."""
    db = get_db()
    row = db.execute("SELECT id FROM decks WHERE name = ?", (deck_name,)).fetchone()
    if row is None:
        console.print(f"[red]Error:[/red] Deck '{deck_name}' not found.")
        sys.exit(1)

    from leitner import calculate_next_review
    next_review = calculate_next_review(1).isoformat()
    db.execute(
        "INSERT INTO cards (deck_id, front, back, box, next_review) VALUES (?, ?, ?, 1, ?)",
        (row["id"], front, back, next_review),
    )
    db.commit()
    console.print(f"[green]Added card to '{deck_name}'[/green]")


@card.command("list")
@click.argument("deck_name")
def card_list(deck_name):
    """List all cards in a deck."""
    db = get_db()
    deck_row = db.execute("SELECT id FROM decks WHERE name = ?", (deck_name,)).fetchone()
    if deck_row is None:
        console.print(f"[red]Error:[/red] Deck '{deck_name}' not found.")
        sys.exit(1)

    rows = db.execute(
        "SELECT id, front, back, box, next_review FROM cards WHERE deck_id = ? ORDER BY id",
        (deck_row["id"],),
    ).fetchall()

    if not rows:
        console.print(f"[dim]No cards in '{deck_name}'. Add one with:[/dim] flashforge card add {deck_name} --front \"Q\" --back \"A\"")
        return

    table = Table(title=f"Cards in '{deck_name}'")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Front", style="cyan", max_width=40)
    table.add_column("Back", style="green", max_width=40)
    table.add_column("Box", justify="center", width=5)
    table.add_column("Next Review", style="dim", width=12)

    for row in rows:
        next_rev = row["next_review"][:10] if row["next_review"] else "—"
        table.add_row(str(row["id"]), row["front"], row["back"], str(row["box"]), next_rev)

    console.print(table)


@card.command("delete")
@click.argument("card_id", type=int)
def card_delete(card_id):
    """Delete a card by ID."""
    db = get_db()
    row = db.execute("SELECT id FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        console.print(f"[red]Error:[/red] Card {card_id} not found.")
        sys.exit(1)

    db.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    db.commit()
    console.print(f"[green]Deleted card {card_id}[/green]")


@card.command("edit")
@click.argument("card_id", type=int)
@click.option("--front", "-f", default=None, help="New front text")
@click.option("--back", "-b", default=None, help="New back text")
def card_edit(card_id, front, back):
    """Edit a card's front or back text."""
    if front is None and back is None:
        console.print("[red]Error:[/red] Provide --front and/or --back to edit.")
        sys.exit(1)

    db = get_db()
    row = db.execute("SELECT id FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        console.print(f"[red]Error:[/red] Card {card_id} not found.")
        sys.exit(1)

    if front is not None:
        db.execute("UPDATE cards SET front = ? WHERE id = ?", (front, card_id))
    if back is not None:
        db.execute("UPDATE cards SET back = ? WHERE id = ?", (back, card_id))
    db.commit()
    console.print(f"[green]Updated card {card_id}[/green]")


# --- Study command ---

@cli.command()
@click.argument("deck_name")
def study(deck_name):
    """Start an interactive study session."""
    db = get_db()
    deck_row = db.execute("SELECT id FROM decks WHERE name = ?", (deck_name,)).fetchone()
    if deck_row is None:
        console.print(f"[red]Error:[/red] Deck '{deck_name}' not found.")
        sys.exit(1)

    due_cards = get_due_cards(deck_row["id"])
    if not due_cards:
        console.print(f"[green]No cards due in '{deck_name}'![/green] Come back later.")
        return

    console.print(f"\n[bold]Study Session:[/bold] {deck_name} ({len(due_cards)} cards due)\n")
    console.print("[dim]Press Enter to reveal answer. Press 'q' to quit.[/dim]\n")

    reviewed = 0
    correct = 0
    quit_session = False

    try:
        for card in due_cards:
            console.print(Panel(card["front"], title=f"Card {card['id']} (Box {card['box']})", border_style="cyan"))

            user_input = input("  [Enter to reveal, q to quit] ")
            if user_input.strip().lower() == "q":
                quit_session = True
                break

            console.print(Panel(card["back"], title="Answer", border_style="green"))
            console.print("  [1] Again  [2] Hard  [3] Good  [4] Easy")

            while True:
                response_key = click.getchar()
                if response_key == "q":
                    quit_session = True
                    break
                response_map = {"1": "again", "2": "hard", "3": "good", "4": "easy"}
                if response_key in response_map:
                    response = response_map[response_key]
                    update_card_box(card["id"], response)
                    reviewed += 1
                    if response in ("good", "easy"):
                        correct += 1
                    console.print(f"  [dim]→ {response}[/dim]\n")
                    break
                else:
                    console.print("  [dim]Press 1-4 or q[/dim]")

            if quit_session:
                break
    except KeyboardInterrupt:
        console.print("\n[dim]Session interrupted.[/dim]")

    console.print(f"\n[bold]Session complete![/bold]")
    console.print(f"  Cards reviewed: {reviewed}")
    if reviewed > 0:
        console.print(f"  Accuracy: {correct / reviewed * 100:.0f}%")


# --- Import commands ---

@cli.group("import")
def import_cmd():
    """Import cards from files."""
    pass


@import_cmd.command("csv")
@click.argument("deck_name")
@click.argument("filepath", type=click.Path(exists=True))
def import_csv_cmd(deck_name, filepath):
    """Import cards from a CSV file (front,back columns)."""
    db = get_db()
    deck_row = db.execute("SELECT id FROM decks WHERE name = ?", (deck_name,)).fetchone()
    if deck_row is None:
        console.print(f"[red]Error:[/red] Deck '{deck_name}' not found.")
        sys.exit(1)

    try:
        count = import_csv(deck_row["id"], filepath)
        console.print(f"[green]Imported {count} cards into '{deck_name}'[/green]")
    except Exception as e:
        console.print(f"[red]Error importing CSV:[/red] {e}")
        sys.exit(1)


@import_cmd.command("markdown")
@click.argument("deck_name")
@click.argument("filepath", type=click.Path(exists=True))
def import_markdown_cmd(deck_name, filepath):
    """Import cards from a Markdown file (## question / answer format)."""
    db = get_db()
    deck_row = db.execute("SELECT id FROM decks WHERE name = ?", (deck_name,)).fetchone()
    if deck_row is None:
        console.print(f"[red]Error:[/red] Deck '{deck_name}' not found.")
        sys.exit(1)

    try:
        count = import_markdown(deck_row["id"], filepath)
        console.print(f"[green]Imported {count} cards into '{deck_name}'[/green]")
    except Exception as e:
        console.print(f"[red]Error importing Markdown:[/red] {e}")
        sys.exit(1)


# --- Export command ---

@cli.command("export")
@click.argument("deck_name")
@click.argument("filepath")
def export_cmd(deck_name, filepath):
    """Export a deck to CSV."""
    db = get_db()
    deck_row = db.execute("SELECT id FROM decks WHERE name = ?", (deck_name,)).fetchone()
    if deck_row is None:
        console.print(f"[red]Error:[/red] Deck '{deck_name}' not found.")
        sys.exit(1)

    try:
        count = export_csv(deck_row["id"], filepath)
        console.print(f"[green]Exported {count} cards to '{filepath}'[/green]")
    except Exception as e:
        console.print(f"[red]Error exporting:[/red] {e}")
        sys.exit(1)


# --- Stats command ---

@cli.command()
@click.argument("deck_name", required=False)
@click.option("--all", "show_all", is_flag=True, help="Show global statistics")
def stats(deck_name, show_all):
    """View study statistics."""
    if show_all:
        data = get_global_stats()
        console.print(Panel("[bold]Global Statistics[/bold]", border_style="blue"))
        render_stats(data)
        return

    if deck_name is None:
        console.print("[red]Error:[/red] Provide a deck name or use --all for global stats.")
        sys.exit(1)

    db = get_db()
    deck_row = db.execute("SELECT id FROM decks WHERE name = ?", (deck_name,)).fetchone()
    if deck_row is None:
        console.print(f"[red]Error:[/red] Deck '{deck_name}' not found.")
        sys.exit(1)

    data = get_deck_stats(deck_row["id"])
    console.print(Panel(f"[bold]Statistics for '{deck_name}'[/bold]", border_style="blue"))
    render_stats(data)


if __name__ == "__main__":
    try:
        cli()
    except RuntimeError as e:
        console.print(f"[red]Fatal error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(130)
