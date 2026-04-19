"""Ref represents git references (branches, tags, HEAD)."""

from dataclasses import dataclass, field
from enum import Enum


class RefType(Enum):
    """Type of git reference."""

    LOCAL_BRANCH = "local_branch"
    REMOTE_BRANCH = "remote_branch"
    TAG = "tag"
    HEAD = "head"


@dataclass
class Tag:
    """Represents a git tag reference."""

    name: str
    oid: bytes
    message: str = ""
    tagger: str = ""
    tag_time: int = 0

    @property
    def full_name(self) -> str:
        return f"refs/tags/{self.name}"

    def matches(self, query: str) -> bool:
        q = query.lower()
        return q in self.name.lower()


@dataclass
class Ref:
    """Represents a git reference."""

    name: str
    ref_type: RefType
    oid: bytes
    target_oid: bytes | None = None
    symbolic: bool = False


@dataclass
class HEAD:
    """Represents the current HEAD state."""

    is_detached: bool = False
    commit_oid: bytes | None = None
    branch_name: str | None = None

    @property
    def display_name(self) -> str:
        """Get display name for HEAD."""
        if self.is_detached:
            if self.commit_oid:
                return f"(HEAD detached at {self.commit_oid.hex()[:7]})"
            return "(HEAD detached)"
        return f"(HEAD -> {self.branch_name})"
