"""Commit represents a git commit object."""

from dataclasses import dataclass, field
from datetime import datetime
from .actor import Actor


@dataclass
class Commit:
    """Represents a git commit object."""

    oid: bytes
    tree_oid: bytes = b"0" * 20
    parents: list[bytes] = field(default_factory=list)
    author: Actor | None = None
    committer: Actor | None = None
    author_time: int = 0
    commit_time: int = 0
    message: str = ""
    encoding: str = "utf-8"

    @property
    def short_oid(self) -> str:
        """First 7 characters of SHA-1."""
        return self.oid.hex()[:7]

    @property
    def full_oid(self) -> str:
        """Full 40-character SHA-1 hash."""
        return self.oid.hex()

    @property
    def is_merge(self) -> bool:
        """True if this commit has multiple parents."""
        return len(self.parents) > 1

    @property
    def short_message(self) -> str:
        """First line of commit message, truncated."""
        first_line = self.message.split("\n")[0]
        return first_line[:72] + "..." if len(first_line) > 72 else first_line

    @property
    def author_date(self) -> datetime:
        """Author date as datetime."""
        return datetime.fromtimestamp(self.author_time)

    @property
    def committer_date(self) -> datetime:
        """Committer date as datetime."""
        return datetime.fromtimestamp(self.commit_time)

    @property
    def branches(self) -> list[str]:
        """Branches that point to this commit (populated by repository)."""
        return []
