"""Branch represents a git branch reference."""

from dataclasses import dataclass


@dataclass
class Branch:
    """Represents a git branch reference."""

    name: str
    oid: bytes
    is_head: bool = False
    is_remote: bool = False
    is_current: bool = False

    @property
    def full_name(self) -> str:
        """Get the full branch name."""
        if self.is_remote:
            return f"origin/{self.name}"
        return self.name

    @property
    def display_name(self) -> str:
        """Get display name (for HEAD detached state)."""
        return self.name

    def matches(self, query: str) -> bool:
        """Check if branch matches query."""
        q = query.lower()
        return q in self.name.lower() or q in self.full_name.lower()
