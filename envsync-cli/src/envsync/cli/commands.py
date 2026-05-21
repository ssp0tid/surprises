"""CLI command implementations."""

import sys

from rich.console import Console
from rich.table import Table

from envsync.core.vault import VaultManager

console = Console()
_password: str | None = None


def _get_password(password: str | None = None) -> str:
    global _password
    if password:
        _password = password
    if _password is None:
        console.print("[red]Error: Password required. Use --password option.[/red]")
        sys.exit(1)
    return _password


def init_vault(password: str | None, group: str | None) -> None:
    if not password:
        console.print("[red]Error: Password required. Use --password option.[/red]")
        sys.exit(1)

    global _password
    _password = password

    vm = VaultManager(password=password)
    if group:
        vm.create_group(group)
    console.print("[green]Vault initialized successfully![/green]")
    if group:
        console.print(f"[green]Created group: {group}[/green]")


def add_variable(variable: str | None, project: str | None, password: str | None) -> None:
    vm = VaultManager(password=_get_password(password))
    if not vm.load():
        console.print("[red]Error: Failed to load vault. Check password.[/red]")
        sys.exit(1)

    if not variable:
        console.print("[red]Error: Variable required. Use VAR=value format.[/red]")
        sys.exit(1)
    if "=" not in variable:
        console.print("[red]Error: Variable must be in VAR=value format[/red]")
        sys.exit(1)
    key, value = variable.split("=", 1)

    vm.add_variable(key, value, project=project)
    console.print(f"[green]Added {key}[/green]")


def remove_variable(
    variable: str, project: str | None, is_global: bool, password: str | None
) -> None:
    vm = VaultManager(password=_get_password(password))
    if not vm.load():
        console.print("[red]Error: Failed to load vault. Check password.[/red]")
        sys.exit(1)

    if vm.remove_variable(variable, project=None if not is_global else project):
        console.print(f"[green]Removed {variable}[/green]")
    else:
        console.print(f"[red]Variable {variable} not found[/red]")


def list_variables(project: str | None, decrypted: bool, password: str | None) -> None:
    vm = VaultManager(password=_get_password(password))
    if not vm.load():
        console.print("[red]Error: Failed to load vault. Check password.[/red]")
        sys.exit(1)

    variables = vm.list_variables(project)

    if not variables:
        console.print("[yellow]No variables found[/yellow]")
        return

    table = Table(title="Environment Variables")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    for key, value in variables.items():
        table.add_row(key, value if decrypted else "*" * len(value))

    console.print(table)


def import_env(path: str, project: str | None, password: str | None) -> None:
    vm = VaultManager(password=_get_password(password))
    if not vm.load():
        console.print("[red]Error: Failed to load vault. Check password.[/red]")
        sys.exit(1)

    count = vm.import_from_file(path, project=project)
    console.print(f"[green]Imported {count} variables from {path}[/green]")


def export_env(project: str | None, output: str | None, password: str | None) -> None:
    if not output:
        output = ".env"

    vm = VaultManager(password=_get_password(password))
    if not vm.load():
        console.print("[red]Error: Failed to load vault. Check password.[/red]")
        sys.exit(1)

    count = vm.export_to_file(output, project=project)
    console.print(f"[green]Exported {count} variables to {output}[/green]")


def sync_group(group: str | None, password: str | None) -> None:
    vm = VaultManager(password=_get_password(password))
    if not vm.load():
        console.print("[red]Error: Failed to load vault. Check password.[/red]")
        sys.exit(1)

    if not group:
        groups = vm.list_groups()
        if not groups:
            console.print("[yellow]No groups found[/yellow]")
            return
        group = list(groups.keys())[0]

    results = vm.sync_group(group)
    if not results:
        console.print("[yellow]No projects synced[/yellow]")
        return

    for proj, count in results.items():
        console.print(f"[green]Synced {count} vars to {proj}[/green]")


def manage_group(action: str, name: str | None, project: str | None, password: str | None) -> None:
    vm = VaultManager(password=_get_password(password))
    if not vm.load():
        console.print("[red]Error: Failed to load vault. Check password.[/red]")
        sys.exit(1)

    if action == "list":
        groups = vm.list_groups()
        if not groups:
            console.print("[yellow]No groups found[/yellow]")
            return
        table = Table(title="Groups")
        table.add_column("Name", style="cyan")
        table.add_column("Projects", style="green")
        for gname, grp in groups.items():
            table.add_row(gname, ", ".join(grp.projects) or "-")
        console.print(table)
        return

    if not name:
        console.print("[red]Error: Group name required[/red]")
        sys.exit(1)

    if action == "create":
        vm.create_group(name)
        console.print(f"[green]Created group: {name}[/green]")
    elif action == "delete":
        if vm.delete_group(name):
            console.print(f"[green]Deleted group: {name}[/green]")
        else:
            console.print(f"[red]Group {name} not found[/red]")
    elif action == "add":
        if not project:
            console.print("[red]Error: --project required[/red]")
            sys.exit(1)
        if vm.add_project_to_group(project, name):
            console.print(f"[green]Added {project} to {name}[/green]")
        else:
            console.print("[red]Failed to add project[/red]")
    elif action == "remove":
        if vm.remove_project_from_group(project or ""):
            console.print("[green]Removed from group[/green]")
        else:
            console.print("[red]Failed to remove from group[/red]")
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        sys.exit(1)


def start_dashboard(port: int) -> None:
    try:
        from envsync.cli import dashboard as db_module

        db_module.run_dashboard(port)
    except ImportError:
        console.print("[red]Dashboard dependencies not installed[/red]")
        console.print("[yellow]Install with: pip install envsync-cli[dashboard][/yellow]")
        sys.exit(1)
