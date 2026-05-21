"""Encrypted storage using AES-256-GCM."""

import os
import json
from pathlib import Path
from typing import List, Optional

from totpauth.core.crypto import CryptoManager
from totpauth.models.account import Account
from totpauth.exceptions import (
    AccountNotFoundError,
    DuplicateAccountError,
    CorruptedDataError,
)


STORAGE_VERSION = 1
DEFAULT_PATH = Path.home() / ".local" / "share" / "totp-auth" / "accounts.enc"


class EncryptedStorage:
    def __init__(self, password: str, path: Path = None):
        self.path = path or DEFAULT_STORAGE_PATH()
        self._ensure_directory()
        self.crypto = None
        self._load_or_initialize(password)

    def _ensure_directory(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load_or_initialize(self, password: str):
        if not self.path.exists():
            self.crypto = CryptoManager(password)
            self._salt = self.crypto.salt
            self.accounts = []
            return
        try:
            data = self.path.read_bytes()
            self._salt = data[:32]
            nonce = data[32:44]
            ciphertext = data[44:]
            self.crypto = CryptoManager(password, self._salt)
            try:
                plaintext = self.crypto.decrypt(ciphertext, nonce)
                store = json.loads(plaintext.decode("utf-8"))
                self.accounts = [
                    Account.from_dict(a) for a in store.get("accounts", [])
                ]
            except Exception:
                raise CorruptedDataError()
        except CorruptedDataError:
            raise
        except Exception:
            self.crypto = CryptoManager(password)
            self._salt = self.crypto.salt
            self.accounts = []

    def save(self):
        store = {
            "version": STORAGE_VERSION,
            "accounts": [a.to_dict() for a in self.accounts],
        }
        plaintext = json.dumps(store, ensure_ascii=False).encode("utf-8")
        ciphertext, nonce = self.crypto.encrypt(plaintext)
        data = self._salt + nonce + ciphertext
        self.path.write_bytes(data)

    def add_account(self, account: Account) -> Account:
        for existing in self.accounts:
            if existing.id == account.id:
                raise DuplicateAccountError(account.issuer, account.account_name)
        self.accounts.append(account)
        self.save()
        return account

    def remove_account(self, identifier: str) -> Account:
        account = self._find_account(identifier)
        if account is None:
            raise AccountNotFoundError(identifier)
        self.accounts.remove(account)
        self.save()
        return account

    def get_account(self, identifier: str) -> Account:
        account = self._find_account(identifier)
        if account is None:
            raise AccountNotFoundError(identifier)
        return account

    def list_accounts(self) -> List[Account]:
        return list(self.accounts)

    def _find_account(self, identifier: str) -> Optional[Account]:
        identifier_lower = identifier.lower()
        for account in self.accounts:
            if account.id.lower() == identifier_lower:
                return account
            if account.issuer.lower() == identifier_lower:
                return account
            if account.issuer.lower().startswith(identifier_lower):
                return account
        return None


def DEFAULT_STORAGE_PATH() -> Path:
    if "XDG_DATA_HOME" in os.environ:
        return Path(os.environ["XDG_DATA_HOME"]) / "totp-auth" / "accounts.enc"
    return DEFAULT_PATH


def get_password(prompt: str = "Enter master password: ") -> str:
    import getpass

    return getpass.getpass(prompt)


def set_master_password() -> str:
    import getpass

    while True:
        password = getpass.getpass("Set master password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            continue
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.")
            continue
        return password
