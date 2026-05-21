"""CLI entry point."""

import sys
from typing import Optional

import click

from totpauth import __version__
from totpauth.commands.add import add_command
from totpauth.commands.list import list_command
from totpauth.commands.generate import generate_command
from totpauth.commands.delete import delete_command
from totpauth.exceptions import TotpAuthError
from totpauth.storage.store import EncryptedStorage, set_master_password, get_password


_storage = None


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option("-c", "--config", type=click.Path(), help="Config file path")
@click.pass_context
def cli(ctx, verbose, config):
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config
    try:
        ctx.obj["storage"] = get_storage()
    except FileNotFoundError:
        click.echo("First run: set your master password")
        password = set_master_password()
        ctx.obj["storage"] = init_storage(password)
    except TotpAuthError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


cli.add_command(add_command)
cli.add_command(list_command)
cli.add_command(generate_command)
cli.add_command(delete_command)


@cli.command("version")
def version():
    click.echo(f"totp-auth {__version__}")


def _init_storage():
    global _storage
    try:
        password = get_password()
        _storage = EncryptedStorage(password)
    except FileNotFoundError:
        click.echo("First run: set your master password")
        password = set_master_password()
        _storage = EncryptedStorage(password)
    except Exception as e:
        click.echo(f"Error initializing storage: {e}", err=True)
        raise
    return _storage


def get_storage() -> EncryptedStorage:
    global _storage
    if _storage is not None:
        return _storage
    password = get_password()
    _storage = EncryptedStorage(password)
    return _storage


def init_storage(password: str) -> EncryptedStorage:
    global _storage
    _storage = EncryptedStorage(password)
    return _storage


def get_storage_from_context(ctx: click.Context) -> Optional[EncryptedStorage]:
    return ctx.obj.get("storage") if ctx.obj else None


def set_storage_in_context(ctx: click.Context, storage: EncryptedStorage):
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["storage"] = storage


def main():
    try:
        cli(obj={})
    except TotpAuthError as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(e.exit_code)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
