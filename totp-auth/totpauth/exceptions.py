"""Custom exception hierarchy for totp-auth."""


class TotpAuthError(Exception):
    """Base exception for all totp-auth errors."""

    exit_code: int = 1

    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


# Account-related errors
class AccountNotFoundError(TotpAuthError):
    """Raised when an account cannot be found."""

    exit_code = 3

    def __init__(self, identifier: str):
        self.identifier = identifier
        message = f"Account '{identifier}' not found. Run 'totp-auth list' to see available accounts."
        super().__init__(message)


class DuplicateAccountError(TotpAuthError):
    """Raised when trying to add a duplicate account."""

    exit_code = 1

    def __init__(self, issuer: str, account_name: str):
        self.issuer = issuer
        self.account_name = account_name
        message = f"Account '{issuer}:{account_name}' already exists."
        super().__init__(message)


class InvalidSecretError(TotpAuthError):
    """Raised when a secret is invalid or malformed."""

    exit_code = 2

    def __init__(self, secret: str):
        self.secret = secret
        message = (
            f"Invalid secret '{secret}'. Secrets must be Base32-encoded (A-Z, 2-7)."
        )
        super().__init__(message)


# QR code errors
class InvalidQRCodeError(TotpAuthError):
    """Base exception for QR code related errors."""

    exit_code = 2


class QRDecodeError(InvalidQRCodeError):
    """Raised when QR code decoding fails."""

    def __init__(self, path: str = None):
        self.path = path
        if path:
            message = f"Failed to decode QR code from '{path}'. Ensure the image is clear and not damaged."
        else:
            message = "Failed to decode QR code from image."
        super().__init__(message)


class InvalidOtpAuthURLError(InvalidQRCodeError):
    """Raised when otpauth:// URL is invalid."""

    def __init__(self, url: str):
        self.url = url
        message = f"Invalid otpauth:// URL: {url}. Expected format: otpauth://totp/Issuer:account?secret=..."
        super().__init__(message)


# Encryption errors
class EncryptionError(TotpAuthError):
    """Base exception for encryption related errors."""

    exit_code = 4


class InvalidPasswordError(EncryptionError):
    """Raised when master password is invalid."""

    def __init__(self):
        super().__init__("Invalid master password. Please try again.")


class CorruptedDataError(EncryptionError):
    """Raised when encrypted data is corrupted."""

    def __init__(self):
        super().__init__("Data appears to be corrupted. Unable to decrypt.")


# Clipboard errors
class ClipboardError(TotpAuthError):
    """Raised when clipboard operations fail."""

    exit_code = 1

    def __init__(self, message: str = "Failed to access clipboard."):
        super().__init__(message)


# CLI errors
class CLIError(TotpAuthError):
    """Base exception for CLI-related errors."""

    exit_code = 2


class InvalidArgumentError(CLIError):
    """Raised when CLI argument is invalid."""

    def __init__(self, argument: str, reason: str):
        self.argument = argument
        self.reason = reason
        message = f"Invalid argument '{argument}': {reason}"
        super().__init__(message)


class MissingArgumentError(CLIError):
    """Raised when CLI argument is missing."""

    def __init__(self, argument: str, required_by: str = None):
        self.argument = argument
        self.required_by = required_by
        if required_by:
            message = (
                f"Missing required argument: {argument} (required by {required_by})"
            )
        else:
            message = f"Missing required argument: {argument}"
        super().__init__(message)
