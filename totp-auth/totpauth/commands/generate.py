"""Generate code command."""

import sys
import time
import pyperclip
import click

from totpauth.storage.store import EncryptedStorage, get_password
from totpauth.core.otp import generate_totp, generate_hotp
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


@click.command("generate")
@click.argument("id_or_issuer", required=False)
@click.option("-c", "--clipboard", is_flag=True, help="Copy to clipboard")
@click.option("-q", "--quiet", is_flag=True, help="Print code only")
@click.option("-w", "--watch", is_flag=True, help="Watch mode (auto-refresh)")
@click.pass_context
def generate_command(ctx, id_or_issuer, clipboard, quiet, watch):
    try:
        storage = ctx.obj.get("storage") or get_storage()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    if not id_or_issuer:
        accounts = storage.list_accounts()
        if not accounts:
            click.echo("No accounts found. Add one first.", err=True)
            sys.exit(1)
        if len(accounts) == 1:
            account = accounts[0]
        else:
            click.echo("Available accounts:")
            for i, acc in enumerate(accounts):
                click.echo(f"  {i + 1}. {acc.issuer}:{acc.account_name}")
            choice = click.prompt("Select account (number)", type=int)
            if choice < 1 or choice > len(accounts):
                click.echo("Invalid selection.", err=True)
                sys.exit(1)
            account = accounts[choice - 1]
    else:
        try:
            account = storage.get_account(id_or_issuer)
        except AccountNotFoundError:
            click.echo(f"Error: Account '{id_or_issuer}' not found.", err=True)
            click.echo("Run 'totp-auth list' to see available accounts.")
            sys.exit(3)
    if watch:
        _watch_mode(account, clipboard, quiet)
    else:
        _generate_once(account, clipboard, quiet)


def _generate_once(account, clipboard, quiet):
    if account.otp_type == "totp":
        code = generate_totp(
            account.secret,
            digits=account.digits,
            period=account.period,
            algorithm=account.algorithm,
        )
    else:
        code = generate_hotp(
            account.secret,
            counter=account.counter,
            digits=account.digits,
            algorithm=account.algorithm,
        )
    if clipboard:
        try:
            pyperclip.copy(code)
            if not quiet:
                click.echo(f"Copied to clipboard: {code}")
            else:
                click.echo(code)
        except Exception as e:
            click.echo(f"Error: Could not copy to clipboard: {e}", err=True)
            sys.exit(1)
    else:
        if not quiet:
            click.echo(f"{account.issuer}:{account.account_name}: {code}")
        else:
            click.echo(code)


def _watch_mode(account, clipboard, quiet):
    period = account.period
    while True:
        if account.otp_type == "totp":
            code = generate_totp(
                account.secret,
                digits=account.digits,
                period=account.period,
                algorithm=account.algorithm,
            )
        else:
            code = generate_hotp(
                account.secret,
                counter=account.counter,
                digits=account.digits,
                algorithm=account.algorithm,
            )
        if clipboard:
            try:
                pyperclip.copy(code)
            except Exception as e:
                click.echo(f"Error: Could not copy to clipboard: {e}", err=True)
        if not quiet:
            click.echo(f"\r{account.issuer}:{account.account_name}: {code} ", err=False)
        else:
            click.echo(f"\r{code} ", err=False)
        click.echo(f"({period}s)", err=False)
        time.sleep(period)
