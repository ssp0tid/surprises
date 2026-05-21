"""Chat subcommand for Local LLM Chat CLI."""

import sys
from pathlib import Path

import click
import rich_click
from click import Context

from local_llm_chat.core.renderer import Renderer
from local_llm_chat.storage import (
    Config,
    Conversation,
    Message,
    load_conversation,
    new_conversation,
    save_conversation,
)


class RichCommand(rich_click.RichCommand):
    """Rich-enabled command for better help output."""


@click.group(cls=RichCommand)
@click.pass_context
def chat(ctx: Context) -> None:
    """Chat with a local LLM model."""
    pass


def _verify_model_exists(model: str, model_dir: str) -> tuple[bool, str]:
    """Verify that the model file exists.

    Args:
        model: Model filename.
        model_dir: Directory containing model files.

    Returns:
        Tuple of (exists, error_message). If exists is False, error_message contains details.
    """
    model_path = Path(model_dir) / model

    if not model_path.exists():
        return False, f"Model file not found: {model_path}"

    if not model_path.is_file():
        return False, f"Model path is not a file: {model_path}"

    return True, ""


def _print_welcome(model: str, conversation: Conversation | None) -> None:
    """Print welcome message showing model being used."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    console = Console()

    title = "Welcome to Local LLM Chat"
    conv_info = f"Conversation: {conversation.id}" if conversation else "New conversation"

    content = Text()
    content.append(f"Model: {model}\n", style="bold green")
    content.append(conv_info, style="cyan")
    content.append("\n\nType /quit to exit, Ctrl+C to interrupt", style="dim")

    console.print(Panel(content, title=title, border_style="blue"))


def _get_user_input() -> str | None:
    """Get input from user with prompt.

    Returns:
        User input string, or None if user wants to quit.
    """
    try:
        user_input = input("\n[You] ").strip()
        return user_input
    except EOFError:
        return None
    except KeyboardInterrupt:
        return None


def _simulate_response(user_input: str) -> str:
    """Simulate a response from the LLM.

    In a real implementation, this would call the LLM inference engine.

    Args:
        user_input: User's input message.

    Returns:
        Simulated response from the LLM.
    """
    return f"This is a simulated response to: {user_input}\n\n(In production, this would call your local LLM.)"


@chat.command("start")
@click.option(
    "--model",
    "-m",
    "model",
    type=str,
    default=None,
    help="Model filename to use (overrides config).",
)
@click.option(
    "--system",
    "-s",
    "system_prompt",
    type=str,
    default=None,
    help="System prompt to use (overrides config).",
)
@click.option(
    "--conversation",
    "-c",
    "conversation_id",
    type=str,
    default=None,
    help="Conversation ID to resume.",
)
@click.option(
    "--stream/--no-stream",
    "stream",
    default=None,
    help="Enable or disable streaming responses (overrides config).",
)
@click.pass_obj
def start(
    config: Config,
    model: str | None,
    system_prompt: str | None,
    conversation_id: str | None,
    stream: bool | None,
) -> None:
    """Start an interactive chat session."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    effective_model = model or config.current_model
    effective_system = system_prompt or config.system_prompt

    exists, error_msg = _verify_model_exists(effective_model, config.model_dir)
    if not exists:
        console = Console()
        content = Text(error_msg, style="bold red")
        console.print(Panel(content, title="Error", border_style="red"))
        sys.exit(1)

    conv: Conversation | None = None

    if conversation_id:
        try:
            conv = load_conversation(conversation_id, config.save_dir)
            conv.messages.append(Message(role="system", content="Conversation resumed."))
        except FileNotFoundError:
            console = Console()
            content = Text(
                f"Conversation not found: {conversation_id}\nStarting new conversation.",
                style="bold yellow",
            )
            console.print(Panel(content, title="Warning", border_style="yellow"))
            conv = new_conversation(effective_model, effective_system)
        except OSError:
            console = Console()
            content = Text(
                f"Failed to load conversation: {conversation_id}\nStarting new conversation.",
                style="bold yellow",
            )
            console.print(Panel(content, title="Warning", border_style="yellow"))
            conv = new_conversation(effective_model, effective_system)
    else:
        conv = new_conversation(effective_model, effective_system)

    _print_welcome(effective_model, conv)

    renderer = Renderer()
    console = Console()

    while True:
        user_input = _get_user_input()

        if user_input is None or user_input.lower() == "/quit":
            console.print("\n[bold]Goodbye![/bold]")
            break

        if not user_input:
            continue

        conv.messages.append(Message(role="user", content=user_input))

        response = _simulate_response(user_input)

        conv.messages.append(Message(role="assistant", content=response))

        console.print()
        renderer.render(response)
        console.print()

        if config.auto_save:
            try:
                save_conversation(conv, config.save_dir)
            except OSError as e:
                console.print(f"[dim]Auto-save failed: {e}[/dim]")
