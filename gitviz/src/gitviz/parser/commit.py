"""Commit object parser."""

from ..models.actor import Actor
from ..models.commit import Commit
from .base import BaseParser


class CommitParser(BaseParser):
    """Parses commit object content into Commit dataclass."""

    def parse(self, data: bytes, oid: bytes) -> Commit:
        """
        Parse raw commit content.

        Content is text with headers, blank line, then message.
        Headers are space-separated: "tree", "parent", "author", "committer"
        """
        content = self._safe_decode(data)
        lines = content.split("\n")

        commit_oid = oid
        tree_oid = b""
        parents: list[bytes] = []
        author: Actor | None = None
        committer: Actor | None = None
        author_time = 0
        commit_time = 0
        encoding = "utf-8"
        message_lines: list[str] = []
        in_message = False

        for line in lines:
            if in_message:
                message_lines.append(line)
                continue

            if not line:
                in_message = True
                continue

            if line.startswith("tree "):
                tree_oid = bytes.fromhex(line[5:41])
            elif line.startswith("parent "):
                parents.append(bytes.fromhex(line[7:47]))
            elif line.startswith("author "):
                author, author_time = self._parse_actor_line(line[7:])
            elif line.startswith("committer "):
                committer, commit_time = self._parse_actor_line(line[10:])
            elif line.startswith("encoding "):
                encoding = line[9:].strip()

        message = "\n".join(message_lines).rstrip("\n")

        return Commit(
            oid=commit_oid,
            tree_oid=tree_oid,
            parents=parents,
            author=author,
            committer=committer,
            author_time=author_time,
            commit_time=commit_time,
            message=message,
            encoding=encoding,
        )

    def _parse_actor_line(self, line: str) -> tuple[Actor, int]:
        """Parse 'Name <email> timestamp timezone' into Actor."""
        import re

        pattern = r"^(.+?) <(.+?)> (\d+) ([+-]\d+)"
        match = re.match(pattern, line)

        if not match:
            name = line.split("<")[0].strip()
            email = ""
            timestamp = 0
            if match := re.search(r" (\d+) ", line):
                timestamp = int(match.group(1))
            return Actor(name=name, email=email), timestamp

        name = match.group(1)
        email = match.group(2)
        timestamp = int(match.group(3))

        return Actor(name=name, email=email), timestamp
