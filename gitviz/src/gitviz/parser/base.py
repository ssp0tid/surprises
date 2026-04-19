"""Base parser for git objects."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """Base class for all git object parsers."""

    def __init__(self, git_dir: Path):
        self.git_dir = git_dir
        self.objects_dir = git_dir / "objects"

    def _safe_decode(self, data: bytes, encoding: str = "utf-8") -> str:
        """Decode bytes, fallback to latin-1."""
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="replace")

    @staticmethod
    def _hex_to_bytes(hex_str: str) -> bytes:
        """Convert hex string to bytes."""
        return bytes.fromhex(hex_str)

    @staticmethod
    def _bytes_to_hex(data: bytes) -> str:
        """Convert bytes to hex string."""
        return data.hex()
