"""Core domain models for git conflict representation."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ConflictSide(Enum):
    """Represents which branch a conflict came from."""

    OURS = auto()  # Current branch (HEAD)
    THEIRS = auto()  # Incoming merge
    BASE = auto()  # Common ancestor (for diff3)
    MERGED = auto()  # Resolved version


class ResolutionChoice(Enum):
    """User selection for conflict resolution."""

    OURS = auto()
    THEIRS = auto()
    MANUAL = auto()
    SAVE_FOR_LATER = auto()
    AUTO = auto()  # Auto-resolved (identical content)


@dataclass(frozen=True)
class ConflictHunk:
    """Single conflict region in a file.

    Attributes:
        start_line: 1-based line number where conflict starts
        end_line: 1-based line number where conflict ends
        ours_content: Lines from current branch
        theirs_content: Lines from incoming branch
        base_content: Common ancestor (if diff3 enabled)
        resolution: User's chosen resolution
        resolved_content: Resolved content if manually edited
    """

    start_line: int
    end_line: int
    ours_content: tuple[str, ...]
    theirs_content: tuple[str, ...]
    base_content: tuple[str, ...] = field(default_factory=tuple)
    resolution: Optional[ResolutionChoice] = None
    resolved_content: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        """Check if this conflict hunk has been resolved."""
        return self.resolution is not None

    @property
    def hunk_label(self) -> str:
        """Return a label describing this hunk's location."""
        return f"Lines {self.start_line}-{self.end_line}"

    @property
    def branch_label_ours(self) -> str:
        """Return the branch label for ours side."""
        return "HEAD"

    @property
    def branch_label_theirs(self) -> str:
        """Return the branch label for theirs side."""
        return "incoming"


@dataclass
class ConflictFile:
    """A file containing one or more conflicts.

    Attributes:
        path: Relative path to the file
        content: Full file content
        conflicts: List of conflict hunks
        is_binary: Whether file is binary
    """

    path: str
    content: str
    conflicts: list[ConflictHunk] = field(default_factory=list)
    is_binary: bool = False
    _original_content: str = field(default="", repr=False)

    def __post_init__(self):
        if not self._original_content:
            object.__setattr__(self, "_original_content", self.content)

    @property
    def original_content(self) -> str:
        """Original content before any resolutions."""
        return self._original_content

    @property
    def unresolved_count(self) -> int:
        """Number of unresolved conflicts."""
        return sum(1 for c in self.conflicts if not c.is_resolved)

    @property
    def resolved_count(self) -> int:
        """Number of resolved conflicts."""
        return sum(1 for c in self.conflicts if c.is_resolved)

    @property
    def total_count(self) -> int:
        """Total number of conflicts."""
        return len(self.conflicts)

    @property
    def is_fully_resolved(self) -> bool:
        """Check if all conflicts are resolved."""
        return self.unresolved_count == 0

    def get_conflict_at(self, index: int) -> Optional[ConflictHunk]:
        """Get conflict at specific index."""
        if 0 <= index < len(self.conflicts):
            return self.conflicts[index]
        return None

    def update_conflict(
        self, index: int, resolution: ResolutionChoice, resolved_content: Optional[str] = None
    ) -> None:
        """Update a conflict's resolution."""
        if 0 <= index < len(self.conflicts):
            hunk = self.conflicts[index]
            hunk.resolution = resolution
            if resolved_content is not None:
                hunk.resolved_content = resolved_content
            elif resolution == ResolutionChoice.OURS:
                hunk.resolved_content = "".join(hunk.ours_content)
            elif resolution == ResolutionChoice.THEIRS:
                hunk.resolved_content = "".join(hunk.theirs_content)

    def rebuild_content(self) -> str:
        """Rebuild file content with resolved conflicts."""
        if not self.conflicts:
            return self.content

        lines = self.content.splitlines(keepends=True)
        result_lines: list[str] = []
        conflict_idx = 0

        for i, line in enumerate(lines):
            # Check if this line is part of any conflict
            matched_conflict = None
            for idx, hunk in enumerate(self.conflicts):
                if hunk.is_resolved and hunk.start_line - 1 <= i <= hunk.end_line - 1:
                    matched_conflict = idx
                    break

            if matched_conflict is not None:
                # Skip original conflict lines
                if i == self.conflicts[matched_conflict].start_line - 1:
                    # Insert resolved content
                    resolved = self.conflicts[matched_conflict].resolved_content
                    if resolved:
                        result_lines.append(resolved)
                    conflict_idx += 1
            elif (
                line.startswith("<<<<<<<")
                or line.startswith("=======")
                or line.startswith(">>>>>>>")
            ):
                # Skip conflict markers - they'll be replaced by rebuilt content
                pass
            else:
                result_lines.append(line)

        # Handle case where no conflicts were resolved - just remove markers
        result_lines = []
        in_conflict = False
        for line in lines:
            if line.startswith("<<<<<<<"):
                in_conflict = True
            elif line.startswith(">>>>>>>"):
                in_conflict = False
            elif line.startswith("=======") and in_conflict:
                continue
            elif not in_conflict:
                result_lines.append(line)

        return "".join(result_lines)
