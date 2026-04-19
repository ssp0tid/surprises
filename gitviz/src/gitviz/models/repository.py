"""Repository represents a git repository with all its data."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .commit import Commit
from .branch import Branch
from .ref import Tag, HEAD


@dataclass
class Repository:
    """Represents a git repository with all its data."""

    path: Path
    worktree: Path | None = None
    commits: dict[bytes, Commit] = field(default_factory=dict)
    branches: list[Branch] = field(default_factory=list)
    tags: list[Tag] = field(default_factory=list)
    head: HEAD = field(default_factory=HEAD)
    is_shallow: bool = False
    is_bare: bool = False

    def get_commit(self, oid: bytes) -> Commit | None:
        """Get commit by OID."""
        return self.commits.get(oid)

    def get_branch_for_commit(self, oid: bytes) -> Branch | None:
        """Find branch pointing to this commit."""
        for branch in self.branches:
            if branch.oid == oid:
                return branch
        return None

    def get_children(self, oid: bytes) -> list[bytes]:
        """Get commits that have this commit as parent."""
        return [commit_oid for commit_oid, commit in self.commits.items() if oid in commit.parents]

    def get_branches_for_commit(self, oid: bytes) -> list[Branch]:
        """Get all branches pointing to this commit."""
        return [b for b in self.branches if b.oid == oid]

    def get_tags_for_commit(self, oid: bytes) -> list[Tag]:
        """Get all tags pointing to this commit."""
        return [t for t in self.tags if t.oid == oid]

    def iter_commits(self, limit: int | None = None, reverse: bool = False) -> Iterator[Commit]:
        """Iterate over commits."""
        sorted_commits = sorted(
            self.commits.values(), key=lambda c: c.commit_time, reverse=not reverse
        )
        count = 0
        for commit in sorted_commits:
            if limit and count >= limit:
                break
            yield commit
            count += 1

    @property
    def current_branch(self) -> Branch | None:
        """Get the current checked-out branch."""
        for branch in self.branches:
            if branch.is_current:
                return branch
        return None

    @property
    def branch_names(self) -> list[str]:
        """Get list of all branch names."""
        return [b.full_name for b in self.branches if not b.is_remote]

    @property
    def remote_branch_names(self) -> list[str]:
        """Get list of remote branch names."""
        return [b.full_name for b in self.branches if b.is_remote]

    @property
    def tag_names(self) -> list[str]:
        """Get list of all tag names."""
        return [t.name for t in self.tags]
