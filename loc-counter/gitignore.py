"""Parse .gitignore patterns and check if paths should be ignored."""

from fnmatch import fnmatch
from pathlib import Path


DEFAULT_EXCLUDES: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".tox",
}


def parse_gitignore(root: Path) -> list[str]:
    """Read .gitignore from root directory and return list of patterns."""
    gitignore_path = root / ".gitignore"
    if not gitignore_path.is_file():
        return []

    patterns: list[str] = []
    try:
        text = gitignore_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line.rstrip("/"))
    return patterns


def is_ignored(path: Path, root: Path, patterns: list[str]) -> bool:
    """Check if path matches any gitignore pattern using fnmatch."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False

    rel_str = str(rel)
    name = path.name

    for pattern in patterns:
        pattern_clean = pattern.rstrip("/")

        if "/" in pattern_clean:
            if fnmatch(rel_str, pattern_clean):
                return True
            if fnmatch(rel_str, pattern_clean + "/**"):
                return True
        else:
            if fnmatch(name, pattern_clean):
                return True

        for parent in rel.parents:
            if parent != Path(".") and fnmatch(parent.name, pattern_clean):
                return True

    return False
