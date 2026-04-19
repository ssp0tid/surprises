"""Reference parser for git refs."""

from pathlib import Path
import re

from ..models.branch import Branch
from ..models.ref import Tag, HEAD
from ..models.errors import NotAGitRepository
from .base import BaseParser


class RefParser(BaseParser):
    """Parses and resolves git references."""

    def __init__(self, git_dir: Path):
        super().__init__(git_dir)
        self.refs_dir = git_dir / "refs"
        self.head_file = git_dir / "HEAD"
        self.packed_refs_file = git_dir / "packed-refs"

    def parse_head(self) -> HEAD:
        """Parse HEAD to determine current state."""
        if not self.head_file.exists():
            return HEAD()

        content = self.head_file.read_text().strip()

        if content.startswith("ref: "):
            ref_path = content[5:]
            branch_name = self._resolve_branch_name(ref_path)
            commit_oid = self._read_ref(ref_path)
            return HEAD(
                is_detached=False,
                commit_oid=commit_oid,
                branch_name=branch_name,
            )
        else:
            commit_oid = bytes.fromhex(content)
            return HEAD(
                is_detached=True,
                commit_oid=commit_oid,
                branch_name=None,
            )

    def _resolve_branch_name(self, ref_path: str) -> str | None:
        """Resolve ref path to branch name."""
        if ref_path.startswith("refs/heads/"):
            return ref_path[11:]
        if ref_path.startswith("refs/"):
            return ref_path
        return ref_path

    def _read_ref(self, ref_path: str) -> bytes | None:
        """Read a reference file."""
        ref_file = self.git_dir / ref_path
        if ref_file.exists():
            content = ref_file.read_text().strip()
            if len(content) == 40:
                return bytes.fromhex(content)

        for packed_ref in self._read_packed_refs():
            if packed_ref.name == ref_path or packed_ref.name.endswith(ref_path):
                return packed_ref.oid

        return None

    def parse_branches(self) -> list[Branch]:
        """Parse all local and remote branches."""
        branches: list[Branch] = []
        head = self.parse_head()

        branches.extend(self._parse_refs_dir(self.refs_dir / "heads", False))
        branches.extend(self._parse_refs_dir(self.refs_dir / "remotes", True))

        branches.extend(self._read_packed_refs_branches())

        for branch in branches:
            if head.branch_name and branch.name == head.branch_name:
                branch.is_current = True
            if head.commit_oid and branch.oid == head.commit_oid:
                branch.is_head = True

        return branches

    def _parse_refs_dir(self, refs_path: Path, is_remote: bool) -> list[Branch]:
        """Parse refs from directory."""
        branches: list[Branch] = []

        if not refs_path.exists():
            return branches

        for ref_file in refs_path.rglob("*"):
            if ref_file.is_file():
                content = ref_file.read_text().strip()
                if len(content) == 40:
                    try:
                        oid = bytes.fromhex(content)
                        rel_path = ref_file.relative_to(refs_path)
                        name = str(rel_path).replace("\\", "/")
                        branches.append(
                            Branch(
                                name=name,
                                oid=oid,
                                is_remote=is_remote,
                            )
                        )
                    except ValueError:
                        pass

        return branches

    def _read_packed_refs_branches(self) -> list[Branch]:
        """Read packed refs."""
        branches: list[Branch] = []

        if not self.packed_refs_file.exists():
            return branches

        content = self.packed_refs_file.read_text()
        for line in content.split("\n"):
            if not line or line.startswith("#"):
                continue

            if line.startswith("^"):
                continue

            parts = line.split(" ")
            if len(parts) >= 2:
                ref_path = parts[0]
                oid_hex = parts[1]

                if not ref_path.startswith("refs/"):
                    continue

                if ref_path.startswith("refs/heads/"):
                    name = ref_path[11:]
                    branches.append(
                        Branch(
                            name=name,
                            oid=bytes.fromhex(oid_hex),
                            is_remote=False,
                        )
                    )
                elif ref_path.startswith("refs/remotes/"):
                    name = ref_path[13:]
                    branches.append(
                        Branch(
                            name=name,
                            oid=bytes.fromhex(oid_hex),
                            is_remote=True,
                        )
                    )

        return branches

    def parse_tags(self) -> list[Tag]:
        """Parse all tags."""
        tags: list[Tag] = []
        tags_dir = self.git_dir / "refs" / "tags"

        if tags_dir.exists():
            for tag_file in tags_dir.rglob("*"):
                if tag_file.is_file():
                    content = tag_file.read_text().strip()
                    if len(content) == 40:
                        try:
                            oid = bytes.fromhex(content)
                            name = tag_file.name
                            tags.append(Tag(name=name, oid=oid))
                        except ValueError:
                            pass

        tags.extend(self._read_packed_refs_tags())

        return tags

    def _read_packed_refs_tags(self) -> list[Tag]:
        """Read packed tags."""
        tags: list[Tag] = []

        if not self.packed_refs_file.exists():
            return tags

        content = self.packed_refs_file.read_text()
        for line in content.split("\n"):
            if not line or line.startswith("#"):
                continue

            if line.startswith("^"):
                continue

            parts = line.split(" ")
            if len(parts) >= 2:
                ref_path = parts[0]
                oid_hex = parts[1]

                if ref_path.startswith("refs/tags/"):
                    name = ref_path[10:]
                    tags.append(
                        Tag(
                            name=name,
                            oid=bytes.fromhex(oid_hex),
                        )
                    )

        return tags
