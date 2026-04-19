"""Tree object parser."""

from dataclasses import dataclass
from enum import IntEnum
from .base import BaseParser


class TreeEntryType(IntEnum):
    """Tree entry types."""

    BLOB = 0o100644
    EXECUTABLE = 0o100755
    LINK = 0o120000
    COMMIT = 0o160000


@dataclass
class TreeEntry:
    """Represents an entry in a tree object."""

    mode: str
    name: str
    oid: bytes
    entry_type: TreeEntryType

    @property
    def is_blob(self) -> bool:
        return self.entry_type == TreeEntryType.BLOB

    @property
    def is_directory(self) -> bool:
        return self.entry_type == TreeEntryType.COMMIT


class TreeParser(BaseParser):
    """Parses tree object content."""

    def parse(self, data: bytes) -> list[TreeEntry]:
        """Parse tree data into list of entries."""
        entries: list[TreeEntry] = []
        offset = 0

        while offset < len(data):
            space_idx = data.index(b" ", offset)
            mode_bytes = data[offset:space_idx]
            mode_str = mode_bytes.decode("ascii")
            mode_int = int(mode_str, 8)

            null_idx = data.index(b"\x00", space_idx)
            name_bytes = data[space_idx + 1 : null_idx]
            name = name_bytes.decode("utf-8", errors="replace")

            oid = data[null_idx + 1 : null_idx + 21]

            entries.append(
                TreeEntry(
                    mode=mode_str,
                    name=name,
                    oid=oid,
                    entry_type=TreeEntryType(mode_int),
                )
            )

            offset = null_idx + 21

        return entries

    def format_entry(self, entry: TreeEntry) -> str:
        """Format tree entry as string."""
        type_char = self._entry_type_char(entry.entry_type)
        return f"{entry.mode} {type_char} {entry.oid.hex()[:8]} {entry.name}"

    def _entry_type_char(self, entry_type: TreeEntryType) -> str:
        """Get character for entry type."""
        return {
            TreeEntryType.BLOB: "blob",
            TreeEntryType.EXECUTABLE: "blob",
            TreeEntryType.LINK: "blob",
            TreeEntryType.COMMIT: "commit",
        }.get(entry_type, "blob")
