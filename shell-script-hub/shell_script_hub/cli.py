"""Click CLI for shell-script-hub."""

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from shell_script_hub.db import Database
from shell_script_hub.script_runner import (
    ScriptRunner,
    serialize_variables,
)
from shell_script_hub.templates import TemplateEngine

console = Console()


def get_db() -> Database:
    """Get database instance."""
    return Database()


@click.group()
def cli():
    """Shell Script Hub - Organize, tag, search, and execute shell scripts."""
    pass


@cli.command()
def init():
    """Initialize script hub in current directory."""
    db = get_db()
    console.print(f"[green]Initialized shell-script-hub at {db.db_path}[/green]")


@cli.command()
@click.argument("script_path", type=click.Path(exists=True))
@click.option("--name", "-n", help="Name for the script (default: filename)")
@click.option("--description", "-d", help="Script description")
@click.option("--tags", "-t", help="Comma-separated tags")
@click.option("--update", "-u", is_flag=True, help="Update existing script")
def add(script_path, name, description, tags, update):
    """Add a script to the registry."""
    script_path = Path(script_path)
    name = name or script_path.stem

    content = script_path.read_text()
    db = get_db()

    if update:
        try:
            script = db.update_script(
                name=name,
                content=content,
                description=description,
                tags=tags,
            )
            console.print(f"[green]Updated script '{script.name}'[/green]")
            return
        except ValueError:
            pass

    try:
        script = db.create_script(
            name=name,
            content=content,
            description=description,
            tags=tags or "",
        )
        console.print(f"[green]Added script '{script.name}'[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--search", "-s", help="Search query")
def list_scripts(tag, search):
    """List all registered scripts."""
    db = get_db()
    scripts = db.list_scripts(tag=tag, search_query=search)

    if not scripts:
        console.print("[yellow]No scripts found[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Tags")

    for script in scripts:
        table.add_row(
            script.name,
            script.description or "-",
            script.tags or "-",
        )

    console.print(table)


@cli.command()
@click.argument("query")
def search(query):
    """Full-text search across scripts."""
    db = get_db()
    scripts = db.list_scripts(search_query=query)

    if not scripts:
        console.print(f"[yellow]No scripts found matching '{query}'[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Tags")

    for script in scripts:
        table.add_row(
            script.name,
            script.description or "-",
            script.tags or "-",
        )

    console.print(table)


@cli.command()
@click.argument("name")
@click.option("--var", "-v", multiple=True, help="Variables (key=value)")
@click.option("--all-vars", "-a", help="JSON string of variables")
def run(name, var, all_vars):
    """Execute a script with variable substitution."""
    db = get_db()
    script = db.get_script(name)

    if not script:
        console.print(f"[red]Script '{name}' not found[/red]")
        sys.exit(1)

    variables = {}
    if all_vars:
        try:
            variables = json.loads(all_vars)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON for --all-vars[/red]")
            sys.exit(1)

    if var:
        for v in var:
            if "=" in v:
                key, value = v.split("=", 1)
                variables[key] = value

    engine = TemplateEngine()
    missing = engine.get_missing_variables(script.content, variables)

    if missing:
        console.print(f"[yellow]Missing variables: {', '.join(missing)}[/yellow]")
        console.print("[dim]Pass variables with -v key=value or -a JSON[/dim]")
        sys.exit(1)

    runner = ScriptRunner()
    result = runner.execute(script.content, variables)

    if result.output:
        console.print(result.output)

    if result.error:
        console.print(f"[red]{result.error}[/red]")

    db.add_execution(
        script_id=script.id,
        script_name=script.name,
        variables_used=serialize_variables(variables),
        exit_code=result.exit_code,
        output=result.output,
        error=result.error,
    )

    sys.exit(result.exit_code)


@cli.command()
@click.option("--script-name", "-n", help="Filter by script name")
@click.option("--limit", "-l", default=50, help="Limit results")
def history(script_name, limit):
    """View execution history."""
    db = get_db()
    entries = db.get_history(script_name=script_name, limit=limit)

    if not entries:
        console.print("[yellow]No execution history[/yellow]")
        return

    table = Table(show_header=True)
    table.add_column("Script")
    table.add_column("Exit Code")
    table.add_column("Executed At")

    for entry in entries:
        table.add_row(
            entry.script_name,
            str(entry.exit_code or "-"),
            entry.executed_at.strftime("%Y-%m-%d %H:%M:%S") if entry.executed_at else "-",
        )

    console.print(table)


@cli.command()
@click.argument("name")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
def export(name, output):
    """Export script to file."""
    db = get_db()
    script = db.get_script(name)

    if not script:
        console.print(f"[red]Script '{name}' not found[/red]")
        sys.exit(1)

    if output:
        Path(output).write_text(script.content)
        console.print(f"[green]Exported to {output}[/green]")
    else:
        console.print(script.content)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--name", "-n", help="Name for the script")
@click.option("--description", "-d", help="Script description")
@click.option("--tags", "-t", help="Comma-separated tags")
@click.option("--update", "-u", is_flag=True, help="Update existing script")
def import_script(file_path, name, description, tags, update):
    """Import script from file."""
    file_path = Path(file_path)
    name = name or file_path.stem
    content = file_path.read_text()

    db = get_db()

    try:
        script = db.create_script(
            name=name,
            content=content,
            description=description,
            tags=tags or "",
        )
        console.print(f"[green]Imported script '{script.name}'[/green]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
