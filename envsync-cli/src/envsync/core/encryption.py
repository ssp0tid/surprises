"""AES-256-GCM encryption with PBKDF2 key derivation."""

import os
from dataclasses import dataclass

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_LENGTH = 32
NONCE_LENGTH = 12
KEY_LENGTH = 32
PBKDF2_ITERATIONS = 100_000


@dataclass
class EncryptedData:
    salt: bytes
    nonce: bytes
    ciphertext: bytes


def derive_key(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = os.urandom(SALT_LENGTH)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend(),
    )
    key = kdf.derive(password.encode("utf-8"))
    return key, salt


def encrypt_data(password: str, plaintext: bytes) -> bytes:
    key, salt = derive_key(password)
    nonce = os.urandom(NONCE_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    encrypted = EncryptedData(salt=salt, nonce=nonce, ciphertext=ciphertext)
    return b"".join(
        [
            b"ENV01",
            encrypted.salt,
            encrypted.nonce,
            encrypted.ciphertext,
        ]
    )


def decrypt_data(password: str, encrypted_bytes: bytes) -> bytes | None:
    if len(encrypted_bytes) < 4 + SALT_LENGTH + NONCE_LENGTH:
        return None

    prefix = encrypted_bytes[:5]
    if prefix != b"ENV01":
        return None

    offset = 5
    salt = encrypted_bytes[offset : offset + SALT_LENGTH]
    offset += SALT_LENGTH
    nonce = encrypted_bytes[offset : offset + NONCE_LENGTH]
    offset += NONCE_LENGTH
    ciphertext = encrypted_bytes[offset:]

    key, _ = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        return None


def verify_password(password: str, encrypted_bytes: bytes) -> bool:
    result = decrypt_data(password, encrypted_bytes)
    return result is not None
