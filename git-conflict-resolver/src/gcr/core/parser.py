"""Conflict marker parser for git merge conflicts."""

import re
from dataclasses import dataclass, field
from typing import Iterator, Optional

from .conflict import ConflictFile, ConflictHunk


@dataclass
class ParseResult:
    """Result of parsing aconflicted file."""

    file: ConflictFile
    parse_warnings: list[str] = field(default_factory=list)
    encoding_errors: list[str] = field(default_factory=list)


class ConflictParser:
    """Parses git conflict markers from file content."""

    CONFLICT_START = re.compile(r"^<<<<<<<[ :](.*)$", re.MULTILINE)
    CONFLICT_SEPARATOR = re.compile(r"^=======[ :]*$", re.MULTILINE)
    CONFLICT_END = re.compile(r"^>>>>>>>[ :](.*)$", re.MULTILINE)
    DIFF3_BASE_START = re.compile(r"^\|\|\|\|\|\| (.*)$", re.MULTILINE)

    def __init__(self, enable_diff3: bool = True):
        self.enable_diff3 = enable_diff3

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse conflict markers from file content.

        Args:
            content: File content as string
            file_path: Path for error messages

        Returns:
            ParseResult with parsed conflicts
        """
        warnings = []
        encoding_errors = []

        if not content:
            return ParseResult(
                file=ConflictFile(path=file_path, content=""),
                parse_warnings=warnings,
                encoding_errors=encoding_errors,
            )

        is_binary = self._detect_binary(content)
        if is_binary:
            return ParseResult(
                file=ConflictFile(path=file_path, content=content, is_binary=True),
                parse_warnings=["File appears to be binary, cannot parse conflicts"],
                encoding_errors=encoding_errors,
            )

        conflicts = list(self._extract_conflicts(content))
        if not conflicts:
            warnings.append("No conflict markers found in file")

        return ParseResult(
            file=ConflictFile(path=file_path, content=content, conflicts=conflicts),
            parse_warnings=warnings,
            encoding_errors=encoding_errors,
        )

    def _detect_binary(self, content: str) -> bool:
        """Detect if content is binary."""
        try:
            content.encode("utf-8")
            return "\x00" in content
        except UnicodeEncodeError:
            return True

    def _extract_conflicts(self, content: str) -> Iterator[ConflictHunk]:
        """Extract individual conflict hunks from content."""
        lines = content.splitlines(keepends=True)
        in_conflict = False
        ours_lines: list[str] = []
        theirs_lines: list[str] = []
        base_lines: list[str] = []
        start_line = 0
        separator_line = 0
        have_base = False

        for i, line in enumerate(lines):
            if self.CONFLICT_START.match(line):
                in_conflict = True
                ours_lines = []
                theirs_lines = []
                base_lines = []
                have_base = False
                start_line = i + 1

            elif in_conflict and self.CONFLICT_SEPARATOR.match(line):
                separator_line = i + 1

            elif in_conflict and self.DIFF3_BASE_START.match(line):
                have_base = True

            elif in_conflict and self.CONFLICT_END.match(line):
                end_line = i + 1
                yield ConflictHunk(
                    start_line=start_line,
                    end_line=end_line,
                    ours_content=tuple(ours_lines),
                    theirs_content=tuple(theirs_lines),
                    base_content=tuple(base_lines) if have_base else tuple(),
                )
                in_conflict = False

            elif in_conflict:
                if separator_line == 0:
                    ours_lines.append(line)
                elif have_base and base_lines:
                    base_lines.append(line)
                else:
                    theirs_lines.append(line)
