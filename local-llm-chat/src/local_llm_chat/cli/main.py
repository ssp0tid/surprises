"""Main CLI group for Local LLM Chat."""

import click
import rich_click
from click import Context

from local_llm_chat import __version__
from local_llm_chat.storage.config import Config, load_config


class RichCommand(rich_click.RichCommand):
    """Rich-enabled command for better help output."""


@click.group(cls=RichCommand)
@click.version_option(version=__version__)
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=False),
    default="config.toml",
    help="Path to configuration file.",
)
@click.pass_context
def main(ctx: Context, config_path: str) -> None:
    """Local LLM Chat - CLI tool to chat with local LLMs."""
    config: Config = load_config(config_path)

    ctx.ensure_object(dict)
    ctx.obj["config"] = config
