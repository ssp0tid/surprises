"""Model management subcommand for Local LLM Chat."""

from __future__ import annotations

from pathlib import Path

import click
import rich.tables as tables

from local_llm_chat.cli.main import RichCommand
from local_llm_chat.models.registry import get_model_info, scan_models
from local_llm_chat.storage.config import Config
from local_llm_chat.utils.pretty import StatusIndicator


@click.group(cls=RichCommand, name="model")
@click.pass_context
def model_group(ctx: click.Context) -> None:
    """Manage available models."""
    pass


@model_group.command(name="list", cls=RichCommand)
@click.option(
    "--model-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to models directory. Default: from config.",
)
@click.pass_context
def list_models(ctx: click.Context, model_dir: Path | None) -> None:
    """List all available models in the models directory.

    Scans the models directory for GGUF model files and displays them
    in a table with name, quantization, size, and context info.
    """
    config: Config = ctx.obj["config"]

    if model_dir is None:
        model_dir = Path(config.model_dir)

    status = StatusIndicator()

    if not model_dir.exists():
        status.warning(f"Model directory does not exist: {model_dir}")
        click.echo("No models found.")
        return

    models = scan_models(str(model_dir))

    if not models:
        status.warning(f"No GGUF models found in directory: {model_dir}")
        click.echo("No models found.")
        return

    table = tables.Table(title=f"Available Models in {model_dir}", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=False)
    table.add_column("Quantization", style="magenta")
    table.add_column("Size", style="green", justify="right")
    table.add_column("Context", style="yellow", justify="right")

    current_name = config.current_model

    for model in models:
        context_str = f"{model.context_size // 1024}K" if model.context_size else "-"

        style = None
        if model.name == current_name or Path(model.path).name == current_name:
            style = "bold"
            current_match = model.name

        table.add_row(
            model.name,
            model.quantization,
            model.size,
            context_str,
            style=style,
        )

    console = status.console
    console.print(table)

    if current_match:
        status.info(f"Currently active: {current_match}")
    else:
        status.warning(f"Current model '{current_name}' not found in directory")


@model_group.command(name="info", cls=RichCommand)
@click.argument("model_name", required=False)
@click.option(
    "--model-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to models directory. Default: from config.",
)
@click.pass_context
def model_info(
    ctx: click.Context,
    model_name: str | None,
    model_dir: Path | None,
) -> None:
    """Show detailed information for a specific model.

    If MODEL_NAME is not provided, shows info for the currently
    active model from the config.
    """
    config: Config = ctx.obj["config"]
    status = StatusIndicator()

    if model_dir is None:
        model_dir = Path(config.model_dir)

    if not model_dir.exists():
        status.error(f"Model directory does not exist: {model_dir}")
        return

    # Find target model
    target_name = model_name if model_name else config.current_model
    models = scan_models(str(model_dir))

    if not models:
        status.error(f"No models found in directory: {model_dir}")
        return

    # Search for model by name or path
    model = None
    for m in models:
        if m.name == target_name or Path(m.path).name == target_name:
            model = m
            break

    if model is None:
        # Fall back to path search
        target_path = Path(target_name)
        if target_path.exists():
            try:
                model = get_model_info(str(target_path))
            except Exception as e:
                status.error(f"Failed to read model: {e}")
                return

    if model is None:
        status.error(f"Model not found: {target_name}")
        click.echo(f"Use 'model list' to see available models.")
        return

    # Display model info
    from rich.panel import Panel
    from rich.text import Text

    info_text = Text()
    info_text.append(f"Name: ", style="bold cyan")
    info_text.append(f"{model.name}\n")

    info_text.append(f"Path: ", style="bold cyan")
    info_text.append(f"{model.path}\n")

    info_text.append(f"Size: ", style="bold cyan")
    info_text.append(f"{model.size} ({model.size_bytes:,} bytes)\n")

    info_text.append(f"Quantization: ", style="bold cyan")
    info_text.append(f"{model.quantization}\n")

    info_text.append(f"context Size: ", style="bold cyan")
    if model.context_size:
        info_text.append(f"{model.context_size:,} ({model.context_size // 1024}K)")
    else:
        info_text.append(f"Unknown")

    is_active = model.name == config.current_model or Path(model.path).name == config.current_model

    panel = Panel(
        info_text,
        title=f"Model Info: {model.name}",
        border_style="cyan",
        subtitle="Active" if is_active else None,
    )

    status.console.print(panel)


@model_group.command(name="switch", cls=RichCommand)
@click.argument("model_name")
@click.option(
    "--model-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to models directory. Default: from config.",
)
@click.option(
    "--config-path",
    "-c",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to config file. Default: config.toml in current directory.",
)
@click.pass_context
def switch_model(
    ctx: click.Context,
    model_name: str,
    model_dir: Path | None,
    config_path: Path | None,
) -> None:
    """Switch to a different model.

    Updates the current_model setting in the config file.
    """
    config: Config = ctx.obj["config"]
    status = StatusIndicator()

    if model_dir is None:
        model_dir = Path(config.model_dir)

    if not model_dir.exists():
        status.error(f"Model directory does not exist: {model_dir}")
        return

    # Verify model exists
    models = scan_models(str(model_dir))

    if not models:
        status.error(f"No models found in directory: {model_dir}")
        return

    model = None
    for m in models:
        if m.name == model_name or Path(m.path).name == model_name:
            model = m
            break

    if model is None:
        status.error(f"Model not found: {model_name}")
        click.echo(f"Use 'model list' to see available models.")
        return

    # Update config
    old_model = config.current_model
    config.current_model = model.name

    # Save config
    if config_path is None:
        config_path = Path("config.toml")

    try:
        from local_llm_chat.storage.config import save_config

        save_config(config, str(config_path))
        status.success(f"Switched from '{old_model}' to '{model.name}'")
    except Exception as e:
        status.error(f"Failed to save config: {e}")
        raise click.Abort() from e
