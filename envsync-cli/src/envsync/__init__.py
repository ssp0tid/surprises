"""envsync-cli - Environment variable sync manager with AES-256-GCM encryption."""

__version__ = "0.1.0"
__author__ = "envsync"
__license__ = "MIT"

from envsync.core.encryption import decrypt_data, derive_key, encrypt_data
from envsync.core.interpolator import interpolate
from envsync.core.vault import Vault, VaultManager

__all__ = [
    "__version__",
    "derive_key",
    "encrypt_data",
    "decrypt_data",
    "Vault",
    "VaultManager",
    "interpolate",
]
