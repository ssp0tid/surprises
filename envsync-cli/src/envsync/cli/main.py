"""Main CLI entry point."""

import click
from rich.console import Console

from envsync.cli import commands

console = Console()


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx):
    """envsync - Environment variable sync manager with AES-256-GCM encryption."""
    ctx.ensure_object(dict)


@main.command()
@click.option("--password", help="Master password for encryption")
@click.option("--group", "-g", help="Initial group to create")
def init(password, group):
    """Initialize a new encrypted vault."""
    commands.init_vault(password, group)


@main.command(name="add")
@click.argument("variable", required=False)
@click.option("--project", help="Project name")
@click.option("--password", help="Master password for encryption")
def add_cmd(variable, project, password):
    """Add a variable (VAR=value format)."""
    commands.add_variable(variable, project, password)


@main.command()
@click.argument("variable")
@click.option("--project", help="Project name")
@click.option("--global", "is_global", is_flag=True, help="Remove from global vars")
@click.option("--password", help="Master password for encryption")
def remove(variable, project, is_global, password):
    """Remove a variable."""
    commands.remove_variable(variable, project, is_global, password)


@main.command()
@click.option("--project", help="Filter by project")
@click.option("--decrypted", "-d", is_flag=True, help="Show decrypted values")
@click.option("--password", help="Master password for encryption")
def list(project, decrypted, password):
    """List all variables."""
    commands.list_variables(project, decrypted, password)


@main.command(name="import")
@click.argument("path", type=click.Path(exists=True))
@click.option("--project", help="Project to import to")
@click.option("--password", help="Master password for encryption")
def import_cmd(path, project, password):
    """Import variables from a .env file."""
    commands.import_env(path, project, password)


@main.command()
@click.option("--project", help="Project to export")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--password", help="Master password for encryption")
def export(project, output, password):
    """Export variables to a .env file."""
    commands.export_env(project, output, password)


@main.command()
@click.argument("group", required=False)
@click.option("--password", help="Master password for encryption")
def sync(group, password):
    """Sync variables to projects in a group."""
    commands.sync_group(group, password)


@main.command()
@click.argument("action")
@click.argument("name", required=False)
@click.option("--project", help="Project name")
@click.option("--password", help="Master password for encryption")
def group(action, name, project, password):
    """Manage groups (create, delete, add, remove, list)."""
    commands.manage_group(action, name, project, password)


@main.command()
@click.option("--port", "-p", default=3000, help="Dashboard port")
def dashboard(port):
    """Start the web dashboard."""
    commands.start_dashboard(port)


if __name__ == "__main__":
    main()
