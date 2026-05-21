import click
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from local_llm_chat.cli.main import RichCommand
from local_llm_chat.storage import conversation


console = Console()


@click.group(cls=RichCommand, name="history")
@click.pass_context
def history(ctx: click.Context) -> None:
    """Manage saved conversations."""
    pass


@history.command(name="list")
@click.pass_context
def list_conversations(ctx: click.Context) -> None:
    """List all saved conversations."""
    config = ctx.obj["config"]
    save_dir = config.save_dir

    conversations_list = conversation.list_conversations(save_dir)

    if not conversations_list:
        console.print("[dim]No saved conversations found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Created", style="yellow")
    table.add_column("Updated", style="yellow")

    for conv in conversations_list:
        table.add_row(
            conv.id,
            conv.model,
            conv.created_at[:19].replace("T", " "),
            conv.updated_at[:19].replace("T", " "),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(conversations_list)} conversation(s)[/dim]")


@history.command(name="load")
@click.argument("conversation_id")
@click.pass_context
def load_conversation_cmd(ctx: click.Context, conversation_id: str) -> None:
    """Load a conversation by ID."""
    config = ctx.obj["config"]
    save_dir = config.save_dir

    try:
        conv = conversation.load_conversation(conversation_id, save_dir)
    except FileNotFoundError:
        console.print(f"[red]Conversation not found: {conversation_id}[/red]")
        raise click.Abort() from None

    console.print(f"[green]Loaded conversation:[/green] {conv.id}")
    console.print(f"[dim]Model: {conv.model}[/dim]")
    console.print(f"[dim]System prompt: {conv.system_prompt}[/dim]")
    console.print(f"[dim]Messages: {len(conv.messages)}[/dim]")

    for msg in conv.messages:
        console.print(f"\n[bold]{msg.role}:[/bold]")
        console.print(msg.content)


@history.command(name="delete")
@click.argument("conversation_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_conversation_cmd(ctx: click.Context, conversation_id: str, force: bool) -> None:
    """Delete a conversation by ID."""
    config = ctx.obj["config"]
    save_dir = config.save_dir

    try:
        conversation.load_conversation(conversation_id, save_dir)
    except FileNotFoundError:
        console.print(f"[red]Conversation not found: {conversation_id}[/red]")
        raise click.Abort() from None

    if not force:
        console.print(f"[yellow]Delete conversation '{conversation_id}'?[/yellow]")
        if not Confirm.ask("This action cannot be undone.", default=False):
            console.print("[dim]Cancelled.[/dim]")
            return

    conversation.delete_conversation(conversation_id, save_dir)
    console.print(f"[green]Deleted conversation:[/green] {conversation_id}")
