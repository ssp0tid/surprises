"""List accounts command."""

import sys
import json
import click

from totpauth.storage.store import EncryptedStorage, get_password
from totpauth.core.otp import generate_totp, generate_hotp


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


@click.command("list")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["table", "json", "plain"]),
    default="table",
    help="Output format",
)
@click.option("-q", "--quiet", is_flag=True, help="Show only codes")
@click.pass_context
def list_command(ctx, format, quiet):
    try:
        storage = ctx.obj.get("storage") or get_storage()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    accounts = storage.list_accounts()
    if not accounts:
        click.echo("No accounts found.")
        return
    if format == "json":
        _list_json(accounts, quiet)
    elif format == "plain":
        _list_plain(accounts, quiet)
    else:
        _list_table(accounts, quiet)


def _list_json(accounts, quiet):
    data = []
    for acc in accounts:
        code = _generate_code(acc)
        if quiet:
            data.append(code)
        else:
            data.append(
                {
                    "issuer": acc.issuer,
                    "account": acc.account_name,
                    "code": code,
                }
            )
    click.echo(json.dumps(data, ensure_ascii=False))


def _list_plain(accounts, quiet):
    for acc in accounts:
        code = _generate_code(acc)
        if quiet:
            click.echo(code)
        else:
            click.echo(f"{acc.issuer}:{acc.account_name}:{code}")


def _list_table(accounts, quiet):
    lines = []
    max_issuer = max(len(acc.issuer) for acc in accounts)
    max_account = max(len(acc.account_name) for acc in accounts)
    lines.append(
        "┌"
        + "─" * (max_issuer + 2)
        + "┬"
        + "─" * (max_account + 2)
        + "┬"
        + "─" * 8
        + "┐"
    )
    lines.append(
        "│"
        + " Issuer".ljust(max_issuer + 1)
        + "│"
        + " Account".ljust(max_account + 1)
        + "│"
        + " Code".ljust(7)
        + "│"
    )
    lines.append(
        "├"
        + "─" * (max_issuer + 2)
        + "┼"
        + "─" * (max_account + 2)
        + "┼"
        + "─" * 8
        + "┤"
    )
    for acc in accounts:
        code = _generate_code(acc)
        lines.append(
            "│"
            + (" " + acc.issuer).ljust(max_issuer + 2)
            + "│"
            + (" " + acc.account_name).ljust(max_account + 2)
            + "│"
            + (" " + code).ljust(8)
            + "│"
        )
    lines.append(
        "└"
        + "─" * (max_issuer + 2)
        + "┴"
        + "─" * (max_account + 2)
        + "┴"
        + "─" * 8
        + "┘"
    )
    for line in lines:
        click.echo(line)


def _generate_code(account):
    if account.otp_type == "totp":
        return generate_totp(
            account.secret,
            digits=account.digits,
            period=account.period,
            algorithm=account.algorithm,
        )
    else:
        return generate_hotp(
            account.secret,
            counter=account.counter,
            digits=account.digits,
            algorithm=account.algorithm,
        )
