"""Core line-counting logic with block comment state machine."""

from dataclasses import dataclass
from pathlib import Path

from languages import LangDef, get_language
from gitignore import DEFAULT_EXCLUDES, parse_gitignore, is_ignored


@dataclass
class FileStats:
    path: str
    language: str
    code: int
    comments: int
    blanks: int
    total: int


@dataclass
class LangSummary:
    language: str
    files: int
    code: int
    comments: int
    blanks: int
    total: int


def _is_binary(filepath: Path) -> bool:
    try:
        chunk = filepath.read_bytes()[:8192]
        return b"\x00" in chunk
    except OSError:
        return True


def count_file(filepath: Path, lang_def: LangDef) -> FileStats:
    """Count code, comment, and blank lines in a single file using a state machine."""
    code = 0
    comments = 0
    blanks = 0
    in_block = False

    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return FileStats(str(filepath), lang_def.name, 0, 0, 0, 0)

    for line in lines:
        stripped = line.strip()

        if not stripped:
            blanks += 1
            continue

        if in_block:
            comments += 1
            if lang_def.block_comment_end and lang_def.block_comment_end in stripped:
                in_block = False
            continue

        if lang_def.block_comment_start and stripped.startswith(lang_def.block_comment_start):
            comments += 1
            if lang_def.block_comment_end and lang_def.block_comment_end in stripped[len(lang_def.block_comment_start):]:
                pass
            else:
                in_block = True
            continue

        if lang_def.line_comment and stripped.startswith(lang_def.line_comment):
            comments += 1
            continue

        code += 1

    total = code + comments + blanks
    return FileStats(str(filepath), lang_def.name, code, comments, blanks, total)


def count_directory(root: Path, ignore_patterns: list[str], exclude_dirs: set[str]) -> list[FileStats]:
    """Walk directory tree, count all recognized source files."""
    results: list[FileStats] = []
    all_excludes = DEFAULT_EXCLUDES | exclude_dirs

    try:
        entries = sorted(root.rglob("*"))
    except PermissionError:
        return results

    for item in entries:
        try:
            if not item.is_file():
                continue
        except (PermissionError, OSError):
            continue

        skip = False
        for part in item.relative_to(root).parts[:-1]:
            if part in all_excludes:
                skip = True
                break
        if skip:
            continue

        if ignore_patterns and is_ignored(item, root, ignore_patterns):
            continue

        lang_def = get_language(item.name, item.suffix)
        if lang_def is None:
            continue

        if _is_binary(item):
            continue

        stats = count_file(item, lang_def)
        if stats.total > 0:
            results.append(stats)

    return results


def summarize_by_language(file_stats: list[FileStats]) -> list[LangSummary]:
    """Aggregate file stats into per-language summaries."""
    lang_map: dict[str, LangSummary] = {}

    for fs in file_stats:
        if fs.language not in lang_map:
            lang_map[fs.language] = LangSummary(
                language=fs.language, files=0, code=0, comments=0, blanks=0, total=0
            )
        summary = lang_map[fs.language]
        summary.files += 1
        summary.code += fs.code
        summary.comments += fs.comments
        summary.blanks += fs.blanks
        summary.total += fs.total

    return list(lang_map.values())
