"""Repository loader and discovery."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterator

from ..models.repository import Repository
from ..models.commit import Commit
from ..models.ref import HEAD
from ..models.errors import NotAGitRepository, CorruptRepository
from .base import BaseParser
from .loose import LooseObjectReader, ObjectType
from .pack import PackFileParser
from .commit import CommitParser
from .ref_parser import RefParser


class RepositoryLoader:
    """Discovers and loads git repositories."""

    def __init__(self):
        self.commit_parser = CommitParser(Path("."))
        self.tree_parser = None

    @staticmethod
    def discover(path: Path | None = None) -> Path | None:
        """
        Find .git directory starting from given path.

        Walks up directory tree if not found.
        Returns path to .git or None.
        """
        if path is None:
            path = Path.cwd()
        elif not path.is_dir():
            return None

        current = path.resolve()

        while True:
            git_dir = current / ".git"
            if git_dir.is_dir():
                return git_dir

            parent = current.parent
            if parent == current:
                break
            current = parent

        return None

    async def load(
        self,
        path: Path,
        *,
        max_commits: int | None = None,
        branch_filter: list[str] | None = None,
        shallow: bool = False,
    ) -> Repository:
        """
        Load complete repository state.

        Args:
            path: Path to .git directory or repository root
            max_commits: Limit commits to load (for large repos)
            branch_filter: Only load specified branches
            shallow: Only load reachable from HEAD

        Returns:
            Populated Repository object

        Raises:
            NotAGitRepository: Path is not a git repo
            CorruptRepository: Git data is corrupted
        """
        git_dir = self._resolve_git_dir(path)

        if git_dir is None or not git_dir.exists():
            raise NotAGitRepository(f"Not a git repository: {path}")

        is_shallow = (git_dir / "shallow").exists()
        is_bare = (git_dir / "HEAD").exists() and not git_dir.is_dir()

        repo = Repository(
            path=git_dir,
            is_shallow=is_shallow,
            is_bare=is_bare,
        )

        if is_bare:
            repo.worktree = git_dir
        else:
            repo.worktree = git_dir.parent

        ref_parser = RefParser(git_dir)
        repo.head = ref_parser.parse_head()
        repo.branches = ref_parser.parse_branches()
        repo.tags = ref_parser.parse_tags()

        loose_reader = LooseObjectReader(git_dir / "objects")

        pack_parsers: list[PackFileParser] = []
        pack_dir = git_dir / "objects" / "pack"
        if pack_dir.exists():
            for pack_file in pack_dir.glob("*.pack"):
                idx_file = pack_file.with_suffix(".idx")
                if idx_file.exists():
                    pack_parsers.append(PackFileParser(pack_file, idx_file))

        commits: dict[bytes, Commit] = {}
        pending_oids: set[bytes] = set()

        if repo.head.commit_oid:
            pending_oids.add(repo.head.commit_oid)

        for branch in repo.branches:
            pending_oids.add(branch.oid)

        for tag in repo.tags:
            pending_oids.add(tag.oid)

        if shallow:
            pending_oids = self._limit_to_shallow(git_dir, pending_oids)

        while pending_oids and len(commits) < (max_commits or float("inf")):
            oid = pending_oids.pop()

            if oid in commits:
                continue

            try:
                commit = await self._load_commit(oid, loose_reader, pack_parsers)
                commits[oid] = commit

                for parent_oid in commit.parents:
                    if parent_oid not in commits:
                        pending_oids.add(parent_oid)

            except Exception as e:
                import logging

                logging.warning(f"Failed to load commit {oid.hex()}: {e}")

        repo.commits = commits
        return repo

    def _resolve_git_dir(self, path: Path) -> Path | None:
        """Resolve path to .git directory."""
        if path.is_file() and path.name == ".git":
            return path

        if path.is_dir() and (path / ".git").is_dir():
            return path / ".git"

        if path.is_dir() and path.name == ".git" and path.is_dir():
            return path

        discovered = self.discover(path)
        return discovered

    def _limit_to_shallow(self, git_dir: Path, oids: set[bytes]) -> set[bytes]:
        """Limit OIDs to shallow clone boundary."""
        shallow_file = git_dir / "shallow"
        if not shallow_file.exists():
            return oids

        shallow_oids = set()
        for line in shallow_file.read_text().splitlines():
            line = line.strip()
            if len(line) == 40:
                shallow_oids.add(bytes.fromhex(line))

        return oids & shallow_oids

    async def _load_commit(
        self,
        oid: bytes,
        loose_reader: LooseObjectReader,
        pack_parsers: list[PackFileParser],
    ) -> Commit:
        """Load a single commit object."""
        obj_type, content = self._find_object(oid, loose_reader, pack_parsers)

        if obj_type != ObjectType.COMMIT:
            raise CorruptRepository(f"Object is not a commit: {oid.hex()}")

        return self.commit_parser.parse(content, oid)

    def _find_object(
        self,
        oid: bytes,
        loose_reader: LooseObjectReader,
        pack_parsers: list[PackFileParser],
    ) -> tuple[int, bytes]:
        """Find object in loose objects or pack files."""
        if loose_reader.has_object(oid):
            return loose_reader.get_object(oid)

        for pack_parser in pack_parsers:
            if pack_parser.index.has_object(oid):
                return pack_parser.get_object(oid)

        raise CorruptRepository(f"Object not found: {oid.hex()}")

    def iter_commits_from_refs(
        self,
        git_dir: Path,
        refs: list[str] | None = None,
    ) -> Iterator[tuple[bytes, Commit]]:
        """Iterate commits from specified refs."""
        loose_reader = LooseObjectReader(git_dir / "objects")
        pack_dir = git_dir / "objects" / "pack"
        pack_parsers: list[PackFileParser] = []

        if pack_dir.exists():
            for pack_file in pack_dir.glob("*.pack"):
                idx_file = pack_file.with_suffix(".idx")
                if idx_file.exists():
                    pack_parsers.append(PackFileParser(pack_file, idx_file))

        visited: set[bytes] = set()
        pending: list[bytes] = []

        if refs is None:
            refs = ["HEAD"]

        for ref_name in refs:
            oid = self._resolve_ref(git_dir, ref_name)
            if oid and oid not in visited:
                pending.append(oid)

        while pending:
            oid = pending.pop(0)
            if oid in visited:
                continue

            try:
                obj_type, content = self._find_object(oid, loose_reader, pack_parsers)
                if obj_type == ObjectType.COMMIT:
                    commit = self.commit_parser.parse(content, oid)
                    yield oid, commit
                    visited.add(oid)
                    for parent_oid in commit.parents:
                        if parent_oid not in visited:
                            pending.append(parent_oid)
                else:
                    visited.add(oid)
            except Exception as e:
                import logging

                logging.warning(f"Failed to load commit during iteration: {e}")
                visited.add(oid)

    def _resolve_ref(self, git_dir: Path, ref_name: str) -> bytes | None:
        """Resolve ref name to OID."""
        head_file = git_dir / "HEAD"

        if ref_name == "HEAD":
            content = head_file.read_text().strip()
            if content.startswith("ref: "):
                ref_path = content[5:]
                ref_file = git_dir / ref_path
                if ref_file.exists():
                    return bytes.fromhex(ref_file.read_text().strip())
            else:
                return bytes.fromhex(content)

        for ref_path in [
            git_dir / "refs" / "heads" / ref_name,
            git_dir / "refs" / "remotes" / ref_name,
            git_dir / "refs" / "tags" / ref_name,
        ]:
            if ref_path.exists():
                return bytes.fromhex(ref_path.read_text().strip())

        return None
