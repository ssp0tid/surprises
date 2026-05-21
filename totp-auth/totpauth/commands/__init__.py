"""CLI commands."""

from totpauth.commands.add import add_command
from totpauth.commands.list import list_command
from totpauth.commands.generate import generate_command
from totpauth.commands.delete import delete_command

__all__ = [
    "add_command",
    "list_command",
    "generate_command",
    "delete_command",
]
