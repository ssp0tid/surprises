"""Diff utilities for generating commit diffs."""

from typing import Iterator


class DiffHunk:
    """Represents a diff hunk."""

    def __init__(
        self,
        old_start: int,
        old_count: int,
        new_start: int,
        new_count: int,
        lines: list[str],
    ):
        self.old_start = old_start
        self.old_count = old_count
        self.new_start = new_start
        self.new_count = new_count
        self.lines = lines


class DiffFile:
    """Represents a diff for a single file."""

    def __init__(
        self,
        old_path: str,
        new_path: str,
        hunks: list[DiffHunk],
        is_binary: bool = False,
    ):
        self.old_path = old_path
        self.new_path = new_path
        self.hunks = hunks
        self.is_binary = is_binary


def generate_diff(old_lines: list[str], new_lines: list[str]) -> list[str]:
    """Generate unified diff between two lists of lines."""
    from difflib import unified_diff

    diff = unified_diff(
        old_lines,
        new_lines,
        lineterm="",
    )

    return list(diff)


def format_diff_header(old_path: str, new_path: str) -> str:
    """Format diff file header."""
    return f"--- {old_path}\n+++ {new_path}"


def format_diff_hunk(hunk: DiffHunk) -> str:
    """Format a diff hunk."""
    lines = [f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@"]
    lines.extend(hunk.lines)
    return "\n".join(lines)


def parse_diff_line(line: str) -> tuple[str, str]:
    """Parse a diff line and return (prefix, content)."""
    if not line:
        return (" ", "")

    if line.startswith("@@"):
        return ("hunk", line)
    if line.startswith("---"):
        return ("file", line)
    if line.startswith("+++"):
        return ("file", line)
    if line.startswith("diff "):
        return ("header", line)

    prefix = line[0] if line else " "
    content = line[1:] if len(line) > 1 else ""

    return (prefix, content)


def is_binary_file(content: bytes, sample_size: int = 8192) -> bool:
    """Check if file content is binary."""
    sample = content[:sample_size]

    null_count = sample.count(b"\x00")
    if null_count > 0:
        return True

    text_char_count = sum(1 for b in sample if 32 <= b < 127 or b in (9, 10, 13))
    text_ratio = text_char_count / len(sample) if sample else 0

    return text_ratio < 0.75


def diff_to_str(old_content: str, new_content: str) -> str:
    """Generate diff as string."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines = generate_diff(old_lines, new_lines)

    if not diff_lines:
        return "No changes"

    return "\n".join(diff_lines)
