"""Cryptography module for encrypted storage.

Security: AES-256-GCM with PBKDF2-HMAC-SHA256 key derivation.
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


ITERATIONS = 480000
SALT_LENGTH = 32
KEY_LENGTH = 32
NONCE_LENGTH = 12


class CryptoManager:
    def __init__(self, password: str, salt: bytes = None):
        self.salt = salt if salt is not None else self.generate_salt()
        self.key = self.derive_key(password, self.salt)

    @classmethod
    def generate_salt(cls) -> bytes:
        return os.urandom(SALT_LENGTH)

    def derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_LENGTH,
            salt=salt,
            iterations=ITERATIONS,
            backend=default_backend(),
        )
        return kdf.derive(password.encode("utf-8"))

    def encrypt(self, data: bytes) -> tuple[bytes, bytes]:
        nonce = os.urandom(NONCE_LENGTH)
        aesgcm = AESGCM(self.key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return ciphertext, nonce

    def decrypt(self, ciphertext: bytes, nonce: bytes) -> bytes:
        aesgcm = AESGCM(self.key)
        return aesgcm.decrypt(nonce, ciphertext, None)
