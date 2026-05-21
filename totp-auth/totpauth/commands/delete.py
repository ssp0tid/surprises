"""Delete account command."""

import sys
import click

from totpauth.storage.store import EncryptedStorage, get_password
from totpauth.exceptions import AccountNotFoundError


_storage = None


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


@click.command("delete")
@click.argument("id_or_issuer")
@click.option("-f", "--force", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_command(ctx, id_or_issuer, force):
    try:
        storage = ctx.obj.get("storage") or get_storage()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    try:
        account = storage.get_account(id_or_issuer)
    except AccountNotFoundError:
        click.echo(f"Error: Account '{id_or_issuer}' not found.", err=True)
        click.echo("Run 'totp-auth list' to see available accounts.")
        sys.exit(3)
    if not force:
        click.echo(f"Delete account: {account.issuer}:{account.account_name}?")
        if not click.confirm("Are you sure?"):
            click.echo("Cancelled.")
            return
    storage.remove_account(id_or_issuer)
    click.echo(f"Deleted account: {account.issuer}:{account.account_name}")
