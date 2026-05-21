"""Config management CLI subcommand."""

from dataclasses import fields

import click
import rich_click
from rich.console import Console
from rich.table import Table

from local_llm_chat.storage.config import Config


class RichCommand(rich_click.RichCommand):
    """Rich-enabled command for better help output."""


console = Console()


@click.group(cls=RichCommand)
@click.pass_obj
def config_group(obj: dict) -> None:
    """Manage configuration settings."""
    pass


@config_group.command(name="show")
@click.pass_obj
def show_config(obj: dict) -> None:
    """Display current configuration."""
    cfg: Config = obj["config"]

    table = Table(title="Current Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for f in fields(Config):
        key = f.name
        value = getattr(cfg, key)
        table.add_row(key, str(value))

    console.print(table)


@config_group.command(name="set")
@click.argument("key")
@click.argument("value")
@click.pass_obj
def set_config(obj: dict, key: str, value: str) -> None:
    """Update a configuration value.

    KEY is the configuration key to update.
    VALUE is the new value to set.
    """
    cfg: Config = obj["config"]

    valid_keys = {f.name for f in fields(Config)}
    if key not in valid_keys:
        raise click.ClickException(
            f"Invalid key '{key}'. Valid keys are: {', '.join(sorted(valid_keys))}"
        )

    field = next(f for f in fields(Config) if f.name == key)
    field_type = field.type

    try:
        if field_type is bool:
            parsed_value = value.lower() in ("true", "1", "yes")
        elif field_type is int:
            parsed_value = int(value)
        elif field_type is float:
            parsed_value = float(value)
        else:
            parsed_value = value
    except ValueError as e:
        raise click.ClickException(
            f"Invalid value '{value}' for key '{key}'. Expected {field_type.__name__}."
        ) from e

    current_values = {f.name: getattr(cfg, f.name) for f in fields(Config)}
    current_values[key] = parsed_value

    try:
        new_config = Config(**current_values)
    except (TypeError, ValueError) as e:
        raise click.ClickException(f"Validation error: {e}") from e

    obj["config"] = new_config

    console.print(f"[green]Updated[/green] {key} = [cyan]{parsed_value}[/cyan]")
