"""Add account command."""

import sys
import click

from totpauth.storage.store import EncryptedStorage, set_master_password, get_password
from totpauth.models.account import Account
from totpauth.core.qr import parse_qr_file, parse_otpauth_uri
from totpauth.exceptions import InvalidSecretError


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


@click.command("add")
@click.option("--manual", is_flag=True, help="Manual secret entry")
@click.option("--qr", type=click.Path(exists=True), help="QR code screenshot")
@click.option("--issuer", type=str, help="Service issuer")
@click.option("--account", type=str, help="Account name/email")
@click.option("--secret", type=str, help="Base32 secret")
@click.option("--totp", "otp_type", flag_value="totp", default=True, help="TOTP type")
@click.option("--hotp", "otp_type", flag_value="hotp", help="HOTP type")
@click.option(
    "--algorithm",
    type=click.Choice(["SHA1", "SHA256", "SHA512"]),
    default="SHA1",
    help="Algorithm",
)
@click.option("--digits", type=click.IntRange(6, 8), default=6, help="Digit count")
@click.option("--period", type=int, default=30, help="TOTP period")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@click.pass_context
def add_command(
    ctx, manual, qr, issuer, account, secret, otp_type, algorithm, digits, period, yes
):
    if qr and manual:
        click.echo("Error: Cannot use both --qr and --manual", err=True)
        sys.exit(2)
    if qr:
        _add_from_qr(ctx, qr)
    elif manual:
        _add_manual(
            ctx, issuer, account, secret, otp_type, algorithm, digits, period, yes
        )
    else:
        click.echo("Error: Use either --qr or --manual", err=True)
        sys.exit(2)


def _add_from_qr(ctx, qr_path: str):
    try:
        uri = parse_qr_file(qr_path)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
    try:
        data = parse_otpauth_uri(uri)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
    account = Account(
        issuer=data["issuer"],
        account_name=data["account_name"],
        secret=data["secret"],
        otp_type=data["otp_type"],
        algorithm=data["algorithm"],
        digits=data["digits"],
        period=data["period"],
        counter=data["counter"],
    )
    try:
        storage = ctx.obj.get("storage") or get_storage()
    except Exception:
        password = set_master_password()
        storage = init_storage(password)
    storage.add_account(account)
    click.echo(f"Added account: {account.issuer}:{account.account_name}")


def _add_manual(ctx, issuer, account, secret, otp_type, algorithm, digits, period, yes):
    if not issuer:
        issuer = click.prompt("Issuer (e.g., GitHub)")
    if not account:
        account = click.prompt("Account name/email")
    if not secret:
        secret = click.prompt("Base32 secret")
    if not _validate_secret(secret):
        raise InvalidSecretError(secret)
    account_obj = Account(
        issuer=issuer,
        account_name=account,
        secret=secret,
        otp_type=otp_type,
        algorithm=algorithm,
        digits=digits,
        period=period,
    )
    if not yes:
        click.echo(f"\nAccount: {account_obj.issuer}:{account_obj.account_name}")
        if not click.confirm("Add this account?"):
            click.echo("Cancelled.")
            return
    try:
        storage = ctx.obj.get("storage") or get_storage()
    except Exception:
        password = set_master_password()
        storage = init_storage(password)
    storage.add_account(account_obj)
    click.echo(f"Added account: {account_obj.issuer}:{account_obj.account_name}")


def _validate_secret(secret: str) -> bool:
    import base64

    try:
        base64.b32decode(secret.replace(" ", "").upper(), casefold=True)
        return True
    except Exception:
        return False
