"""totp-auth - CLI TOTP/HOTP Authenticator with encrypted storage."""

__version__ = "0.1.0"
__author__ = "Developer"
__license__ = "MIT"

from totpauth.models.account import Account
from totpauth.exceptions import (
    TotpAuthError,
    AccountNotFoundError,
    DuplicateAccountError,
    InvalidSecretError,
    InvalidQRCodeError,
    QRDecodeError,
    InvalidOtpAuthURLError,
    EncryptionError,
    InvalidPasswordError,
    CorruptedDataError,
    ClipboardError,
    CLIError,
    InvalidArgumentError,
    MissingArgumentError,
)

__all__ = [
    "__version__",
    "Account",
    "TotpAuthError",
    "AccountNotFoundError",
    "DuplicateAccountError",
    "InvalidSecretError",
    "InvalidQRCodeError",
    "QRDecodeError",
    "InvalidOtpAuthURLError",
    "EncryptionError",
    "InvalidPasswordError",
    "CorruptedDataError",
    "ClipboardError",
    "CLIError",
    "InvalidArgumentError",
    "MissingArgumentError",
]
